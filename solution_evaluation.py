from vehicle import locate_request_group_in_schedule, get_departure_time_at_node, get_next_occ_of_node, boarding_pass_at_node
from requests import get_od_from_request_group


def calc_request_group_waiting_time(vehicles_schedule, request_group):
    vehicle, node = locate_request_group_in_schedule(vehicles_schedule, request_group)
    departure_time = get_departure_time_at_node(vehicles_schedule, vehicle, node)
    waiting_time = sum([departure_time - request[1] for request in request_group])

    return waiting_time


def calc_request_group_invehicle_time(vehicles_schedule, request_group):
    o, d = get_od_from_request_group(request_group)

    vehicle, node = locate_request_group_in_schedule(vehicles_schedule, request_group)
    departure_time = get_departure_time_at_node(vehicles_schedule, vehicle, node)
    arrival_node = get_next_occ_of_node(vehicles_schedule, vehicle, node, d)
    arrival_time = get_departure_time_at_node(vehicles_schedule, vehicle, arrival_node)

    in_vehicle_time = (arrival_time - departure_time)*len(request_group)

    return in_vehicle_time


def generate_waiting_time_dict(vehicles_schedule):
    waiting_time_dict = {}

    for vehicle in vehicles_schedule:
        waiting_time_dict[vehicle] = {}
        for node in vehicles_schedule[vehicle]:
            waiting_time_dict[vehicle][node] = []
            for request_group in vehicles_schedule[vehicle][node][1:]:
                if boarding_pass_at_node(vehicles_schedule, vehicle, node):
                    waiting_time_dict[vehicle][node].\
                        append(calc_request_group_waiting_time(vehicles_schedule, request_group))

    return waiting_time_dict


def generate_in_vehicle_time_dict(vehicles_schedule):
    in_vehicle_time_dict = {}

    for vehicle in vehicles_schedule:
        in_vehicle_time_dict[vehicle] = {}
        for node in vehicles_schedule[vehicle]:
            in_vehicle_time_dict[vehicle][node] = []
            for request_group in vehicles_schedule[vehicle][node][1:]:
                if boarding_pass_at_node(vehicles_schedule, vehicle, node):
                    in_vehicle_time_dict[vehicle][node].\
                        append(calc_request_group_invehicle_time(vehicles_schedule, request_group))

    return in_vehicle_time_dict


def generate_total_travel_time_dict(in_vehicle_time_dict, waiting_time_dict):
    total_travel_time_dict = {}

    for vehicle in in_vehicle_time_dict:
        total_travel_time_dict[vehicle] = {}
        for node in in_vehicle_time_dict[vehicle]:
            total_travel_time_dict[vehicle][node] = list(range(len(in_vehicle_time_dict[vehicle][node])))
            for t in range(len(in_vehicle_time_dict[vehicle][node])):
                if len(in_vehicle_time_dict[vehicle][node]) != 0 and len(waiting_time_dict[vehicle][node]) != 0:
                    total_travel_time_dict[vehicle][node][t] = in_vehicle_time_dict[vehicle][node][t] + \
                                                               waiting_time_dict[vehicle][node][t]

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


def get_objective_function_val(vehicles_schedule):
    in_vehicle_time_dict = generate_in_vehicle_time_dict(vehicles_schedule)
    waiting_time_dict = generate_waiting_time_dict(vehicles_schedule)
    total_travel_time = generate_total_travel_time_dict(in_vehicle_time_dict, waiting_time_dict)

    return round(sum_total_travel_time(total_travel_time, 'total'), 2)


def calc_occupancy_rate(solution, capacity):
    # [1:] slice: because the departure time should not be counted!
    return {v: {s: len([j for i in solution[v][s][1:] for j in i])/capacity for s in solution[v]} for v in solution}


### TEST FUNCTIONS:

# fucntion that asserts that no vehicle goes over its capacity at no stop
# function that asserts that departure time goes up!

