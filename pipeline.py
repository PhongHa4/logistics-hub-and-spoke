from vrp_solver import solve_vrp
from main import compute_time_matrix

# Tọa độ 2 Hub - cần tìm id đỉnh thật gần nhất trong ways_vertices_pgr
HUB_A_HANOI = 1019649      # ví dụ, dùng tạm id gần Hồ Gươm đã tìm ở Bước 7B
HUB_B_HALONG = 501759      # id gần Hạ Long đã tìm ở Bước 7B


def run_first_mile(shop_node_ids: list[int], demands: list[int], capacity: int, max_vehicles: int):
    """Giai đoạn 1: gom hàng từ các shop về Hub A"""
    all_nodes = [HUB_A_HANOI] + shop_node_ids
    all_demands = [0] + demands
    return solve_vrp(
        node_ids=all_nodes,
        demands=all_demands,
        vehicle_capacity=capacity,
        max_vehicles=max_vehicles,
        fixed_cost=3000,
        span_coefficient=1,
        service_time=180,
    )


def run_linehaul():
    """Giai đoạn 2: xe tải nặng chạy thẳng Hub A -> Hub B (không cần VRP)"""
    matrix = compute_time_matrix([HUB_A_HANOI, HUB_B_HALONG])
    return {"travel_time_s": matrix[0][1]}


def run_last_mile(delivery_node_ids: list[int], demands: list[int], capacity: int, max_vehicles: int):
    """Giai đoạn 3: phát hàng từ Hub B đến các điểm nhận"""
    all_nodes = [HUB_B_HALONG] + delivery_node_ids
    all_demands = [0] + demands
    return solve_vrp(
        node_ids=all_nodes,
        demands=all_demands,
        vehicle_capacity=capacity,
        max_vehicles=max_vehicles,
        fixed_cost=3000,
        span_coefficient=1,
        service_time=180,
    )


def run_multi_tier_pipeline(shop_ids, shop_demands, delivery_ids, delivery_demands, capacity=20, max_vehicles=3):
    """Chạy trọn 3 giai đoạn, trả về kết quả tổng hợp"""
    stage1 = run_first_mile(shop_ids, shop_demands, capacity, max_vehicles)
    stage2 = run_linehaul()
    stage3 = run_last_mile(delivery_ids, delivery_demands, capacity, max_vehicles)

    return {
        "first_mile": stage1,
        "linehaul": stage2,
        "last_mile": stage3,
    }