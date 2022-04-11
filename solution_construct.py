import random
import numpy as np
import copy

from requests import count_requests, get_od_from_request_group, get_max_pick_time, \
    pop_request, remove_from_request_dictionairy

from static_operators import find_best_position_for_request_group, insert_request_group, \
    remove_request_group, add_request_group_to_dict, select_random_request_groups, find_random_position_for_request_group

from vehicle import locate_request_group_in_schedule

from solution_evaluation import select_most_costly_request_groups, get_objective_function_val

from parameters import cost_matrix, nb_of_required_ser


def init_fill_every_vehicle(request_dict, nb_of_available_veh, seed=True):
    """
    Function that fills every vehicle with a request group to start.
    A node ID consists of the stop id, followed by its occurence in the schedule.
    The latter is done because a dictionairy cannot hold keys with the same name.
    """
    vehicles_schedule = dict()

    for v in range(1, nb_of_available_veh+1):
        if seed is True:
            random.seed(1)

        request_group = pop_request(request_dict)
        remove_from_request_dictionairy(request_dict, request_group)

        o, d = get_od_from_request_group(request_group)
        pt = get_max_pick_time(request_group)

        vehicles_schedule[v] = dict()
        vehicles_schedule[v][str(o)+',0'] = [pt, request_group]
        vehicles_schedule[v][str(d)+',0'] = [round(pt + cost_matrix[(o, d)], 2)]

    return vehicles_schedule


def generate_initial_solution(requests_dict, vehicles_schedule=None):
    """
    An alternative version to the initial solution build, which does not
    assume fixed vehicle schedules.
    """

    if vehicles_schedule is None:
        vehicles_schedule = init_fill_every_vehicle(requests_dict, nb_of_required_ser)

    if count_requests(requests_dict) == 0:
        return vehicles_schedule
    else:
        request_group = pop_request(requests_dict)

    candidate_position = find_best_position_for_request_group(vehicles_schedule, request_group)
    candidate_vehicle, candidate_pos_within_veh = candidate_position[0], candidate_position[1]

    insert_request_group(vehicles_schedule, requests_dict, request_group, candidate_vehicle, candidate_pos_within_veh)
    return generate_initial_solution(requests_dict, vehicles_schedule)


def static_optimization(vehicles_schedule, required_requests_per_it=1, nb_of_iterations=1, temp_request_dict=None):
    """
    Performs the static optimization for a number of iterations. The static optimization happens as follows:
    - In every iteration, the 'required_request_per_it' most costly requests are (1) removed from their current position
    and (2) inserted into a new one. This encompasses the intensification part of the algorithm.
    - Every 'shuffle_threshold' iterations, the solution is shaken in order to escape local optima.

    """

    # should we do the copy do inside the loop, and only make this the incumbent if we achieve an improvement?
    it = 0

    new_positions = dict()

    while it < nb_of_iterations:
        temp_schedule = copy.deepcopy(vehicles_schedule)

        most_costly_requests = select_most_costly_request_groups(temp_schedule, required_requests_per_it)

        print('current iteration: ', it)
        for request_group in most_costly_requests:
            # print(request_group)
            remove_request_group(temp_schedule, request_group)
            temp_request_dict = add_request_group_to_dict(request_group, temp_request_dict)

        new_positions[it] = []

        while count_requests(temp_request_dict) != 0:
            request_group = pop_request(temp_request_dict, seed=True)
            candidate_vehicle, candidate_node, score = find_best_position_for_request_group(temp_schedule, request_group)
            new_positions[it].append((request_group, candidate_vehicle, candidate_node))
            insert_request_group(temp_schedule, temp_request_dict, request_group, candidate_vehicle, candidate_node)

        if get_objective_function_val(temp_schedule) < get_objective_function_val(vehicles_schedule):
            print('new improvement found: ', get_objective_function_val(temp_schedule))
            vehicles_schedule = temp_schedule
        else:
            print('start shuffle...')
            vehicles_schedule = shuffle_solution(vehicles_schedule, intensity=50)

        it += 1

    return vehicles_schedule, new_positions


def shuffle_solution(vehicles_schedule, intensity=50, temp_request_dict=None):
    """
    Function which shakes a solution schedule. The intensity parameter
    indicates how many requests are lifted and moved elsewhere. The shaking process goes as follows:
    - 'intensity' amount of requests are removed from the schedule and put in a random
    """

    if not temp_request_dict:
        temp_request_dict = dict()

    random_request_groups = select_random_request_groups(vehicles_schedule, intensity)

    for request_group in random_request_groups:
        remove_request_group(vehicles_schedule, request_group)
        temp_request_dict = add_request_group_to_dict(request_group, temp_request_dict)

    while count_requests(temp_request_dict) != 0:
        request_group = pop_request(temp_request_dict, seed=False)
        candidate_vehicle, candidate_node = find_random_position_for_request_group(vehicles_schedule, request_group)
        insert_request_group(vehicles_schedule, temp_request_dict, request_group, candidate_vehicle, candidate_node)

    return vehicles_schedule


