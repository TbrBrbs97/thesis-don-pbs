from vehicle import locate_request_group_in_schedule, get_departure_time_at_node, get_next_occ_of_node, \
    boarding_pass_at_node, is_empty_vehicle_schedule, count_total_assigned_requests
from requests import get_od_from_request_group
from static_operators import remove_request_group
from network_generation import cv, generate_distance_matrix
from copy import deepcopy


def calc_request_group_waiting_time(vehicles_schedule, request_group, relative=False):
    if relative:
        denominator = len(request_group)
    else:
        denominator = 1

    waiting_time = 0

    if len(request_group) > 0:
        vehicle, node = locate_request_group_in_schedule(vehicles_schedule, request_group)
        departure_time = get_departure_time_at_node(vehicles_schedule, vehicle, node)
        waiting_time = round(sum([departure_time - request[1] for request in request_group])/denominator, 2)

    return waiting_time


def calc_request_group_opportunity_cost(network, vehicles_schedule, request_group):
    """
    Returns the opportunity cost of a request group; or the drop in objective function
    value due to removing a request group.
    """
    original_obj_func_val = get_objective_function_val(vehicles_schedule)
    schedule_copy = deepcopy(vehicles_schedule)
    remove_request_group(network, schedule_copy, request_group)
    opportunity_cost = original_obj_func_val - get_objective_function_val(schedule_copy)
    return opportunity_cost


def calc_request_group_invehicle_time(vehicles_schedule, request_group, relative=False):
    if relative:
        denominator = len(request_group)
    else:
        denominator = 1

    in_vehicle_time = 0

    if len(request_group) > 0:
        o, d = get_od_from_request_group(request_group)
        vehicle, node = locate_request_group_in_schedule(vehicles_schedule, request_group)

        departure_time = get_departure_time_at_node(vehicles_schedule, vehicle, node)
        arrival_node = get_next_occ_of_node(vehicles_schedule, vehicle, node, d)
        if arrival_node:
            arrival_time = get_departure_time_at_node(vehicles_schedule, vehicle, arrival_node)
            in_vehicle_time = round((arrival_time - departure_time)*len(request_group)/denominator, 2)

    return in_vehicle_time


def generate_waiting_time_dict(vehicles_schedule, relative=False, direction='all'):
    waiting_time_dict = {}

    if direction == 'all':
        for vehicle in vehicles_schedule:
            waiting_time_dict[vehicle] = {}
            for node in vehicles_schedule[vehicle]:
                waiting_time_dict[vehicle][node] = []
                for request_group in vehicles_schedule[vehicle][node][1:]:
                    if boarding_pass_at_node(vehicles_schedule, vehicle, node):
                        waiting_time_dict[vehicle][node].\
                            append(calc_request_group_waiting_time(vehicles_schedule, request_group, relative))
    elif direction == 'city':
        for vehicle in vehicles_schedule:
            waiting_time_dict[vehicle] = {}
            for node in vehicles_schedule[vehicle]:
                waiting_time_dict[vehicle][node] = []
                for request_group in vehicles_schedule[vehicle][node][1:]:
                    if boarding_pass_at_node(vehicles_schedule, vehicle, node):
                        o, d = get_od_from_request_group(request_group)
                        if o < d:
                            waiting_time_dict[vehicle][node].\
                                    append(calc_request_group_waiting_time(vehicles_schedule, request_group, relative))

    elif direction == 'terminal':
        for vehicle in vehicles_schedule:
            waiting_time_dict[vehicle] = {}
            for node in vehicles_schedule[vehicle]:
                waiting_time_dict[vehicle][node] = []
                for request_group in vehicles_schedule[vehicle][node][1:]:
                    if boarding_pass_at_node(vehicles_schedule, vehicle, node):
                        o, d = get_od_from_request_group(request_group)
                        if o > d:
                            waiting_time_dict[vehicle][node].\
                                    append(calc_request_group_waiting_time(vehicles_schedule, request_group, relative))

    return waiting_time_dict


def generate_in_vehicle_time_dict(vehicles_schedule, relative=False, direction='all'):
    in_vehicle_time_dict = {}

    if direction == 'all':
        for vehicle in vehicles_schedule:
            in_vehicle_time_dict[vehicle] = {}
            if not is_empty_vehicle_schedule(vehicles_schedule, vehicle):
                for node in vehicles_schedule[vehicle]:
                    in_vehicle_time_dict[vehicle][node] = []
                    for request_group in vehicles_schedule[vehicle][node][1:]:
                        if boarding_pass_at_node(vehicles_schedule, vehicle, node):
                            in_vehicle_time_dict[vehicle][node].\
                                append(calc_request_group_invehicle_time(vehicles_schedule, request_group, relative))
    elif direction == 'city':
        for vehicle in vehicles_schedule:
            in_vehicle_time_dict[vehicle] = {}
            if not is_empty_vehicle_schedule(vehicles_schedule, vehicle):
                for node in vehicles_schedule[vehicle]:
                    in_vehicle_time_dict[vehicle][node] = []
                    for request_group in vehicles_schedule[vehicle][node][1:]:
                        if boarding_pass_at_node(vehicles_schedule, vehicle, node):
                            o, d = get_od_from_request_group(request_group)
                            if o < d:
                                in_vehicle_time_dict[vehicle][node].\
                                    append(calc_request_group_invehicle_time(vehicles_schedule, request_group, relative))
    elif direction == 'terminal':
        for vehicle in vehicles_schedule:
            in_vehicle_time_dict[vehicle] = {}
            if not is_empty_vehicle_schedule(vehicles_schedule, vehicle):
                for node in vehicles_schedule[vehicle]:
                    in_vehicle_time_dict[vehicle][node] = []
                    for request_group in vehicles_schedule[vehicle][node][1:]:
                        if boarding_pass_at_node(vehicles_schedule, vehicle, node):
                            o, d = get_od_from_request_group(request_group)
                            if o > d:
                                in_vehicle_time_dict[vehicle][node].\
                                    append(calc_request_group_invehicle_time(vehicles_schedule, request_group, relative))

    return in_vehicle_time_dict


def generate_total_travel_time_dict(vehicles_schedule, relative=False, direction='all'):
    in_vehicle_time_dict = generate_in_vehicle_time_dict(vehicles_schedule, relative, direction)
    waiting_time_dict = generate_waiting_time_dict(vehicles_schedule, relative, direction)

    total_travel_time_dict = {}

    for vehicle in in_vehicle_time_dict:
        total_travel_time_dict[vehicle] = {}
        for node in in_vehicle_time_dict[vehicle]:
            total_travel_time_dict[vehicle][node] = list(range(len(in_vehicle_time_dict[vehicle][node])))
            for t in range(len(in_vehicle_time_dict[vehicle][node])):
                if len(in_vehicle_time_dict[vehicle][node]) != 0 and len(waiting_time_dict[vehicle][node]) != 0:
                    total_travel_time_dict[vehicle][node][t] = round(in_vehicle_time_dict[vehicle][node][t] +
                                                                     waiting_time_dict[vehicle][node][t], 2)

    return total_travel_time_dict


def sum_total_travel_time(total_travel_time_dict, level='total'):

    if level == 'stop':
        result = {v: {s: sum([r for r in total_travel_time_dict[v][s]]) for s in total_travel_time_dict[v]}
                  for v in total_travel_time_dict}
    elif level == 'vehicle':
        result = {v: sum([sum([r for r in total_travel_time_dict[v][s]]) for s in total_travel_time_dict[v]])
                  for v in total_travel_time_dict}
    elif level == 'total':
        result = sum([sum([sum([r for r in total_travel_time_dict[v][s]]) for s in total_travel_time_dict[v]])
                      for v in total_travel_time_dict])
    else:
        result = 0

    return result


def get_objective_function_val(vehicles_schedule, relative=False, direction='all'):
    if direction == 'all':
        total_travel_time = generate_total_travel_time_dict(vehicles_schedule, direction=direction)
        if relative is True:
            return round(sum_total_travel_time(total_travel_time, 'total') / count_total_assigned_requests(vehicles_schedule), 2)
        else:
            return round(sum_total_travel_time(total_travel_time, 'total'), 2)

    elif direction == 'city':
        total_travel_time = generate_total_travel_time_dict(vehicles_schedule, direction=direction)
        if relative is True:
            return round(sum_total_travel_time(total_travel_time, 'total') /
                         count_total_assigned_requests(vehicles_schedule, direction=direction), 2)
        else:
            return round(sum_total_travel_time(total_travel_time, 'total'), 2)

    elif direction == 'terminal':
        total_travel_time = generate_total_travel_time_dict(vehicles_schedule, direction=direction)
        if relative is True:
            return round(sum_total_travel_time(total_travel_time, 'total') /
                         count_total_assigned_requests(vehicles_schedule, direction=direction), 2)
        else:
            return round(sum_total_travel_time(total_travel_time, 'total'), 2)


def select_most_costly_request_groups(network, vehicles_schedule, required_amount=1, request_groups=None, current_time=None):
    """
    Returns a list of length 'required_amount' with the most costly request_groups.
    """
    if request_groups is None:
        request_groups = []

    if required_amount == 0:
        return request_groups

    most_costly_so_far = None
    original_obj_func_val = get_objective_function_val(vehicles_schedule)

    for vehicle in list(vehicles_schedule):
        for node in list(vehicles_schedule[vehicle]):
            if boarding_pass_at_node(vehicles_schedule, vehicle, node):
                if not current_time:
                    for request_group in vehicles_schedule[vehicle][node][1:]:
                        schedule_copy = deepcopy(vehicles_schedule)
                        remove_request_group(network, schedule_copy, request_group)
                        opportunity_cost = original_obj_func_val - get_objective_function_val(schedule_copy)
                        if (not most_costly_so_far or opportunity_cost > most_costly_so_far[1]) \
                                and request_group not in request_groups:
                            most_costly_so_far = request_group, opportunity_cost
                elif get_departure_time_at_node(vehicles_schedule, vehicle, node) > current_time:
                    for request_group in vehicles_schedule[vehicle][node][1:]:
                        schedule_copy = deepcopy(vehicles_schedule)
                        remove_request_group(network, schedule_copy, request_group)
                        opportunity_cost = original_obj_func_val - get_objective_function_val(schedule_copy)
                        if (not most_costly_so_far or opportunity_cost > most_costly_so_far[1]) \
                                and request_group not in request_groups:
                            most_costly_so_far = request_group, opportunity_cost

    request_groups.append(most_costly_so_far[0])
    required_amount -= 1
    return select_most_costly_request_groups(network, vehicles_schedule, required_amount, request_groups, current_time)


def calc_total_vehicle_kilometers(network, vehicles_schedule):
    """
    Calculates the total distance driven by all vehicles.
    """
    distance_matrix = generate_distance_matrix(network)

    total_vehicle_kilometres = 0
    for vehicle in vehicles_schedule:
        n = 0
        stops = list(vehicles_schedule[vehicle])
        while n < len(vehicles_schedule[vehicle])-1:
            total_vehicle_kilometres += distance_matrix[(cv(stops[n]), cv(stops[n+1]))]
            n += 1

    return round(total_vehicle_kilometres, 2)


def calc_occupancy_rate(vehicles_schedule, capacity):
    # [1:] slice: because the departure time should not be counted!
    return {vehicle: {node: len([j for i in vehicles_schedule[vehicle][node][1:] for j in i]) / capacity
                      for node in vehicles_schedule[vehicle] if boarding_pass_at_node(vehicles_schedule, vehicle, node)}
            for vehicle in vehicles_schedule}
