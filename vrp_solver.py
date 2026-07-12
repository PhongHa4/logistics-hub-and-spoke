from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from time_matrix import compute_time_matrix


def solve_vrp(
    node_ids: list[int],
    demands: list[int],
    vehicle_capacity: int,
    max_vehicles: int,
    fixed_cost: int = 0,
    span_coefficient: int = 0,
    service_time: int = 0,
    depot_index: int = 0,
):
    """
    Giải bài toán VRP cho 1 tầng (dùng chung cho First-mile lẫn Last-mile).

    node_ids: danh sách id đỉnh (node đầu tiên = kho/depot)
    demands: nhu cầu (kg) tương ứng từng điểm, depot phải = 0
    vehicle_capacity: tải trọng tối đa MỖI xe (giả định các xe giống nhau)
    max_vehicles: số xe TỐI ĐA có sẵn ở kho (thuật toán sẽ tự chọn dùng bao nhiêu
                  trong số này, nhờ fixed_cost "ép" không dùng dư thừa)
    fixed_cost: phạt mỗi lần 1 xe được dùng (điều khiển "tốn ít xe nhất")
    span_coefficient: phạt xe bận nhất (điều khiển cân bằng tải giữa các xe)
    service_time: thời gian dừng dỡ hàng tại mỗi điểm (cùng đơn vị với cost - giây)
    """
    matrix = compute_time_matrix(node_ids)
    int_matrix = [[round(cell) for cell in row] for row in matrix]

    vehicle_capacities = [vehicle_capacity] * max_vehicles

    manager = pywrapcp.RoutingIndexManager(len(int_matrix), max_vehicles, depot_index)
    routing = pywrapcp.RoutingModel(manager)

    # --- Cost tuyến đường: thuần quãng đường/thời gian di chuyển ---
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # --- Fixed Cost: ép dùng ít xe nhất có thể ---
    for vehicle_id in range(max_vehicles):
        routing.SetFixedCostOfVehicle(fixed_cost, vehicle_id)

    # --- Capacity: giới hạn tải trọng mỗi xe ---
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return demands[from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index, 0, vehicle_capacities, True, "Capacity"
    )

    # --- Time: di chuyển + service time, dùng cho Global Span ---
    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        service = service_time if from_node != depot_index else 0
        return int_matrix[from_node][to_node] + service

    time_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.AddDimension(time_callback_index, 0, 10**9, True, "Time")
    time_dimension = routing.GetDimensionOrDie("Time")
    time_dimension.SetGlobalSpanCostCoefficient(span_coefficient)

    # --- Giải ---
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.FromSeconds(5)

    solution = routing.SolveWithParameters(search_parameters)

    if not solution:
        return {"success": False, "routes": []}

    routes = []
    for vehicle_id in range(max_vehicles):
        index = routing.Start(vehicle_id)
        route_nodes = []
        route_load = 0
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            route_load += demands[node]
            route_nodes.append(node_ids[node])
            index = solution.Value(routing.NextVar(index))
        route_nodes.append(node_ids[manager.IndexToNode(index)])

        if len(route_nodes) > 2:  # bỏ qua xe không dùng đến
            route_time = solution.Value(time_dimension.CumulVar(index))
            routes.append({
                "vehicle_id": vehicle_id,
                "route": route_nodes,
                "load_kg": route_load,
                "time_s": route_time,
            })

    return {
        "success": True,
        "vehicles_used": len(routes),
        "routes": routes,
        "total_cost": solution.ObjectiveValue(),
    }


if __name__ == "__main__":
    result = solve_vrp(
        node_ids=[81537, 949220, 1155520, 990865, 385191],
        demands=[0, 8, 12, 5, 9],
        vehicle_capacity=20,
        max_vehicles=3,
        fixed_cost=3000,      # tăng mạnh - đủ sức "răn đe" so với chi phí hàng nghìn giây
        span_coefficient=1,   # giảm mạnh - chỉ còn vai trò "tinh chỉnh nhẹ", không lấn át fixed_cost
        service_time=180,
    )
    print(result)