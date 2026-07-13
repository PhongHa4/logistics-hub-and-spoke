import asyncio
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from db import get_connection

router = APIRouter()

DEFAULT_DURATION_S = 60  # fallback nếu route nào đó thiếu time_s


def flatten_coords(geojson):
    """Gộp coordinates của LineString hoặc MultiLineString thành 1 list điểm duy nhất"""
    if geojson["type"] == "LineString":
        return geojson["coordinates"]
    elif geojson["type"] == "MultiLineString":
        coords = []
        for line in geojson["coordinates"]:
            coords.extend(line)
        return coords
    return []


def interpolate_position(coords, fraction):
    """Tìm điểm nằm ở vị trí `fraction` (0.0 -> 1.0) dọc theo đường coords"""
    if len(coords) < 2:
        return coords[0] if coords else None

    # Tính khoảng cách dồn tích qua từng điểm
    cum_dist = [0]
    for i in range(1, len(coords)):
        x1, y1 = coords[i - 1]
        x2, y2 = coords[i]
        cum_dist.append(cum_dist[-1] + ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5)

    total = cum_dist[-1]
    if total == 0:
        return coords[0]

    target = fraction * total
    for i in range(1, len(cum_dist)):
        if cum_dist[i] >= target:
            seg_len = cum_dist[i] - cum_dist[i - 1]
            seg_frac = (target - cum_dist[i - 1]) / seg_len if seg_len > 0 else 0
            x1, y1 = coords[i - 1]
            x2, y2 = coords[i]
            return [x1 + (x2 - x1) * seg_frac, y1 + (y2 - y1) * seg_frac]

    return coords[-1]


def load_latest_batch_routes():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT MAX(batch_id) FROM route_results;")
    batch_id = cur.fetchone()[0]
    if batch_id is None:
        cur.close()
        conn.close()
        return []

    cur.execute("""
        SELECT id, stage, hub_zone, vehicle_id, geojson, time_s
        FROM route_results WHERE batch_id = %s;
    """, (batch_id,))

    vehicles = []
    for row_id, stage, hub_zone, vehicle_id, geojson, time_s in cur.fetchall():
        coords = flatten_coords(geojson)
        if len(coords) < 2:
            continue  # route quá ngắn, không có gì để mô phỏng di chuyển
        vehicles.append({
            "key": f"{stage}_{hub_zone}_{vehicle_id if vehicle_id is not None else row_id}",
            "stage": stage,
            "hub_zone": hub_zone,
            "coords": coords,
            "duration_s": float(time_s) if time_s else DEFAULT_DURATION_S,
        })

    cur.close()
    conn.close()
    return vehicles


@router.websocket("/ws/vehicles")
async def vehicles_ws(websocket: WebSocket):
    await websocket.accept()

    vehicles = load_latest_batch_routes()
    if not vehicles:
        await websocket.send_json({"vehicles": [], "message": "Chưa có route nào để mô phỏng"})

    start_time = time.time()

    try:
        while True:
            elapsed = time.time() - start_time
            payload = []
            for v in vehicles:
                fraction = (elapsed % v["duration_s"]) / v["duration_s"]
                pos = interpolate_position(v["coords"], fraction)
                payload.append({
                    "key": v["key"], "stage": v["stage"], "hub_zone": v["hub_zone"],
                    "position": pos,
                })
            await websocket.send_json({"vehicles": payload})
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass