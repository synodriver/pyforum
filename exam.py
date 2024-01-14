"""Simple Travelling Salesperson Problem (TSP) between cities."""
from typing import Tuple

import numpy as np
from ortools.constraint_solver import pywrapcp, routing_enums_pb2


def create_data_model():
    """Stores the data for the problem."""
    return np.array(
        [
            [0, 1, 2, 1, 0],
            [1, 0, 1, 2, 0],
            [2, 1, 0, 1, 0],
            [1, 2, 1, 0, 0],
            [0, 0, 0, 0, 0],
        ]
    )


def eval_solution(manager, routing, solution) -> Tuple[int, list]:
    """Prints solution on console."""
    # print('Objective: {} miles'.format(solution.ObjectiveValue()))
    index = routing.Start(0)
    # plan_output = 'Route for vehicle 0:\n'
    plan_output = []
    route_distance = 0
    while not routing.IsEnd(index):
        plan_output.append(manager.IndexToNode(index))
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        route_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
    plan_output.append(manager.IndexToNode(index))
    # print(plan_output)
    # print(route_distance)
    return solution.ObjectiveValue(), plan_output


def solve(matrix: np.ndarray, start=0, end=0):
    """Entry point of the program."""
    # Instantiate the data problem.
    # data = create_data_model()

    # Create the routing index manager.
    assert (matrix.T == matrix).all()
    manager = pywrapcp.RoutingIndexManager(matrix.shape[0], 1, [start], [end])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if solution:
        return eval_solution(manager, routing, solution)


if __name__ == "__main__":
    print(
        solve(
            np.array(
                [
                    [0, 1, 2, 1, 0],
                    [1, 0, 1, 2, 0],
                    [2, 1, 0, 1, 0],
                    [1, 2, 1, 0, 0],
                    [0, 0, 0, 0, 0],
                ]
            ),
            0,
            3,
        )
    )
