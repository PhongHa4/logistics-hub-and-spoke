from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from main import compute_time_matrix

def solve_simple_vrp():
    node_ids = [81537, 949220, 1155520, 990865, 385191]
    matrix = compute_time_matrix(node_ids)

    # OR-Tools cần số nguyên, nhưng cost của mình là số thực (giây có phần thập phân)
    # Nên làm tròn về giây nguyên - đủ chính xác cho bài toán logistics
    int_matrix = [[round(cell) for cell in row] for row in matrix]

    num_vehicles = 1
    depot_index = 0  # điểm 81537 làm kho xuất phát

    manager = pywrapcp.RoutingIndexManager(len(int_matrix), num_vehicles, depot_index)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    solution = routing.SolveWithParameters(search_parameters)

    if solution:
        print("✅ Tìm được lộ trình!")
        index = routing.Start(0)
        route = []
        total_cost = 0
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            route.append(node_ids[node])
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            total_cost += routing.GetArcCostForVehicle(previous_index, index, 0)
        route.append(node_ids[manager.IndexToNode(index)])
        print("Lộ trình (theo id điểm):", route)
        print(f"Tổng thời gian: {total_cost} giây (~{total_cost/60:.1f} phút)")
    else:
        print("❌ Không tìm được lời giải")

if __name__ == "__main__":
    solve_simple_vrp()