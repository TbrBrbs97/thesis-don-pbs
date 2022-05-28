import copy
import random
from copy import deepcopy
from network_generation import generate_cost_matrix
import time

from requests import count_requests, get_rep_pick_up_time, \
    pop_request_group, remove_from_request_dictionairy, add_request_group_to_dict

from static_operators import find_best_position_for_request_group, iter_find_best_position_for_request_group, \
    insert_request_group, remove_request_group, select_random_request_groups, find_random_position_for_request_group, \
    occupy_available_seats

from find_position import find_first_best_improvement_for_request_group_2, \
    find_first_best_improvement_for_request_group, find_best_improvement_for_request_group

from dynamic_operators import collect_request_until_time, find_best_position_for_dynamic_request

from vehicle import locate_request_group_in_schedule, count_assigned_request_groups, \
    get_copy_vehicles_schedule, count_total_assigned_requests

from solution_evaluation import select_most_costly_request_groups, \
    get_objective_function_val, calc_request_group_waiting_time, \
    calc_request_group_invehicle_time, calc_request_group_opportunity_cost

from settings import disturbance_threshold, disturbance_ratio, shuffle_ratio,\
    shuffle_threshold, delta, v_mean, reinitiation_threshold


def init_fill_every_vehicle(network, requests_dict, nb_of_available_veh, seed=True, capacity=20, depot='terminal'):
    """
    Function that fills every vehicle with a request group to start.
    A node ID consists of the stop id, followed by its occurence in the schedule.
    The latter is done because a dictionairy cannot hold keys with the same name.
    """
    vehicles_schedule = dict()

    for v in range(1, nb_of_available_veh + 1):
        vehicles_schedule[v] = dict()
        if seed is True:
            random.seed(1)
        if count_requests(requests_dict) != 0:
            request_group = pop_request_group(requests_dict)
            insert_request_group(network, vehicles_schedule, requests_dict, request_group,
                                 vehicle=v, position='first entry', capacity=capacity, depot=depot)

    return vehicles_schedule


def generate_initial_solution(network, requests_dict, vehicles_schedule=None,
                              nb_of_available_veh=16, capacity=20, depot='terminal'):
    """
    An alternative version to the initial vehicles_schedule build, which does not
    assume fixed vehicle schedules. NOTE: This is a recursive function!
    """

    if vehicles_schedule is None:
        vehicles_schedule = init_fill_every_vehicle(network, requests_dict, nb_of_available_veh,
                                                    capacity=capacity, depot=depot)

    if count_requests(requests_dict) == 0:
        return vehicles_schedule
    else:
        request_group = pop_request_group(requests_dict)

    candidate_position = find_best_position_for_request_group(network, vehicles_schedule,
                                                              request_group, capacity=capacity, depot=depot)
    candidate_vehicle, candidate_node, score = candidate_position
    # print(len(request_group), candidate_position)
    insert_request_group(network, vehicles_schedule, requests_dict,
                         request_group, candidate_vehicle, candidate_node, capacity=capacity, depot=depot)
    return generate_initial_solution(network, requests_dict, vehicles_schedule, nb_of_available_veh, capacity, depot)


def iter_generate_initial_solution(network, requests_dict, vehicles_schedule=None,
                                   nb_of_available_veh=16, capacity=20, depot='terminal'):
    """
    An iterative version of the initial vehicles_schedule generator, to be used in case the networks get too big
    or demand gets too numerous.
    """

    if vehicles_schedule is None:
        vehicles_schedule = init_fill_every_vehicle(network, requests_dict, nb_of_available_veh)

    iteration = 0
    while count_requests(requests_dict) != 0:
        # print(iteration)

        request_group = pop_request_group(requests_dict)
        # print(request_group)
        candidate_position = iter_find_best_position_for_request_group(network, vehicles_schedule,
                                                                       request_group, capacity, depot=depot)
        candidate_vehicle, candidate_node, score = candidate_position

        insert_request_group(network, vehicles_schedule, requests_dict,
                             request_group, candidate_vehicle, candidate_node, capacity=capacity, depot=depot)
        iteration += 1

    return vehicles_schedule


def static_optimization(network, vehicles_schedule, required_requests_per_it=1, time_limit=5,
                        temp_request_dict=None, capacity=20, depot='terminal'):
    """
    Performs the static optimization for a number of iterations. The static optimization happens as follows:
    - In every iteration, the 'required_request_per_it' most costly requests are (1) removed from their current position
    and (2) inserted into a new one. This encompasses the intensification part of the algorithm.
    - Every 'shuffle_threshold' iterations, the vehicles_schedule is shaken in order to escape local optima.

    """
    time_limit *= 60  # convert time limit to seconds

    it = 0
    dis = 0  # counter which keeps track of the amount of disturbances
    shf = 0  # counter which keeps track of the amount of shuffles

    elapsed_time = 0
    best_iteration = 0
    best_schedule_so_far = None

    while elapsed_time < time_limit:

        start_time = time.time()
        temp_schedule = deepcopy(vehicles_schedule)

        most_costly_requests = select_most_costly_request_groups(network, temp_schedule, required_requests_per_it)

        print('current iteration: ', it, 'obj. func: ', get_objective_function_val(temp_schedule))

        j = 0
        # improvement_found = True
        while j < len(most_costly_requests): # improvement_found and
            request_group = most_costly_requests[j]
            temp_schedule = steepest_descent(network, vehicles_schedule, request_group, capacity=capacity, depot=depot)
            difference = get_objective_function_val(temp_schedule) - get_objective_function_val(vehicles_schedule)
            if difference < 0.0:
                print('new improvement found: ', get_objective_function_val(temp_schedule))
                vehicles_schedule = deepcopy(temp_schedule)
            # else:
            #     improvement_found = False
            j += 1

        if not best_schedule_so_far or get_objective_function_val(
                vehicles_schedule) < get_objective_function_val(best_schedule_so_far):
            print('NEW BEST SOLUTION', get_objective_function_val(vehicles_schedule))
            best_schedule_so_far = deepcopy(vehicles_schedule)
            best_iteration = it


        if get_objective_function_val(vehicles_schedule) >= \
                get_objective_function_val(best_schedule_so_far) and it % disturbance_threshold == 0 and it != 0:
            disturbance_rate = disturbance_ratio
            print('no further improvement found, obj. func: ', get_objective_function_val(vehicles_schedule),
                  'disturb with rate: ', disturbance_rate)
            vehicles_schedule = disturb_2(network, vehicles_schedule, disturbance=disturbance_rate, capacity=capacity,
                                        depot=depot)
            dis += 1

        if it % reinitiation_threshold == 0 and it != 0 and it % shuffle_threshold != 0:
            print('exploring new neighborhood using the incumbent:', get_objective_function_val(best_schedule_so_far))
            vehicles_schedule = best_schedule_so_far
            dis = 0

        # if get_objective_function_val(vehicles_schedule) >= \
        #         get_objective_function_val(best_schedule_so_far) and it % shuffle_threshold == 0 and it != 0:
        if get_objective_function_val(vehicles_schedule) >= \
                get_objective_function_val(best_schedule_so_far) and it == shuffle_threshold and it != 0:
            shuffle_rate = shuffle_ratio
            print('performing large shuffle with rate: ', shuffle_rate)
            vehicles_schedule = shuffle(network, vehicles_schedule, shuffle_rate=shuffle_rate, capacity=capacity,
                                        depot=depot)
            shf += 1


        end_time = time.time()
        elapsed_time += end_time - start_time
        it += 1

    return best_schedule_so_far, best_iteration


def steepest_descent(network, vehicles_schedule, request_group, temp_request_dict=None, capacity=20, depot='terminal'):
    """
    Function that removes a request group from the vehicle schedule and reinserts it in the best possible spot.
    This is the spot that is best suited according to 'find_best_post_cost'
    """
    if not temp_request_dict:
        temp_request_dict = dict()

    temp_schedule = deepcopy(vehicles_schedule)

    remove_request_group(network, temp_schedule, request_group)
    temp_request_dict = add_request_group_to_dict(request_group, temp_request_dict)

    while count_requests(temp_request_dict) != 0:
        request_group = pop_request_group(temp_request_dict, set_seed=False)
        candidate_vehicle, candidate_node, score = find_best_position_for_request_group(network, temp_schedule,
                                                                                        request_group, capacity=capacity,
                                                                                        depot=depot)
        insert_request_group(network, temp_schedule, temp_request_dict, request_group, candidate_vehicle, candidate_node,
                             capacity=capacity, depot=depot)

    return temp_schedule


def disturb(network, vehicles_schedule, temp_request_dict=None,
            disturbance=disturbance_ratio, capacity=20, depot='terminal'):
    """
    Function which shakes a vehicles_schedule schedule. The intensity parameter
    indicates how many requests are lifted and moved elsewhere. The shaking process goes as follows:
    - 'intensity' amount of requests are removed from the schedule and put in a random
    """

    if not temp_request_dict:
        temp_request_dict = dict()

    request_groups_to_select = int(round(disturbance * count_assigned_request_groups(vehicles_schedule)))
    random_request_groups = select_random_request_groups(vehicles_schedule, request_groups_to_select)

    for request_group in random_request_groups:
        remove_request_group(network, vehicles_schedule, request_group)
        temp_request_dict = add_request_group_to_dict(request_group, temp_request_dict)

    while count_requests(temp_request_dict) != 0:
        request_group = pop_request_group(temp_request_dict, set_seed=False)
        candidate_vehicle, candidate_node, score = find_best_position_for_request_group(network, vehicles_schedule,
                                                                                        request_group, capacity,
                                                                                        depot=depot)
        insert_request_group(network, vehicles_schedule, temp_request_dict, request_group,
                             candidate_vehicle, candidate_node, capacity=capacity, depot=depot)

    return vehicles_schedule


def disturb_2(network, vehicles_schedule, temp_request_dict=None,
              disturbance=disturbance_ratio, capacity=20, depot='terminal'):
    """
    Function which shakes a vehicles_schedule schedule by a large amount. The shaking process goes as follows:
    """

    if not temp_request_dict:
        temp_request_dict = dict()

    nb_request_groups_to_select = min(int(round(disturbance * count_assigned_request_groups(vehicles_schedule))), 1)
    # random_request_groups = select_most_costly_request_groups(network, vehicles_schedule, request_groups_to_select)
    random_request_groups = select_random_request_groups(vehicles_schedule, nb_request_groups_to_select)
    print(random_request_groups)

    for request_group in random_request_groups:
        original_score = round(calc_request_group_opportunity_cost(network, vehicles_schedule, request_group), 2)
        temp_schedule = copy.deepcopy(vehicles_schedule)
        remove_request_group(network, temp_schedule, request_group)

        positions = []
        assigned_so_far = []
        while len(assigned_so_far) != len(request_group):
            portion_to_add = [r for r in request_group if r not in assigned_so_far]
            candidate_vehicle, candidate_node, \
            score, added_portion = find_first_best_improvement_for_request_group_2(network, temp_schedule,
                                                                                   portion_to_add, original_score=original_score,
                                                                                    capacity=capacity, depot=depot)
            insert_request_group(network, temp_schedule, temp_request_dict, portion_to_add,
                                 candidate_vehicle, candidate_node, ignore_request_dict=True, capacity=capacity, depot=depot)
            positions.append((added_portion, candidate_vehicle, candidate_node, score))
            assigned_so_far += added_portion
            if candidate_node != 'current pos':
                original_score -= calc_request_group_opportunity_cost(network, temp_schedule, added_portion)

        if all([candidate[2] != 'current pos' for candidate in positions]):
            vehicles_schedule = temp_schedule

    return vehicles_schedule


def shuffle(network, vehicles_schedule, temp_request_dict=None, shuffle_rate=shuffle_ratio, capacity=20, depot='terminal'):
    """
    Function which shakes a vehicles_schedule schedule by a large amount. The shaking process goes as follows:
    - First, a random amount of request groups are selected amounting to the portion 'shuffle_rate' of the vehicles_schedule.
    - Then, these are inserted in the first best improving position, that is a position with a lower opportunity cost.
    """

    if not temp_request_dict:
        temp_request_dict = dict()

    request_groups_to_select = int(round(shuffle_rate * count_assigned_request_groups(vehicles_schedule)))
    random_request_groups = select_random_request_groups(vehicles_schedule, request_groups_to_select)

    for request_group in random_request_groups:
        original_score = round(calc_request_group_opportunity_cost(network, vehicles_schedule, request_group), 2)
        temp_schedule = copy.deepcopy(vehicles_schedule)
        remove_request_group(network, temp_schedule, request_group)

        positions = []
        assigned_so_far = []
        while len(assigned_so_far) != len(request_group):
            portion_to_add = [r for r in request_group if r not in assigned_so_far]
            candidate_vehicle, candidate_node, \
            score, added_portion = find_first_best_improvement_for_request_group_2(network, temp_schedule,
                                                                                   portion_to_add, original_score=original_score,
                                                                                    capacity=capacity, depot=depot)
            insert_request_group(network, temp_schedule, temp_request_dict, portion_to_add,
                                 candidate_vehicle, candidate_node, ignore_request_dict=True, capacity=capacity, depot=depot)
            positions.append((added_portion, candidate_vehicle, candidate_node, score))
            assigned_so_far += added_portion

            if len(added_portion) == 0:
                print('added portion: ', added_portion)
                print('assigned so far', assigned_so_far)
                print('request group: ', request_group)
                print('veh. schedule: ', temp_schedule)

            if candidate_node != 'current pos':
                original_score -= calc_request_group_opportunity_cost(network, temp_schedule, added_portion)

        if all([candidate[2] != 'current pos' for candidate in positions]):
            vehicles_schedule = temp_schedule

    return vehicles_schedule


def generate_dynamic_solution(network, vehicles_schedule, dynamic_requests, lead_time, peak_hour_duration,
                              temp_request_dict=None, capacity=20, depot='terminal'):
    """
    Lead time should be at least 1! That corresponds to ZLT in this case. A dynamic optimization is integrated in the
    algorithm as well.
    """

    cost_matrix = generate_cost_matrix(network, v_mean)
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
                                                                                                      current_time,
                                                                                                      cost_matrix)
                    insert_request_group(network, vehicles_schedule, temp_request_dict, request, candidate_vehicle,
                                         candidate_node, capacity=capacity, depot=depot)
        if current_time % delta == 0:
            print('initiate dynamic optimization...')
            vehicles_schedule = dynamic_optimization(vehicles_schedule, current_time, cost_matrix)

        current_time += 1

    return vehicles_schedule


def dynamic_optimization(network, vehicles_schedule, current_time, required_requests_per_it=1, time_limit=0.2,
                         temp_request_dict=None, capacity=20, depot='terminal'):
    """
    An alteration on the static optimization which takes into account the locking point, that is, only that
    request_group of vehicles schedule beyond the 'current_time' can be dealt with. That is:
    - Only requests at a stop with departure time beyond 'current_time' can be removed
    - And they can only be reinserted in spots with a departure time beyond 'current_time'
    """
    cost_matrix = generate_cost_matrix(network, v_mean)

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

        most_costly_requests = select_most_costly_request_groups(network, temp_schedule, required_requests_per_it,
                                                                 current_time=current_time)

        print('current iteration: ', it, 'obj. func: ', get_objective_function_val(temp_schedule))
        for request_group in most_costly_requests:
            remove_request_group(network, temp_schedule, request_group)
            temp_request_dict = add_request_group_to_dict(request_group, temp_request_dict)

        while count_requests(temp_request_dict) != 0:
            request_group = pop_request_group(temp_request_dict, set_seed=False)
            candidate_vehicle, candidate_node, score = find_best_position_for_dynamic_request(temp_schedule,
                                                                                              request_group,
                                                                                              current_time, cost_matrix=cost_matrix)
            insert_request_group(network, temp_schedule, temp_request_dict,
                                 request_group, candidate_vehicle, candidate_node, capacity=capacity, depot=depot)

        difference = get_objective_function_val(temp_schedule) - get_objective_function_val(vehicles_schedule)

        if difference < 0:
            print('new improvement found: ', get_objective_function_val(temp_schedule))
            vehicles_schedule = deepcopy(temp_schedule)
        else:
            print('returning best found vehicles_schedule: ', get_objective_function_val(best_schedule_so_far))
            return best_schedule_so_far

        end_time = time.time()
        elapsed_time += end_time - start_time
        it += 1

    print('returning best found vehicles_schedule: ', get_objective_function_val(best_schedule_so_far))
    return best_schedule_so_far
