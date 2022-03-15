import solution_evaluation as se
import solution_generation as sg
import vehicle_generation as vg
import requests_generation as rg
import break_and_repair_op as br

import copy

# TODO: Do we do the check for available capacity in the outer or inner function?
# If we do it in the outer functions, we can control which portion is 'sent' in as request group better
# so, then within this next function, we assume that the insertion is feasible!


def static_opt(solution, nb_of_iterations=1):
    """
    Performs the static optimization for a number of iterations.

    """

    solution = copy.deepcopy(solution)

    amount_removed = 1
    most_costly_requests = br.list_most_costly_requests(solution, amount_removed)
    # TODO: keep a tabu list of already made moves?

    old_positions = []

    for request_group in most_costly_requests:
        old_positions.append(sg.get_request_group_position(solution, request_group[1])[:2])
        br.remove_request_group(solution, request_group[1])

    for index in range(len(most_costly_requests)):
        request_group = most_costly_requests[index][1]
        old_pos = old_positions[index]

        best_new_pos = br.find_first_available_best_insertion(solution, request_group, [old_pos])
        # be aware! insertion happens now in the order of most costly request!
        br.insert_request_group(solution, best_new_pos[0][0], request_group)

    return solution


def shuffle_solution(solution, intensity=50):
    '''
    Function which shakes a solution schedule. The intensity parameter
    indicates how many requests are lifted.
    '''
    return None



