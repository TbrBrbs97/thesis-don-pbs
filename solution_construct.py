import random
import numpy as np
from copy import deepcopy
import time
from pdb import set_trace


from requests import count_requests, get_od_from_request_group, get_max_pick_time, \
    pop_request_group, remove_from_request_dictionairy, add_request_group_to_dict

from static_operators import find_best_position_for_request_group, insert_request_group, \
    remove_request_group, select_random_request_groups, find_random_position_for_request_group, \
    find_first_best_improvement_for_request_group, occupy_available_seats

from dynamic_operators import collect_request_until_time, find_best_position_for_dynamic_request

from vehicle import locate_request_group_in_schedule, count_assigned_request_groups, get_copy_vehicles_schedule

from solution_evaluation import select_most_costly_request_groups, get_objective_function_val

from parameters import cost_matrix, nb_of_available_vehicles, M, disturbance_ratio, shuffle_ratio


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

        request_group = pop_request_group(request_dict)
        vehicles_schedule[v] = dict()
        insert_request_group(vehicles_schedule, request_dict, request_group, vehicle=v, position='first entry')

    return vehicles_schedule


def generate_initial_solution(requests_dict, vehicles_schedule=None, score_dict=None):
    """
    An alternative version to the initial solution build, which does not
    assume fixed vehicle schedules.
    """

    if score_dict is None:
        score_dict = dict()

    if vehicles_schedule is None:
        vehicles_schedule = init_fill_every_vehicle(requests_dict, nb_of_available_vehicles)

    if count_requests(requests_dict) == 0:
        return vehicles_schedule, score_dict
    else:
        request_group = pop_request_group(requests_dict)

    candidate_position = find_best_position_for_request_group(vehicles_schedule, request_group)
    # print(candidate_position)
    candidate_vehicle, candidate_node, score = candidate_position
    score_dict[str(request_group)] = score  # does not take into account that request groups might be split up!
    # should we maybe take the splitting up already into account in the cost calculation process?

    insert_request_group(vehicles_schedule, requests_dict, request_group, candidate_vehicle, candidate_node)
    return generate_initial_solution(requests_dict, vehicles_schedule, score_dict)


def static_optimization(vehicles_schedule, required_requests_per_it=1, time_limit=5, temp_request_dict=None):
    """
    Performs the static optimization for a number of iterations. The static optimization happens as follows:
    - In every iteration, the 'required_request_per_it' most costly requests are (1) removed from their current position
    and (2) inserted into a new one. This encompasses the intensification part of the algorithm.
    - Every 'shuffle_threshold' iterations, the solution is shaken in order to escape local optima.

    """
    time_limit *= 60  # convert time limit to seconds

    it = 0
    dis = 0 # counter which keeps track of the amount of disturbances

    elapsed_time = 0
    new_positions = dict()

    best_schedule_so_far = None

    while elapsed_time < time_limit:

        if not best_schedule_so_far or get_objective_function_val(best_schedule_so_far) > get_objective_function_val(vehicles_schedule):
            best_schedule_so_far = vehicles_schedule

        start_time = time.time()
        temp_schedule = deepcopy(vehicles_schedule)

        most_costly_requests = select_most_costly_request_groups(temp_schedule, required_requests_per_it)

        print('current iteration: ', it, 'obj. func: ', get_objective_function_val(temp_schedule))
        for request_group in most_costly_requests:
            remove_request_group(temp_schedule, request_group)
            temp_request_dict = add_request_group_to_dict(request_group, temp_request_dict)

        new_positions[it] = []

        while count_requests(temp_request_dict) != 0:
            request_group = pop_request_group(temp_request_dict, set_seed=False)
            candidate_vehicle, candidate_node, score = find_best_position_for_request_group(temp_schedule, request_group)
            new_positions[it].append((request_group, candidate_vehicle, candidate_node))
            insert_request_group(temp_schedule, temp_request_dict, request_group, candidate_vehicle, candidate_node)

        difference = get_objective_function_val(temp_schedule) - get_objective_function_val(vehicles_schedule)

        if difference < 0:
            print('new improvement found: ', get_objective_function_val(temp_schedule))
            vehicles_schedule = temp_schedule
        else:
            # disturbance_rate = max(abs(difference / 100), 0.05)
            disturbance_rate = disturbance_ratio + 0.005 * dis
            # disturbance_rate = max(disturbance_ratio + 0.005*it, abs(difference / 1000), 0.01)

            print('no improvement found, obj. func: ', get_objective_function_val(temp_schedule),
                  'disturb with rate: ', disturbance_rate)
            disturbed_schedule = disturb_solution(temp_schedule, disturbance=disturbance_rate)
            vehicles_schedule = disturbed_schedule
            dis += 1

        end_time = time.time()
        elapsed_time += end_time - start_time
        it += 1

    # print(get_objective_function_val(vehicles_schedule))
    return best_schedule_so_far, new_positions


def disturb_solution(vehicles_schedule, temp_request_dict=None, disturbance=disturbance_ratio):
    """
    Function which shakes a solution schedule. The intensity parameter
    indicates how many requests are lifted and moved elsewhere. The shaking process goes as follows:
    - 'intensity' amount of requests are removed from the schedule and put in a random
    """

    if not temp_request_dict:
        temp_request_dict = dict()

    request_groups_to_select = int(round(disturbance*count_assigned_request_groups(vehicles_schedule)))
    random_request_groups = select_random_request_groups(vehicles_schedule, request_groups_to_select)

    for request_group in random_request_groups:
        remove_request_group(vehicles_schedule, request_group)
        temp_request_dict = add_request_group_to_dict(request_group, temp_request_dict)

    while count_requests(temp_request_dict) != 0:
        request_group = pop_request_group(temp_request_dict, set_seed=False)
        # original_score = original_scores[str(request_group)]
        candidate_vehicle, candidate_node, score = find_best_position_for_request_group(vehicles_schedule,
                                                                                        request_group)
        insert_request_group(vehicles_schedule, temp_request_dict, request_group, candidate_vehicle, candidate_node)

    return vehicles_schedule


def large_shuffle(vehicles_schedule, temp_request_dict=None):
    """
    Function which shakes a solution schedule by a large amount. The shaking process goes as follows:
    """

    if not temp_request_dict:
        temp_request_dict = dict()

    request_groups_to_select = int(round(shuffle_ratio * count_assigned_request_groups(vehicles_schedule)))
    random_request_groups = select_random_request_groups(vehicles_schedule, request_groups_to_select)

    for request_group in random_request_groups:
        remove_request_group(vehicles_schedule, request_group)
        temp_request_dict = add_request_group_to_dict(request_group, temp_request_dict)

    while count_requests(temp_request_dict) != 0:
        request_group = pop_request_group(temp_request_dict, set_seed=False)
        candidate_vehicle, candidate_node = find_random_position_for_request_group(vehicles_schedule, request_group)
        insert_request_group(vehicles_schedule, temp_request_dict, request_group, candidate_vehicle, candidate_node)

    return vehicles_schedule


def generate_dynamic_solution(vehicles_schedule, dynamic_requests, lead_time, peak_hour_duration, temp_request_dict=None):
    """
    Lead time should be at least 1! That corresponds to ZLT in this case. A dynamic optimization is integrated in the
    algorithm as well.
    """

    current_time = 0

    if not temp_request_dict:
        temp_request_dict = {}
        for request in dynamic_requests:
            temp_request_dict = add_request_group_to_dict(request, temp_request_dict)

    while current_time < peak_hour_duration:
        print('current time: ', current_time)
        if current_time % lead_time == 0:
            selected_requests = collect_request_until_time(dynamic_requests, current_time, lead_time)
            print('inserting requests: ', selected_requests)
            if len(selected_requests) != 0:
                for request in selected_requests:
                    candidate_vehicle, candidate_node, score = find_best_position_for_dynamic_request(vehicles_schedule,
                                                                                                      request, current_time)
                    insert_request_group(vehicles_schedule, temp_request_dict, request, candidate_vehicle, candidate_node)
        current_time += 1

    return vehicles_schedule


def dynamic_optimization(vehicles_schedule, current_time):
    """
    An alteration on the static optimization which takes into account the locking point, that is, only that
    portion of vehicles schedule beyond the 'current_time' can be dealt with.
    """