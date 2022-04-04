import solution_evaluation as se
import solution_generation as sg
import vehicle as vg
import requests as rg
import break_and_repair_op as br

import copy

# TODO: Do we do the check for available capacity in the outer or inner function?
# If we do it in the outer functions, we can control which portion is 'sent' in as request group better
# so, then within this next function, we assume that the insertion is feasible!


def static_opt(solution, treated_requests_per_it=1, nb_of_iterations=1):
    """
    Performs the static optimization for a number of iterations.

    """

    solution = copy.deepcopy(solution)
    it = 0

    while it < nb_of_iterations:

        most_costly_requests = br.list_most_costly_requests(solution, treated_requests_per_it)
        # TODO: keep a tabu list of already made moves?

        old_positions = []

        for tup_request_group in most_costly_requests:
            old_positions.append((tup_request_group[0], rg.get_od_from_request_group(tup_request_group[1])[0]))
            br.remove_request_group(solution, tup_request_group[1], tup_request_group[0])

        # print(old_positions)
        # print(most_costly_requests)

        new_positions = []

        for index in range(len(most_costly_requests)):
            request_group = most_costly_requests[index][1]
            old_pos = old_positions[index]

            best_new_pos = br.find_first_available_best_insertion(solution, request_group, [old_pos])
            new_positions.append(best_new_pos[0])
            # be aware! insertion happens now in the order of most costly request!
            br.insert_request_group(solution, best_new_pos[0][0], request_group)

        it += 1
        # print(new_positions)

    return solution


def shuffle_solution(solution, intensity=50):
    '''
    Function which shakes a solution schedule. The intensity parameter
    indicates how many requests are lifted.
    '''
    return None



