from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from main import compute_time_matrix

def solve_vrp_with_capacity():
    node_ids = [81537, 1019649, 1020378, 501759, 552534]
    matrix = compute_time_matrix(node_ids)
    int_matrix = [[round(cell) for cell in row] for row in matrix]

    # Demand giả lập cho từng điểm (kg) - depot (index 0) luôn = 0
    demands = [0, 5, 5, 5, 5]

    num_vehicles = 2
    vehicle_capacities = [50, 50]  # mỗi xe chở tối đa 50kg
    depot_index = 0

    manager = pywrapcp.RoutingIndexManager(len(int_matrix), num_vehicles, depot_index)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # --- Phần mới: khai báo demand callback + ràng buộc capacity ---
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return demands[from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,                    # slack (không cho phép "dư thừa", để 0)
        vehicle_capacities,
        True,                 # start cumul to zero - mỗi xe bắt đầu với tải = 0
        "Capacity"
    )
    # --- Hết phần mới ---

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    solution = routing.SolveWithParameters(search_parameters)

    if solution:
        print("✅ Tìm được lộ trình!")
        for vehicle_id in range(num_vehicles):
            index = routing.Start(vehicle_id)
            route = []
            route_load = 0
            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                route_load += demands[node]
                route.append(node_ids[node])
                index = solution.Value(routing.NextVar(index))
            route.append(node_ids[manager.IndexToNode(index)])
            print(f"Xe {vehicle_id}: {route} | Tổng tải: {route_load}kg")
    else:
        print("❌ Không tìm được lời giải")

if __name__ == "__main__":
    solve_vrp_with_capacity()