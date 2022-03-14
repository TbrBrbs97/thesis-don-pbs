import solution_evaluation as se
import solution_generation as sg
import vehicle_generation as vg
import requests_generation as rg
import break_and_repair_op as br

import copy

# TODO: Do we do the check for available capacity in the outer or inner function?
# If we do it in the outer functions, we can control which portion is 'sent' in as request group better
# so, then within this next function, we assume that the insertion is feasible!


def static_opt(solution, od_matrix, network_dim, nb_of_iterations=1):
    """
    Performs the static optimization for a number of iterations.

    """

    solution = copy.deepcopy(solution)

    amount_removed = 1
    most_costly_requests = br.list_most_costly_requests(solution, od_matrix, network_dim, amount_removed)

    old_positions = []

    for request_group in most_costly_requests:
        old_positions.append(sg.get_request_group_position(solution, request_group)[:2])
        br.remove_request_group(solution, request_group, od_matrix, network_dim)

    for index in range(len(most_costly_requests)):
        request_group = most_costly_requests[index][1]
        old_pos = old_positions[index]

        best_new_pos = br.find_best_insertion(solution, request_group, old_pos)
        #TODO: here, the capacity constraint should be checked!
        # - Also, what about splitting up requests? If only a portion can be added, what do we do with the rest?
        br.insert_request_group(solution, best_new_pos, request_group, od_matrix, network_dim)

    return solution


def shuffle_solution(solution, intensity=50):
    '''
    Function which shakes a solution schedule. The intensity parameter
    indicates how many requests are lifted.
    '''
    return None



