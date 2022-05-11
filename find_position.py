from parameters import nb_of_available_vehicles, M
from copy import deepcopy
from vehicle import get_insertion_possibilities, room_for_insertion_at_node, \
    get_next_occ_of_node, get_last_arrival, locate_request_group_in_schedule
from static_operators import find_pos_cost_given_ins_cons, \
    add_request_group_to_dict, insert_request_group, remove_request_group
from solution_evaluation import calc_request_group_opportunity_cost
from requests import count_requests, pop_request_group, get_od_from_request_group


def find_best_improvement_for_request_group(vehicles_schedule, request_group, original_score=M,
                                            current_vehicle=1, best_improvement=None):
    """Find the best improving position for a request group request_group, instead of looking for the best spot.
    This function allows only part of the request group given as input to be returned, but then it"""

    if current_vehicle > nb_of_available_vehicles:
        return best_improvement

    if not best_improvement:
        best_improvement = current_vehicle, 'current pos', round(original_score, 2), request_group

    temp_request_dict = dict()

    insertion_constraints = get_insertion_possibilities(vehicles_schedule, current_vehicle, request_group)

    for ins_cons in insertion_constraints:
        temp_schedule = deepcopy(vehicles_schedule)
        added_portion = insert_request_group(temp_schedule, temp_request_dict, request_group,
                                             current_vehicle, ins_cons, return_added_portion=True,
                                             ignore_request_dict=True)
        vehicle, node = locate_request_group_in_schedule(temp_schedule, added_portion)
        if len(added_portion) > 0:
            current_score = calc_request_group_opportunity_cost(temp_schedule, added_portion)
        elif get_last_arrival(temp_schedule, vehicle):
            current_score = M
        else: # heavily penalize insertions of empty added_portions
            current_score = 5*M

        if not best_improvement or current_score < best_improvement[2]:
            best_improvement = current_vehicle, ins_cons, round(current_score, 2), added_portion

    current_vehicle += 1
    return find_best_improvement_for_request_group(vehicles_schedule, request_group, original_score,
                                                   current_vehicle, best_improvement)


def find_first_best_improvement_for_request_group(vehicles_schedule, request_group, original_score=M, current_vehicle=1,
                                                  best_improvement=None):
    "Find the first best improving position for a request group, in stead of looking for the best spot"

    if current_vehicle > nb_of_available_vehicles:
        return best_improvement

    # original_score = calc_request_group_opportunity_cost(vehicles_schedule, request_group)

    insertion_constraints = get_insertion_possibilities(vehicles_schedule, current_vehicle, request_group)

    for ins_cons in insertion_constraints:
        current_score = find_pos_cost_given_ins_cons(vehicles_schedule, current_vehicle, request_group, ins_cons)
        if not best_improvement:
            best_improvement = current_vehicle, 'current pos', round(original_score, 2)
        elif current_score < best_improvement[2]:
            best_improvement = current_vehicle, ins_cons, round(current_score, 2)
            return best_improvement

    current_vehicle += 1
    return find_first_best_improvement_for_request_group(vehicles_schedule, request_group,
                                                         original_score, current_vehicle, best_improvement)


def find_first_best_improvement_for_request_group_2(vehicles_schedule, request_group, original_score=M,
                                                    current_vehicle=1, best_improvement=None):
    """Find the first best improving position for a request group request_group, instead of looking for the best spot.
    This function allows only part of the request group given as input to be returned, but then it"""
    # if request_group == [((12, 15), 6.08, 0), ((12, 15), 10.07, 0), ((12, 15), 19.39, 0)]:
    #     print(True)

    if current_vehicle > nb_of_available_vehicles:
        return best_improvement

    if not best_improvement:
        best_improvement = current_vehicle, 'current pos', round(original_score, 2), request_group

    temp_request_dict = dict()

    insertion_constraints = get_insertion_possibilities(vehicles_schedule, current_vehicle, request_group)

    for ins_cons in insertion_constraints:
        temp_schedule = deepcopy(vehicles_schedule)
        # temp_request_dict = add_request_group_to_dict(request_group, temp_request_dict)
        added_portion = insert_request_group(temp_schedule, temp_request_dict, request_group,
                                             current_vehicle, ins_cons, return_added_portion=True,
                                             ignore_request_dict=True)
        if len(added_portion) > 0:
            current_score = calc_request_group_opportunity_cost(temp_schedule, added_portion)
        else: # penalize insertions that have very high costs
            current_score = 5*M

        if current_score < best_improvement[2]:
            best_improvement = current_vehicle, ins_cons, round(current_score, 2), added_portion
            return best_improvement

    current_vehicle += 1
    return find_first_best_improvement_for_request_group_2(vehicles_schedule,
                                                           request_group, original_score, current_vehicle, best_improvement)