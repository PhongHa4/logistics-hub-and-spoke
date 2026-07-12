import json
from fastapi import APIRouter
from db import get_connection
from pipeline import (
    load_pending_orders, run_first_mile_for_hub, run_last_mile_for_hub,
    run_linehaul_for_pair, get_active_linehaul_pairs,
)
from route_geometry import get_route_geometry
from geo_constants import HUBS


router = APIRouter()


def get_next_batch_id(cur) -> int:
    cur.execute("SELECT COALESCE(MAX(batch_id), 0) + 1 FROM route_results;")
    return cur.fetchone()[0]


def save_route_result(cur, batch_id, stage, hub_zone, vehicle_id, geojson, load_kg, time_s):
    cur.execute("""
        INSERT INTO route_results (batch_id, stage, hub_zone, vehicle_id, geojson, load_kg, time_s)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
    """, (batch_id, stage, hub_zone, vehicle_id, json.dumps(geojson), load_kg, time_s))


@router.post("/calculate-routes")
def calculate_routes():
    orders = load_pending_orders()
    if not orders:
        return {"message": "Không có đơn nào ở trạng thái pending", "batch_id": None}

    conn = get_connection()
    cur = conn.cursor()
    batch_id = get_next_batch_id(cur)

    # --- First-mile ---
    for hub_zone in HUBS:
        stage1 = run_first_mile_for_hub(hub_zone, orders)
        if not stage1 or not stage1["success"]:
            continue
        for r in stage1["routes"]:
            geojson = get_route_geometry(r["route"])
            if geojson:
                save_route_result(cur, batch_id, "first_mile", hub_zone,
                                   r["vehicle_id"], geojson, r["load_kg"], r["time_s"])

    # --- Linehaul ---
    for from_hub, to_hub in get_active_linehaul_pairs(orders):
        stage2 = run_linehaul_for_pair(from_hub, to_hub)
        node_sequence = [HUBS[from_hub]["node_id"], HUBS[to_hub]["node_id"]]
        geojson = get_route_geometry(node_sequence)
        if geojson:
            save_route_result(cur, batch_id, "linehaul", f"{from_hub}__{to_hub}",
                               None, geojson, None, stage2["travel_time_s"])

    # --- Last-mile ---
    for hub_zone in HUBS:
        stage3 = run_last_mile_for_hub(hub_zone, orders)
        if not stage3 or not stage3["success"]:
            continue
        for r in stage3["routes"]:
            geojson = get_route_geometry(r["route"])
            if geojson:
                save_route_result(cur, batch_id, "last_mile", hub_zone,
                                   r["vehicle_id"], geojson, r["load_kg"], r["time_s"])

    # --- Update trạng thái đơn hàng đã xử lý ---
    order_ids = [o["id"] for o in orders]
    cur.execute("""
        UPDATE orders SET status = 'routed', batch_id = %s, updated_at = NOW()
        WHERE id = ANY(%s);
    """, (batch_id, order_ids))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Đã tính toán xong", "batch_id": batch_id, "orders_processed": len(order_ids)}


@router.get("/routes/latest")
def get_latest_routes():
    """Lấy toàn bộ route_results của batch gần nhất, dạng GeoJSON FeatureCollection"""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT MAX(batch_id) FROM route_results;")
    latest_batch = cur.fetchone()[0]
    if latest_batch is None:
        cur.close()
        conn.close()
        return {"type": "FeatureCollection", "features": []}

    cur.execute("""
        SELECT stage, hub_zone, vehicle_id, geojson, load_kg, time_s
        FROM route_results WHERE batch_id = %s;
    """, (latest_batch,))

    features = []
    for stage, hub_zone, vehicle_id, geojson, load_kg, time_s in cur.fetchall():
        features.append({
            "type": "Feature",
            "geometry": geojson,
            "properties": {
                "stage": stage, "hub_zone": hub_zone, "vehicle_id": vehicle_id,
                "load_kg": load_kg, "time_s": time_s,
            },
        })

    cur.close()
    conn.close()
    return {"type": "FeatureCollection", "features": features, "batch_id": latest_batch}