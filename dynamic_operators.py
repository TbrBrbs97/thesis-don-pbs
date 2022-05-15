from requests import collect_request_until_time, get_od_from_request_group
from vehicle import get_insertion_possibilities, get_departure_time_at_node, get_prev_node, get_next_node
from network_generation import cv
from static_operators import find_pos_cost_given_ins_cons


def filter_dynamic_insertion_possibilities(vehicles_schedule, vehicle, request, insertion_constraints, current_time, cost_matrix):
    """
    A function that narrows down the insertions constraints, based on the current real time ('current_time'). As such,
    the 'locking point' principle is applied, which dictates that a request can ONLY be inserted in 'vehicle' at a point
    which lies beyond the visited stop at that time.

    So e.g., if a request ((3,2), 45.0, 39) has an issue time of 34, and the vehicle schedule looks like the following:
    1: {'1,0': [0.0, [...]], '3,1': [5.0, [...]], ... '3,10', [25.0: [...]], '3,9', [37.0, [...]], ...

    Then, the request can only be inserted after node '3,9'.
    """
    filtered_insertion_constraints = []
    o, d = get_od_from_request_group(request)

    for ins_cons in insertion_constraints:
        if ins_cons[0] == 'on arc with o: ' and \
                get_departure_time_at_node(vehicles_schedule, vehicle, ins_cons[1]) > current_time:
            filtered_insertion_constraints.append(ins_cons)
        elif ins_cons[1] == 'insert d after' and get_departure_time_at_node(vehicles_schedule,
                                                                            vehicle, ins_cons[1]) > current_time:
            filtered_insertion_constraints.append(ins_cons)
        elif ins_cons[1] == 'insert o after' and get_departure_time_at_node(vehicles_schedule,
                                                                            vehicle, ins_cons[1]) > current_time:
            filtered_insertion_constraints.append(ins_cons)
        elif ins_cons[1] == 'insert o before' and \
                (get_departure_time_at_node(vehicles_schedule, vehicle, ins_cons[1]) - cost_matrix[(o, d)]) > current_time:
            filtered_insertion_constraints.append(ins_cons)
        elif ins_cons == 'in front':
            first_node = get_prev_node(vehicles_schedule, vehicle)
            time_constraint = get_departure_time_at_node(vehicles_schedule, vehicle, first_node) \
                              - cost_matrix[(o, d)] - cost_matrix[(cv(first_node), d)]
            if time_constraint > current_time:
                filtered_insertion_constraints.append(ins_cons)
        elif ins_cons == 'back':
            last_node = get_next_node(vehicles_schedule, vehicle)
            time_constraint = get_departure_time_at_node(vehicles_schedule, vehicle, last_node) \
                              + cost_matrix[(cv(last_node), o)]
            if time_constraint > current_time:
                filtered_insertion_constraints.append(ins_cons)

    return filtered_insertion_constraints


def find_best_position_for_dynamic_request(vehicles_schedule, request, current_time, cost_matrix, current_vehicle=1,
                                           best_pos_so_far=None):
    """
    Finds the best position for a request group, taking the locking point condition into account as well.
    """
    if current_vehicle > len(list(vehicles_schedule)):
        return best_pos_so_far

    insertion_constraints = get_insertion_possibilities(vehicles_schedule, current_vehicle, request)
    filtered_insertion_constraints = filter_dynamic_insertion_possibilities(vehicles_schedule, current_vehicle,
                                                                            request, insertion_constraints,
                                                                            current_time, cost_matrix)

    for ins_con in filtered_insertion_constraints:
        matching_score = find_pos_cost_given_ins_cons(vehicles_schedule, current_vehicle, request, ins_con)
        if not best_pos_so_far or min(best_pos_so_far[2], matching_score) == matching_score:
            best_pos_so_far = current_vehicle, ins_con, round(matching_score, 2)

    current_vehicle += 1
    return find_best_position_for_dynamic_request(vehicles_schedule, request, current_time, cost_matrix, current_vehicle, best_pos_so_far)
