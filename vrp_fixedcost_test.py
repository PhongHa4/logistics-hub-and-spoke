from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def solve_vrp(fixed_cost_per_vehicle):
    # node 0 = kho, node 1,2 = cụm A, node 3,4 = cụm B
    hand_matrix = [
        [0,   10,  12,  10,  12],
        [10,  0,   3,   100, 100],
        [12,  3,   0,   100, 100],
        [10,  100, 100, 0,   3  ],
        [12,  100, 100, 3,   0  ],
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

    # --- Fixed Cost: đánh "thuế" mỗi khi 1 xe được dùng ---
    for vehicle_id in range(num_vehicles):
        routing.SetFixedCostOfVehicle(fixed_cost_per_vehicle, vehicle_id)
    # --- Hết phần Fixed Cost ---

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    solution = routing.SolveWithParameters(search_parameters)

    print(f"\n=== Fixed Cost = {fixed_cost_per_vehicle} ===")
    if solution:
        for vehicle_id in range(num_vehicles):
            index = routing.Start(vehicle_id)
            route = []
            while not routing.IsEnd(index):
                route.append(manager.IndexToNode(index))
                index = solution.Value(routing.NextVar(index))
            route.append(manager.IndexToNode(index))
            if len(route) > 2:  # chỉ in xe có chạy thật (không in tuyến rỗng)
                print(f"Xe {vehicle_id}: {route}")
        print(f"Tổng cost: {solution.ObjectiveValue()}")
    else:
        print("Không tìm được lời giải")

if __name__ == "__main__":
    solve_vrp(fixed_cost_per_vehicle=0)     # baseline - chưa phạt
    solve_vrp(fixed_cost_per_vehicle=200)   # phạt nặng - đủ để ép về 1 xe