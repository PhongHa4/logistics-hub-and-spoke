from vrp_solver import solve_vrp
from main import compute_time_matrix, get_connection

HUB_A_HANOI = 1019649
HUB_B_HALONG = 501759


def load_mock_orders(order_type: str):
    """Đọc danh sách node_id + demand từ bảng mock_orders theo loại"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT node_id, demand_kg FROM mock_orders WHERE order_type = %s;",
        (order_type,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    node_ids = [int(row[0]) for row in rows]
    demands = [int(row[1]) for row in rows]
    return node_ids, demands


def run_first_mile(shop_node_ids, demands, capacity, max_vehicles):
    all_nodes = [HUB_A_HANOI] + shop_node_ids
    all_demands = [0] + demands
    return solve_vrp(
        node_ids=all_nodes, demands=all_demands,
        vehicle_capacity=capacity, max_vehicles=max_vehicles,
        fixed_cost=3000, span_coefficient=1, service_time=180,
    )


def run_linehaul():
    matrix = compute_time_matrix([HUB_A_HANOI, HUB_B_HALONG])
    return {"travel_time_s": matrix[0][1]}


def run_last_mile(delivery_node_ids, demands, capacity, max_vehicles):
    all_nodes = [HUB_B_HALONG] + delivery_node_ids
    all_demands = [0] + demands
    return solve_vrp(
        node_ids=all_nodes, demands=all_demands,
        vehicle_capacity=capacity, max_vehicles=max_vehicles,
        fixed_cost=3000, span_coefficient=1, service_time=180,
    )


if __name__ == "__main__":
    shop_ids, shop_demands = load_mock_orders("shop")
    delivery_ids, delivery_demands = load_mock_orders("delivery")

    print(f"Số shop: {len(shop_ids)}, tổng demand: {sum(shop_demands)}kg")
    print(f"Số điểm giao: {len(delivery_ids)}, tổng demand: {sum(delivery_demands)}kg")

    CAPACITY = 100      # tải trọng mỗi xe (kg) - đặt đủ lớn so với tổng demand
    MAX_VEHICLES = 8    # số xe tối đa có sẵn, đặt dư ra để thuật toán tự chọn

    print("\n--- First-mile (gom hàng về Hub A - Hà Nội) ---")
    stage1 = run_first_mile(shop_ids, shop_demands, CAPACITY, MAX_VEHICLES)
    print(f"Số xe dùng: {stage1['vehicles_used']}, tổng cost: {stage1['total_cost']}")

    print("\n--- Linehaul (Hub A -> Hub B) ---")
    stage2 = run_linehaul()
    print(f"Thời gian di chuyển: {stage2['travel_time_s']}s (~{stage2['travel_time_s']/60:.1f} phút)")

    print("\n--- Last-mile (phát hàng từ Hub B - Hạ Long) ---")
    stage3 = run_last_mile(delivery_ids, delivery_demands, CAPACITY, MAX_VEHICLES)
    print(f"Số xe dùng: {stage3['vehicles_used']}, tổng cost: {stage3['total_cost']}")