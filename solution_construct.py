import copy
import random
import numpy as np
from copy import deepcopy
import time

from requests import count_requests, get_od_from_request_group, get_max_pick_time, \
    pop_request_group, remove_from_request_dictionairy, add_request_group_to_dict

from static_operators import find_best_position_for_request_group, iter_find_best_position_for_request_group, \
    insert_request_group, remove_request_group, select_random_request_groups, find_random_position_for_request_group, \
    occupy_available_seats

from find_position import find_first_best_improvement_for_request_group_2, find_first_best_improvement_for_request_group

from dynamic_operators import collect_request_until_time, find_best_position_for_dynamic_request

from vehicle import locate_request_group_in_schedule, count_assigned_request_groups, \
    get_copy_vehicles_schedule, count_total_assigned_requests

from solution_evaluation import select_most_costly_request_groups, \
    get_objective_function_val, calc_request_group_waiting_time, \
    calc_request_group_invehicle_time, calc_request_group_opportunity_cost

from parameters import cost_matrix, nb_of_available_vehicles, M, disturbance_ratio, shuffle_ratio, delta, network_size


def init_fill_every_vehicle(request_dict, nb_of_available_veh, seed=True):
    """
    Function that fills every vehicle with a request group to start.
    A node ID consists of the stop id, followed by its occurence in the schedule.
    The latter is done because a dictionairy cannot hold keys with the same name.
    """
    vehicles_schedule = dict()

    for v in range(1, nb_of_available_veh + 1):
        if seed is True:
            random.seed(1)

        request_group = pop_request_group(request_dict)
        vehicles_schedule[v] = dict()
        insert_request_group(vehicles_schedule, request_dict, request_group, vehicle=v, position='first entry')

    return vehicles_schedule


def generate_initial_solution(requests_dict, vehicles_schedule=None):
    """
    An alternative version to the initial solution build, which does not
    assume fixed vehicle schedules. NOTE: This is a recursive function!
    """

    if vehicles_schedule is None:
        vehicles_schedule = init_fill_every_vehicle(requests_dict, nb_of_available_vehicles)

    if count_requests(requests_dict) == 0:
        return vehicles_schedule
    else:
        request_group = pop_request_group(requests_dict)

    candidate_position = find_best_position_for_request_group(vehicles_schedule, request_group)
    candidate_vehicle, candidate_node, score = candidate_position
    # print(portion, candidate_position)
    insert_request_group(vehicles_schedule, requests_dict, request_group, candidate_vehicle, candidate_node)
    return generate_initial_solution(requests_dict, vehicles_schedule)


def iter_generate_initial_solution(requests_dict, vehicles_schedule=None):
    """
    An iterative version of the initial solution generator, to be used in case the networks get too big
    or demand gets too numerous.
    """

    if vehicles_schedule is None:
        vehicles_schedule = init_fill_every_vehicle(requests_dict, nb_of_available_vehicles)

    iteration = 0
    while count_requests(requests_dict) != 0:
        # print(iteration)

        request_group = pop_request_group(requests_dict)
        # print(portion)
        candidate_position = iter_find_best_position_for_request_group(vehicles_schedule, request_group)
        candidate_vehicle, candidate_node, score = candidate_position

        insert_request_group(vehicles_schedule, requests_dict, request_group, candidate_vehicle, candidate_node)
        iteration += 1

    return vehicles_schedule


def static_optimization(vehicles_schedule, required_requests_per_it=1, time_limit=5, temp_request_dict=None):
    """
    Performs the static optimization for a number of iterations. The static optimization happens as follows:
    - In every iteration, the 'required_request_per_it' most costly requests are (1) removed from their current position
    and (2) inserted into a new one. This encompasses the intensification part of the algorithm.
    - Every 'shuffle_threshold' iterations, the solution is shaken in order to escape local optima.

    """
    time_limit *= 60  # convert time limit to seconds

    it = 0
    dis = 0  # counter which keeps track of the amount of disturbances
    shf = 0  # counter which keeps track of the amount of shuffles

    elapsed_time = 0
    best_schedule_so_far = None

    while elapsed_time < time_limit:
        if not best_schedule_so_far or get_objective_function_val(best_schedule_so_far) > get_objective_function_val(
                vehicles_schedule):
            best_schedule_so_far = vehicles_schedule

        start_time = time.time()
        temp_schedule = deepcopy(vehicles_schedule)

        most_costly_requests = select_most_costly_request_groups(temp_schedule, required_requests_per_it)

        print('current iteration: ', it, 'obj. func: ', get_objective_function_val(temp_schedule))
        for request_group in most_costly_requests:
            remove_request_group(temp_schedule, request_group)
            temp_request_dict = add_request_group_to_dict(request_group, temp_request_dict)

        while count_requests(temp_request_dict) != 0:
            request_group = pop_request_group(temp_request_dict, set_seed=False)
            candidate_vehicle, candidate_node, score = find_best_position_for_request_group(temp_schedule,
                                                                                            request_group)
            insert_request_group(temp_schedule, temp_request_dict, request_group, candidate_vehicle, candidate_node)

        difference = get_objective_function_val(temp_schedule) - get_objective_function_val(vehicles_schedule)

        if difference < 0:
            print('new improvement found: ', get_objective_function_val(temp_schedule))
            vehicles_schedule = temp_schedule
        else:
            # disturbance_rate = min(disturbance_ratio + 0.005 * dis, 0.45)
            disturbance_rate = disturbance_ratio

            print('no improvement found, obj. func: ', get_objective_function_val(temp_schedule),
                  'disturb with rate: ', disturbance_rate)
            disturbed_schedule = disturb_solution_2(temp_schedule, disturbance=disturbance_rate)
            vehicles_schedule = disturbed_schedule
            dis += 1

        if get_objective_function_val(vehicles_schedule) >= \
                get_objective_function_val(best_schedule_so_far) and it % 5 == 0 and it != 0:
            # shuffle_rate = min(shuffle_ratio + shf*0.01, 0.8)
            shuffle_rate = shuffle_ratio
            print('performing large shuffle with rate: ', shuffle_rate)
            vehicles_schedule = large_shuffle_3(vehicles_schedule, shuffle_rate=shuffle_rate)
            shf += 1

        end_time = time.time()
        elapsed_time += end_time - start_time
        it += 1

    return best_schedule_so_far


def disturb_solution(vehicles_schedule, temp_request_dict=None, disturbance=disturbance_ratio):
    """
    Function which shakes a solution schedule. The intensity parameter
    indicates how many requests are lifted and moved elsewhere. The shaking process goes as follows:
    - 'intensity' amount of requests are removed from the schedule and put in a random
    """

    if not temp_request_dict:
        temp_request_dict = dict()

    request_groups_to_select = int(round(disturbance * count_assigned_request_groups(vehicles_schedule)))
    random_request_groups = select_random_request_groups(vehicles_schedule, request_groups_to_select)

    for request_group in random_request_groups:
        remove_request_group(vehicles_schedule, request_group)
        temp_request_dict = add_request_group_to_dict(request_group, temp_request_dict)

    while count_requests(temp_request_dict) != 0:
        request_group = pop_request_group(temp_request_dict, set_seed=False)
        candidate_vehicle, candidate_node, score = find_best_position_for_request_group(vehicles_schedule,
                                                                                        request_group)
        insert_request_group(vehicles_schedule, temp_request_dict, request_group, candidate_vehicle, candidate_node)

    return vehicles_schedule


def disturb_solution_2(vehicles_schedule, temp_request_dict=None, disturbance=disturbance_ratio):
    """
    Function which shakes a solution schedule. The intensity parameter
    indicates how many requests are lifted and moved elsewhere. The shaking process goes as follows:
    - 'intensity' amount of requests are removed from the schedule and put in a random
    """

    if not temp_request_dict:
        temp_request_dict = dict()

    request_groups_to_select = int(round(disturbance * count_assigned_request_groups(vehicles_schedule)))
    random_request_groups = select_random_request_groups(vehicles_schedule, request_groups_to_select)

    for request_group in random_request_groups:
        original_score = calc_request_group_waiting_time(vehicles_schedule, request_group) + \
                         calc_request_group_invehicle_time(vehicles_schedule, request_group)

        temp_schedule = copy.deepcopy(vehicles_schedule)

        remove_request_group(temp_schedule, request_group)
        temp_request_dict = add_request_group_to_dict(request_group, temp_request_dict)

        # candidate_vehicle, candidate_node, score = \
        #     find_first_best_improvement_for_request_group(vehicles_schedule, portion, original_score)

        candidate_vehicle, candidate_node, score = find_best_position_for_request_group(temp_schedule,
                                                                                        request_group)
        insert_request_group(temp_schedule, temp_request_dict, request_group, candidate_vehicle, candidate_node)
        new_opportunity_cost = calc_request_group_opportunity_cost(temp_schedule, request_group)

        if new_opportunity_cost < original_score:
            vehicles_schedule = temp_schedule

    return vehicles_schedule


def large_shuffle(vehicles_schedule, temp_request_dict=None, shuffle_rate=shuffle_ratio):
    """
    Function which shakes a solution schedule by a large amount. The shaking process goes as follows:
    """

    if not temp_request_dict:
        temp_request_dict = dict()

    request_groups_to_select = int(round(shuffle_rate * count_assigned_request_groups(vehicles_schedule)))
    random_request_groups = select_random_request_groups(vehicles_schedule, request_groups_to_select)

    for request_group in random_request_groups:
        # original_obj_func_value = get_objective_function_val(vehicles_schedule)
        original_score = calc_request_group_opportunity_cost(vehicles_schedule, request_group)

        temp_schedule = copy.deepcopy(vehicles_schedule)
        # print(count_total_assigned_requests(vehicles_schedule))

        remove_request_group(temp_schedule, request_group)
        temp_request_dict = add_request_group_to_dict(request_group, temp_request_dict)
        # candidate_vehicle, candidate_node, score = find_first_best_improvement_for_request_group(temp_schedule,
        #                                                                                          portion, original_score=M/4)
        candidate_vehicle, candidate_node, score = find_first_best_improvement_for_request_group_2(temp_schedule,
                                                                                                 request_group, original_score=original_score)

        # TODO check if you have to constrain position by 'if obj_func of temp < original schedule AFTER insertion in temp above!
        # if get_objective_function_val(temp_schedule) < original_obj_func_value:
        # if the result is satisfactory, perform it on the original vehicles schedule

        if candidate_node != 'current pos':
            remove_request_group(vehicles_schedule, request_group)
            insert_request_group(vehicles_schedule, temp_request_dict, request_group, candidate_vehicle, candidate_node)

    return vehicles_schedule


def large_shuffle_2(vehicles_schedule, temp_request_dict=None, shuffle_rate=shuffle_ratio):
    """
    Function which shakes a solution schedule by a large amount. The shaking process goes as follows:
    """

    if not temp_request_dict:
        temp_request_dict = dict()

    request_groups_to_select = int(round(shuffle_rate * count_assigned_request_groups(vehicles_schedule)))
    random_request_groups = select_random_request_groups(vehicles_schedule, request_groups_to_select)

    for request_group in random_request_groups:
        original_obj_func_value = get_objective_function_val(vehicles_schedule)
        temp_schedule = copy.deepcopy(vehicles_schedule)

        remove_request_group(temp_schedule, request_group)
        temp_request_dict = add_request_group_to_dict(request_group, temp_request_dict)
        candidate_vehicle, candidate_node, score = find_best_position_for_request_group(temp_schedule, request_group)

        if get_objective_function_val(temp_schedule) < original_obj_func_value:
            remove_request_group(vehicles_schedule, request_group)
            insert_request_group(vehicles_schedule, temp_request_dict, request_group, candidate_vehicle, candidate_node)

    return vehicles_schedule


def large_shuffle_3(vehicles_schedule, temp_request_dict=None, shuffle_rate=shuffle_ratio):
    """
    Function which shakes a solution schedule by a large amount. The shaking process goes as follows:
    """

    if not temp_request_dict:
        temp_request_dict = dict()

    request_groups_to_select = int(round(shuffle_rate * count_assigned_request_groups(vehicles_schedule)))
    random_request_groups = select_random_request_groups(vehicles_schedule, request_groups_to_select)

    for request_group in random_request_groups:
        o, d = get_od_from_request_group(request_group)
        original_score = round(calc_request_group_opportunity_cost(vehicles_schedule, request_group), 2)

        temp_schedule = copy.deepcopy(vehicles_schedule)

        remove_request_group(temp_schedule, request_group)
        temp_request_dict = add_request_group_to_dict(request_group, temp_request_dict)
        request_dict_copy = deepcopy(temp_request_dict)

        positions = []
        assigned_so_far = []
        while len(assigned_so_far) != len(request_group):
            portion = pop_request_group(request_dict_copy)
            print(portion)

            candidate_vehicle, candidate_node, score, added_portion = find_first_best_improvement_for_request_group_2(
                                                                temp_schedule, portion, original_score=original_score)
            insert_request_group(temp_schedule, request_dict_copy, portion,
                                 candidate_vehicle, candidate_node)
            positions.append((added_portion, candidate_vehicle, candidate_node, score))
            assigned_so_far += added_portion
            if candidate_node != 'current pos':
                original_score -= calc_request_group_opportunity_cost(temp_schedule, added_portion)

        if all([candidate[2] != 'current pos' for candidate in positions]):
            remove_request_group(vehicles_schedule, request_group)
            for (added_portion, candidate_vehicle, candidate_node, score) in positions:
                insert_request_group(vehicles_schedule, temp_request_dict, added_portion,
                                     candidate_vehicle, candidate_node)
        else:
            temp_request_dict[(o, d)].remove(request_group)

    return vehicles_schedule


def generate_dynamic_solution(vehicles_schedule, dynamic_requests, lead_time, peak_hour_duration,
                              temp_request_dict=None):
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
                                                                                                      request,
                                                                                                      current_time)
                    insert_request_group(vehicles_schedule, temp_request_dict, request, candidate_vehicle,
                                         candidate_node)
        if current_time % delta == 0:
            print('initiate dynamic optimization...')
            vehicles_schedule = dynamic_optimization(vehicles_schedule, current_time)

        current_time += 1

    return vehicles_schedule


def dynamic_optimization(vehicles_schedule, current_time, required_requests_per_it=1, time_limit=0.2,
                         temp_request_dict=None):
    """
    An alteration on the static optimization which takes into account the locking point, that is, only that
    portion of vehicles schedule beyond the 'current_time' can be dealt with. That is:
    - Only requests at a stop with departure time beyond 'current_time' can be removed
    - And they can only be reinserted in spots with a departure time beyond 'current_time'
    """

    if not temp_request_dict:
        temp_request_dict = dict()

    time_limit *= 60
    it = 0
    elapsed_time = 0
    best_schedule_so_far = None

    while elapsed_time < time_limit:

        if not best_schedule_so_far or get_objective_function_val(best_schedule_so_far) > get_objective_function_val(
                vehicles_schedule):
            best_schedule_so_far = vehicles_schedule

        start_time = time.time()
        temp_schedule = deepcopy(vehicles_schedule)

        most_costly_requests = select_most_costly_request_groups(temp_schedule, required_requests_per_it,
                                                                 current_time=current_time)

        print('current iteration: ', it, 'obj. func: ', get_objective_function_val(temp_schedule))
        for request_group in most_costly_requests:
            remove_request_group(temp_schedule, request_group)
            temp_request_dict = add_request_group_to_dict(request_group, temp_request_dict)

        while count_requests(temp_request_dict) != 0:
            request_group = pop_request_group(temp_request_dict, set_seed=False)
            candidate_vehicle, candidate_node, score = find_best_position_for_dynamic_request(temp_schedule,
                                                                                              request_group,
                                                                                              current_time)
            insert_request_group(temp_schedule, temp_request_dict, request_group, candidate_vehicle, candidate_node)

        difference = get_objective_function_val(temp_schedule) - get_objective_function_val(vehicles_schedule)

        if difference < 0:
            print('new improvement found: ', get_objective_function_val(temp_schedule))
            vehicles_schedule = temp_schedule
        else:
            print('returning best found solution: ', get_objective_function_val(best_schedule_so_far))
            return best_schedule_so_far

        end_time = time.time()
        elapsed_time += end_time - start_time
        it += 1

    print('returning best found solution: ', get_objective_function_val(best_schedule_so_far))
    return best_schedule_so_far
