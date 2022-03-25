import random
import copy

from requests_generation import count_requests, get_od_from_request_group, get_max_pick_time
from solution_generation import available_capacity

from parameters import network_dim, cap_per_veh, cost_matrix, nb_of_required_ser


def generate_initial_solution(requests_dict, current_service, nb_of_available_veh,
                                vehicles_schedule=None):
    '''
    An alternative version to the initial solution build, which does not
    assume fixed vehicle schedules.
    '''

    if count_requests(requests_dict) == 0 and current_service < nb_of_available_veh:
        return vehicles_schedule
    else:
        request_group = pop_request(requests_dict)
        o, d = get_od_from_request_group(request_group)
        pt = get_max_pick_time(request_group)

    if vehicles_schedule is None:
        vehicles_schedule = init_fill_every_vehicle(requests_dict, nb_of_available_veh)

    else:
        candidate_vehicle = find_best_vehicle_for_request_group(vehicles_schedule, request_group)
        best_position_within_veh = find_best_position_within_vehicle(vehicles_schedule, request_group, candidate_vehicle)


        # try to insert a request in the current position (find_closest_match?)
        # make this a seperate function

    # recursive part
    # remove the request group from the request dictionairy
    # return alt_create_initial_solution(requests_dict, current_service, nb_of_available_veh, vehicles_schedule)

# if no spot in the current veh, or current veh > max_tour_length:
    # return solution with new vehicle


def init_fill_every_vehicle(request_dict, nb_of_available_veh, seed=True):
    '''
    Function that fills every vehicle with a request group to start.
    Standard, node ids are multiplied with a 1000 in order to accomodate
    earlier occurences & later occurences of stops in a schedule
    ( respectively then /10 or *10 for the next occurence)
    '''
    vehicles_schedule = dict()

    for v in range(1, nb_of_available_veh+1):
        if seed is True:
            random.seed(1)

        request_group = pop_request(request_dict)
        o, d = get_od_from_request_group(request_group)
        pt = get_max_pick_time(request_group)

        vehicles_schedule[v] = dict()
        vehicles_schedule[v][str(o)+',0'] = [pt, request_group]
        vehicles_schedule[v][str(d)+',0'] = [pt + cost_matrix[(o, d)]]

        request_dict[(o, d)].remove(request_group)

    return vehicles_schedule


def pop_request(request_dictionairy):
    '''
    Function that returns a random request group from the request dictionairy
    '''

    random_od_pair = random.choice(list(request_dictionairy))
    while count_requests(request_dictionairy, random_od_pair) == 0:
        random_od_pair = random.choice(list(request_dictionairy))

    return random.choice(request_dictionairy[random_od_pair])


def find_best_vehicle_for_request_group(vehicle_schedule, request_group, current_vehicle=1, best_vehicle_so_far=None):
    '''
    Function that returns the best possible position in the schedule for insertion,
    taking into account capacity constraints & the marginal cost of insertion
    (detour).

    TODO: make this a recursive function: call until start_vehicle = nb_of_vehicles
    TODO: evaluate waiting time & travel time incremement per case

    # TODO:
    # - First, you look for best vehicle - difference dep.time & pick-up OR closest stop
    # - Second, you find the exact position within the chosen vehicle

    '''
    if best_vehicle_so_far is None:
        best_vehicle_so_far = 1

    o, d = get_od_from_request_group(request_group)
    request_group_max_pt = get_max_pick_time(request_group)

    if current_vehicle > nb_of_required_ser:
        return vehicle_schedule

    if arc_in_vehicle(vehicle_schedule, current_vehicle, (o, d)) == (o, d) and \
            remaining_capacity(vehicle_schedule, current_vehicle, (o, d)) > 0:
        matching_score = calculate_matching_score(vehicle_schedule, current_vehicle, (o, d), request_group_max_pt)
        if max(best_vehicle_so_far[1], matching_score) == matching_score:
            best_vehicle_so_far = current_vehicle,  matching_score
        # matching score is on the basis of the dep_time difference with the origin in this case

    if arc_in_vehicle(vehicle_schedule, current_vehicle, (o, d)) == o and \
            remaining_capacity(vehicle_schedule, current_vehicle, o) > 0:
        matching_score = calculate_matching_score(vehicle_schedule, current_vehicle, o, request_group_max_pt)
        if max(best_vehicle_so_far[1], matching_score) == matching_score:
            best_vehicle_so_far = current_vehicle,  matching_score

    if arc_in_vehicle(vehicle_schedule, current_vehicle, (o, d)) == d and \
            remaining_capacity(vehicle_schedule, current_vehicle, d) > 0:
        matching_score = calculate_matching_score(vehicle_schedule, current_vehicle, d, request_group_max_pt)
        if max(best_vehicle_so_far[1], matching_score) == matching_score:
            best_vehicle_so_far = current_vehicle,  matching_score

    # if o in schedule + capacity left in between o and the next stop:
        # here
        # add the request group at o and make the vehicle detour via d, before going to the next
        # if solution is better:
            # best_insertion_so_far = vehicle, position, score (=dep_time_difference)
    # if d in schedule + capacity left in between the previous stop and d:
        # add the request between the previous stop and d and make detour via o
    # else: > if neither o or d are in the schedule
        # if the dep time at o < the dep at the starting stop + driving time, add it before
        # in the case o > dep_t at the last stop + driving time, chain the arc in the end

    current_vehicle += 1
    return find_best_vehicle_for_request_group(vehicle_schedule, request_group, current_vehicle, best_vehicle_so_far)


def arc_in_vehicle(vehicle_schedule, current_vehicle, od_tup):
    '''
    Returns the portion of the arc of 'od_tup' that is in the vehicle, as well as the number of times
    this portions appears in the vehicle
    '''
    o, d = od_tup

    if any([int(node[0]) == o for node in vehicle_schedule[current_vehicle]]) and \
            any([int(node[0]) == d for node in vehicle_schedule[current_vehicle]]):
        return o, d  #, len([int(node_o[0]) == o and int(node_d[0]) == d for node_o in vehicle_schedule[current_vehicle] for node_d in vehicle_schedule[current_vehicle]])
    elif any([int(node[0]) == o for node in vehicle_schedule[current_vehicle]]):
        return o  #, len([int(node[0]) == o for node in vehicle_schedule[current_vehicle]])
    elif any([int(node[0]) == d for node in vehicle_schedule[current_vehicle]]):
        return d  #, len([int(node[0]) == d for node in vehicle_schedule[current_vehicle]])
    else:
        return False


def find_best_position_within_vehicle(vehicle_schedule, request_group, vehicle):
    return None


def insert_request_group(vehicles_schedule, request_group, vehicle, position):
    return None


def get_existing_arcs(vehicles_schedule, service):
    '''
    Function that returns a list of the already present arcs in the vehicle schedule, created
    by the pick-up and drop-off of passengers.
    '''

    nodes = list(vehicles_schedule[service].keys())
    return [(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)]


def get_all_occurences_of_node(vehicles_schedule, service, portion_of_od_in_sched):
    '''
    Function that returns a list of all occurences of a certain stop
    in the schedule of a vehicle
    '''
    if not portion_of_od_in_sched is tuple:
        return [n for n in vehicles_schedule[service] if int(n[0]) == portion_of_od_in_sched]
    else:
        # otherwise we want to know how often the origin is in the schedule
        return [n for n in vehicles_schedule[service] if int(n[0]) == portion_of_od_in_sched[0]]


def remaining_capacity(vehicles_schedule, vehicle, arc):
    '''
    Returns the available capacity on a given arc,
    taken into account the number of available seates parameter
    '''
    # this is defined on a link-basis between two nodes (e.g. between 1 and 2)
    # The occupied load between o and d are all passengers with origin: 1 and destination != 1
    occupied_spots = set(())

    # check for all stops beyond the starting position until the ending
    for a in range(arc[0], arc[1]):
        if len(vehicles_schedule[vehicle][a]) != 0:
            x = {j for i in vehicles_schedule[vehicle][a][1:] for j in i}
            occupied_spots = occupied_spots.union(x)

    return cap_per_veh - len(occupied_spots)


def get_departure_time(vehicles_schedule, vehicle, node):
    return vehicles_schedule[vehicle][node][0]


def insert_stop_in_vehicle(vehicle_schedule, vehicle, new_stop, previous_stop = None, next_stop = None):
    '''
    Function that alters the vehicles_schedule with sorted keys, depending on where you want to insert
    a stop. Either previous_stop or next_stop should be defined, e.g. previous_stop can be '3, 0', but
    next_stop == None, then we know we can add the new stop.

    Takes into account that if a stop is already in the schedule, then it adds a new number

    see: https://stackoverflow.com/questions/44390818/how-to-insert-key-value-pair-into-dictionary-at-a-specified-position
    '''


def calculate_matching_score(vehicles_schedule, vehicle, request_group, portion_of_od_in_sched):
    '''
    Returns how a vehicles scores for accomodating a request group: this is based
    on the difference between the departure time at a stop and the max pickup time of a request group.
    '''

    matching_score = 0
    o, d = get_od_from_request_group(request_group)
    request_group_max_pt = get_max_pick_time(request_group)

    if type(portion_of_od_in_sched) == (o, d):
        occurences = get_all_occurences_of_node(vehicles_schedule, vehicle, portion_of_od_in_sched)
        best_matching_node = None
        for node in occurences:
            dep_time = get_departure_time(vehicles_schedule, vehicle, node)
            delta_dep_time = abs(dep_time - request_group_max_pt)
            if best_matching_node is None or delta_dep_time < best_matching_node[1]:
                best_matching_node = node, delta_dep_time

