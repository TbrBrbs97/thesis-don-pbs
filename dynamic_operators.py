from requests import collect_request_until_time, get_od_from_request_group
from vehicle import get_insertion_possibilities, get_departure_time_at_node, room_for_insertion_at_node
from parameters import nb_of_available_vehicles
from static_operators import find_pos_cost_given_ins_cons

def dynamic_insert(vehicles_schedule, dynamic_requests, request, vehicle, node):
    """
    Function that inserts the collected dynamic requests in the vehicles schedule.
    Removes request from the dynamic requests as well.
    """
    return None


def filter_dynamic_insertion_possibilities(vehicles_schedule, vehicle, insertion_constraints, current_time):
    """
    A function that narrows down the insertions constraints, based on the current real time ('current_time'). As such,
    the 'locking point' principle is applied, which dictates that a request can ONLY be inserted in 'vehicle' at a point
    which lies beyond the visited stop at that time.

    So e.g., if a request ((3,2), 45.0, 39) has an issue time of 34, and the vehicle schedule looks like the following:
    1: {'1,0': [0.0, [...]], '3,1': [5.0, [...]], ... '3,10', [25.0: [...]], '3,9', [37.0, [...]], ...

    Then, the request can only be inserted after node '3,9'.

    For now, we only allow to add these request, since they are singular, on existing arcs.
    """
    filtered_insertion_constraints = []

    for ins_cons in insertion_constraints:
        if ins_cons[0] == 'on arc with o: ' and \
                get_departure_time_at_node(vehicles_schedule, vehicle, ins_cons[1]) > current_time and \
                room_for_insertion_at_node(vehicles_schedule, vehicle, ins_cons[1]) >= 1:
            filtered_insertion_constraints.append(ins_cons)
        # if ins_cons[1] == 'insert d after':
            # finish this statement > you can add more of these, and see how expensive they become!

    return filtered_insertion_constraints


def find_best_position_for_dynamic_request(vehicles_schedule, request, current_time, current_vehicle=1,
                                           best_pos_so_far=None):
    """
    Finds the best position for a request group, taking the locking point condition into account as well.
    """
    if current_vehicle > nb_of_available_vehicles:
        return best_pos_so_far

    insertion_constraints = get_insertion_possibilities(vehicles_schedule, current_vehicle, request)
    filtered_insertion_constraints = filter_dynamic_insertion_possibilities(vehicles_schedule, current_vehicle,
                                                                            insertion_constraints, current_time)

    for ins_con in filtered_insertion_constraints:
        matching_score = find_pos_cost_given_ins_cons(vehicles_schedule, current_vehicle, request, ins_con)
        if not best_pos_so_far or min(best_pos_so_far[2], matching_score) == matching_score:
            best_pos_so_far = current_vehicle, ins_con, round(matching_score, 2)

    current_vehicle += 1
    return find_best_position_for_dynamic_request(vehicles_schedule, request, current_time, current_vehicle, best_pos_so_far)
