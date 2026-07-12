from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

SERVICE_TIME = 5  # "5 phút" giả lập, cùng đơn vị với ma trận

def solve_vrp(span_coefficient, use_service_time):
    hand_matrix = [
        [0,  5,  6,  7,  50],
        [5,  0,  2,  3,  50],
        [6,  2,  0,  2,  50],
        [7,  3,  2,  0,  50],
        [50, 50, 50, 50, 0 ],
    ]

    num_vehicles = 2
    depot_index = 0

    manager = pywrapcp.RoutingIndexManager(len(hand_matrix), num_vehicles, depot_index)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return hand_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # --- Time callback: di chuyển + service time (nếu bật) ---
    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        service = SERVICE_TIME if (use_service_time and from_node != depot_index) else 0
        return hand_matrix[from_node][to_node] + service

    time_callback_index = routing.RegisterTransitCallback(time_callback)

    routing.AddDimension(
        time_callback_index,
        0,
        1000,
        True,
        "Time"
    )
    time_dimension = routing.GetDimensionOrDie("Time")
    time_dimension.SetGlobalSpanCostCoefficient(span_coefficient)
    # --- Hết phần Time ---

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    solution = routing.SolveWithParameters(search_parameters)

    label = "CÓ Service Time" if use_service_time else "KHÔNG Service Time"
    print(f"\n=== {label} (span_coefficient={span_coefficient}) ===")
    if solution:
        vehicle_times = []
        for vehicle_id in range(num_vehicles):
            index = routing.Start(vehicle_id)
            route = []
            while not routing.IsEnd(index):
                route.append(manager.IndexToNode(index))
                index = solution.Value(routing.NextVar(index))
            route.append(manager.IndexToNode(index))
            route_time = solution.Value(time_dimension.CumulVar(index))
            vehicle_times.append(route_time)
            if len(route) > 2:
                print(f"Xe {vehicle_id}: {route} | Thời gian xe này (Time dimension): {route_time}")
        print(f"Thời gian xe bận nhất: {max(vehicle_times)}")
    else:
        print("Không tìm được lời giải")

if __name__ == "__main__":
    solve_vrp(span_coefficient=50, use_service_time=False)
    solve_vrp(span_coefficient=50, use_service_time=True)