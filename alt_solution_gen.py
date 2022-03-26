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
        candidate_position = find_best_position_for_request_group(vehicles_schedule, request_group)
        # insert the request group in the candidate postion
        # remove the request group from the request dictionairy
        # return alt_create_initial_solution(requests_dict, current_service, nb_of_available_veh, vehicles_schedule)


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


def find_best_position_for_request_group(vehicles_schedule, request_group, current_vehicle=1, best_pos_so_far=None):
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

    if best_pos_so_far is None:
        best_pos_so_far = 1

    o, d = get_od_from_request_group(request_group)
    request_group_max_pt = get_max_pick_time(request_group)

    if current_vehicle > nb_of_required_ser:
        return vehicles_schedule

    if arc_in_vehicle(vehicles_schedule, current_vehicle, (o, d)) == (o, d):
            # room_for_insertion_at_node(vehicle_schedule, current_vehicle, (o, d)) > 0:
        matching_score = find_best_position_within_vehicle(vehicles_schedule, request_group, (o,d), current_vehicle)
        if max(best_pos_so_far[1], matching_score) == matching_score:
            best_pos_so_far = current_vehicle, matching_score
        # matching score is on the basis of the dep_time difference with the origin in this case

    if arc_in_vehicle(vehicles_schedule, current_vehicle, (o, d)) == o:
        matching_score = find_best_position_within_vehicle(vehicles_schedule, request_group, o, current_vehicle)
        if max(best_pos_so_far[1], matching_score) == matching_score:
            best_pos_so_far = current_vehicle, matching_score

    if arc_in_vehicle(vehicles_schedule, current_vehicle, (o, d)) == d:
        matching_score = find_best_position_within_vehicle(vehicles_schedule, request_group, d, current_vehicle)
        if max(best_pos_so_far[1], matching_score) == matching_score:
            best_pos_so_far = current_vehicle, matching_score

    else: # in all other cases, you position the request group either in front of existing chain / behind it


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
        return find_best_position_for_request_group(vehicles_schedule, request_group, current_vehicle, best_pos_so_far)


def find_best_position_within_vehicle(vehicles_schedule, request_group, portion_matching_od, vehicle):
    '''
    Returns how a vehicles scores for accommodating a request group: this is based
    on the difference between the departure time at a stop and the max pickup time of a request group.

    >> check for capacity on this level!

    Why not check for all possibilities? > i.e. not make it dependent whether or not o,d is (partly) matching in the schedule
    '''

    matching_score = 0
    o, d = get_od_from_request_group(request_group)
    request_group_max_pt = get_max_pick_time(request_group)

    if portion_matching_od == (o, d):
        # the function below will return the origin in the case of the arc o,d to be present
        occ_of_node = get_all_occurrences_of_node(vehicles_schedule, vehicle, portion_matching_od)
        best_matching_pos = calc_best_matching_position(vehicles_schedule, vehicle, request_group_max_pt, (o, d), occ_of_node, portion_matching_od)
    elif portion_matching_od == o:
        occ_of_node = get_all_occurrences_of_node(vehicles_schedule, vehicle, portion_matching_od)
        best_matching_pos = calc_best_matching_position(vehicles_schedule, vehicle, request_group_max_pt, o, occ_of_node, portion_matching_od)
    elif portion_matching_od == d:
        return None
    else: # check for the 'nearest stop' to either O or D
        return None


def get_prev_node(vehicles_schedule, vehicle, node):
    nodes_in_vehicle = get_existing_nodes(vehicles_schedule, vehicle)
    index_of_node = nodes_in_vehicle.index(node)
    if index_of_node > 0:
        return nodes_in_vehicle[index_of_node - 1]
    else:
        return None


def get_next_node(vehicles_schedule, vehicle, node):
    nodes_in_vehicle = get_existing_nodes(vehicles_schedule, vehicle)
    index_of_node = nodes_in_vehicle.index(node)
    if index_of_node < len(nodes_in_vehicle):
        return nodes_in_vehicle[index_of_node + 1]
    else:
        return None


def calc_best_matching_position(vehicles_schedule, vehicle, max_pt_rg, od_rg, occurrences, portion_matching_od):
    '''
    Given that there are multiple occurences of a node (e.g. ['2,0', '2,1', ...])
    '''
    # best_matching_node = previous_node, next_node, matching_score
    best_matching_position = None

    # if both the origin & dest. can be found as an arc, or if only the origin can be found as an arc
    if portion_matching_od == od_rg or portion_matching_od == od_rg[0]:
        for node in occurrences:
            dep_time = get_departure_time_at_node(vehicles_schedule, vehicle, node)
            delta_dep_time = abs(dep_time - max_pt_rg)

            if best_matching_position is None or delta_dep_time < best_matching_position[1]\
                    and room_for_insertion_at_node(vehicles_schedule, vehicle, node) > 0:
                best_matching_position = node, delta_dep_time
    # if only the destionation can be found as an arc
    elif portion_matching_od == od_rg[1]:
        for node in occurrences:
            prev_node = get_prev_node(vehicles_schedule, vehicle, node)
            if prev_node:
                dep_time = get_departure_time_at_node(vehicles_schedule, vehicle, prev_node)
                delta_dep_time = abs(dep_time - max_pt_rg)

                if best_matching_position is None or delta_dep_time < best_matching_position[1] \
                        and room_for_insertion_at_node(vehicles_schedule, vehicle, node) > 0:
                    best_matching_position = prev_node, delta_dep_time
            else: # meaning that if the destination happens to be the first stop in the schedule
                dep_time = get_departure_time_at_node(vehicles_schedule, vehicle, node)
                delta_dep_time = abs(dep_time - max_pt_rg)

                if best_matching_position is None or delta_dep_time < best_matching_position[1] \
                        and room_for_insertion_at_node(vehicles_schedule, vehicle, node) > 0:
                    best_matching_position = prev_node, delta_dep_time

    return best_matching_position


def arc_in_vehicle(vehicles_schedule, current_vehicle, od_tup):
    '''
    Returns the portion of the arc of 'od_tup' that is in the vehicle (i.e. the portion_matching_od),
    as well as the number of times this portions appears in the vehicle
    '''
    o, d = od_tup

    if any([int(node[0]) == o for node in vehicles_schedule[current_vehicle]]) and \
            any([int(node[0]) == d for node in vehicles_schedule[current_vehicle]]):
        return o, d
    elif any([int(node[0]) == o for node in vehicles_schedule[current_vehicle]]):
        return o
    elif any([int(node[0]) == d for node in vehicles_schedule[current_vehicle]]):
        return d
    else:
        return False


def get_existing_arcs(vehicles_schedule, vehicle):
    '''
    Function that returns a list of the already present arcs in the vehicle schedule, created
    by the pick-up and drop-off of passengers.
    '''

    nodes = list(vehicles_schedule[vehicle].keys())
    return [(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)]


def get_existing_nodes(vehicles_schedule, vehicle):
    '''
    Function that returns the list of existing nodes/stops in a vehicle schedule.
    '''
    return list(vehicles_schedule[vehicle])


def get_all_occurrences_of_node(vehicles_schedule, service, portion_of_od_in_sched):
    '''
    Function that returns a list of all occurences of a certain stop
    in the schedule of a vehicle. We only need to know if either the origin or the destination is within the vehicle.
    '''

    if portion_of_od_in_sched is tuple:
        return [n for n in vehicles_schedule[service] if int(n[0]) == portion_of_od_in_sched[0]]
    else:
        return [n for n in vehicles_schedule[service] if int(n[0]) == portion_of_od_in_sched]


def room_for_insertion_at_node(vehicles_schedule, vehicle, node):
    '''
    Returns the available capacity for insertion at a node 'node'. The function essentially diminishes the capacity
    per vehicle (which is a parameter) with the amount of request which obey the following criteria:
    1) The requests already boarding the vehicle at 'node';
    2) The requests boarding at any node before 'node', and also having a drop-off node after 'node'.

    '''

    pax_boarding_at_current_stop = sum([len(request_group) for request_group in vehicles_schedule[vehicle][node][1:]])
    pax_from_prev_stops = count_transit_pax_over_node(vehicles_schedule, vehicle, node)

    return cap_per_veh - (pax_boarding_at_current_stop + pax_from_prev_stops)


def count_transit_pax_over_node(vehicles_schedule, vehicle, node):
    '''
    Function that counts the nb of passengers who enter the vehicle before 'node',
    and remain in the vehicle until after 'node'.
    '''
    all_nodes = get_existing_nodes(vehicles_schedule, vehicle)
    index_curr_node = all_nodes.index(node)
    all_previous_nodes = all_nodes[:index_curr_node]

    transit_pax = 0

    for node in all_previous_nodes:
        # TODO
        # this will not work! in the case there are multiple instances of the destination >> you have to know where people get off
        # >> maybe build a dictionairy with keys = request, value = [vehicle, pick-up node, dep_time, drop_off node, arr_time]
        # this will probably also be easier to refer to later! >> and calculate IVT & WT for later
        transit_pax += sum([len(request_group) for request_group in vehicles_schedule[vehicle][node][1:] if get_max_pick_time(request_group)])

    return transit_pax


def get_departure_time_at_node(vehicles_schedule, vehicle, node):
    return vehicles_schedule[vehicle][node][0]


def insert_stop_in_vehicle(vehicle_schedule, vehicle, new_stop, previous_stop = None, next_stop = None):
    '''
    Function that alters the vehicles_schedule with sorted keys, depending on where you want to insert
    a stop. Either previous_stop or next_stop should be defined, e.g. previous_stop can be '3, 0', but
    next_stop == None, then we know we can add the new stop.

    Takes into account that if a stop is already in the schedule, then it adds a new number

    see: https://stackoverflow.com/questions/44390818/how-to-insert-key-value-pair-into-dictionary-at-a-specified-position
    '''
    return None


def insert_request_group(vehicles_schedule, request_group, vehicle, position):
    return None




