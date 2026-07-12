from vrp_solver import solve_vrp
from time_matrix import compute_time_matrix
from db import get_connection
from geo_constants import HUBS

DEFAULT_CAPACITY = 100
DEFAULT_MAX_VEHICLES = 8


def load_pending_orders():
    """Đọc các đơn 'pending' (đã geocode + tìm node + phân loại hub thành công)"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, pickup_node_id, delivery_node_id, pickup_hub_zone, delivery_hub_zone, demand_kg
        FROM orders WHERE status = 'pending';
    """)
    columns = [desc[0] for desc in cur.description]
    orders = [dict(zip(columns, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return orders


def run_first_mile_for_hub(hub_zone, orders, capacity=DEFAULT_CAPACITY, max_vehicles=DEFAULT_MAX_VEHICLES):
    """Gom tất cả đơn có pickup tại hub_zone này, bất kể giao ở đâu"""
    pickups = [o for o in orders if o["pickup_hub_zone"] == hub_zone]
    if not pickups:
        return None

    hub_node = HUBS[hub_zone]["node_id"]
    node_ids = [hub_node] + [o["pickup_node_id"] for o in pickups]
    demands = [0] + [int(round(o["demand_kg"])) for o in pickups]

    return solve_vrp(
        node_ids=node_ids, demands=demands,
        vehicle_capacity=capacity, max_vehicles=max_vehicles,
        fixed_cost=3000, span_coefficient=1, service_time=180,
    )


def run_last_mile_for_hub(hub_zone, orders, capacity=DEFAULT_CAPACITY, max_vehicles=DEFAULT_MAX_VEHICLES):
    """Phát tất cả đơn có delivery tại hub_zone này, bất kể lấy hàng từ đâu"""
    deliveries = [o for o in orders if o["delivery_hub_zone"] == hub_zone]
    if not deliveries:
        return None

    hub_node = HUBS[hub_zone]["node_id"]
    node_ids = [hub_node] + [o["delivery_node_id"] for o in deliveries]
    demands = [0] + [int(round(o["demand_kg"])) for o in deliveries]

    return solve_vrp(
        node_ids=node_ids, demands=demands,
        vehicle_capacity=capacity, max_vehicles=max_vehicles,
        fixed_cost=3000, span_coefficient=1, service_time=180,
    )


def run_linehaul_for_pair(from_hub, to_hub):
    """Thời gian di chuyển Hub -> Hub (chỉ chạy cho các cặp thực sự có đơn liên tỉnh)"""
    from_node = HUBS[from_hub]["node_id"]
    to_node = HUBS[to_hub]["node_id"]
    matrix = compute_time_matrix([from_node, to_node])
    return {"travel_time_s": matrix[0][1]}


def get_active_linehaul_pairs(orders):
    """Tìm các cặp (pickup_hub, delivery_hub) khác nhau thực sự xuất hiện trong đơn hàng"""
    pairs = set()
    for o in orders:
        if o["pickup_hub_zone"] != o["delivery_hub_zone"]:
            pairs.add((o["pickup_hub_zone"], o["delivery_hub_zone"]))
    return pairs


def run_full_pipeline():
    orders = load_pending_orders()
    if not orders:
        return {"message": "Không có đơn nào ở trạng thái pending"}

    result = {"first_mile": {}, "linehaul": {}, "last_mile": {}}

    for hub_zone in HUBS:
        stage1 = run_first_mile_for_hub(hub_zone, orders)
        if stage1:
            result["first_mile"][hub_zone] = stage1

    for from_hub, to_hub in get_active_linehaul_pairs(orders):
        key = f"{from_hub}__{to_hub}"
        result["linehaul"][key] = run_linehaul_for_pair(from_hub, to_hub)

    for hub_zone in HUBS:
        stage3 = run_last_mile_for_hub(hub_zone, orders)
        if stage3:
            result["last_mile"][hub_zone] = stage3

    return result


if __name__ == "__main__":
    import json
    result = run_full_pipeline()
    print(json.dumps(result, indent=2, ensure_ascii=False))