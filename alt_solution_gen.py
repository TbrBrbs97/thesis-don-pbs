import random
import numpy as np
import copy

from requests import count_requests, get_od_from_request_group, get_max_pick_time, \
    pop_request, remove_from_request_dictionairy
from vehicle import get_departure_time_at_node, get_insertion_possibilities, \
    get_existing_nodes, get_existing_arcs, get_prev_node, get_next_node, get_next_occ_of_node, get_vehicle_first_departure, \
    get_all_occurrences_of_node, room_for_insertion_at_node, boarding_pass_at_node, get_nodes_in_range, get_last_arrival

from parameters import cost_matrix, nb_of_required_ser, max_vehicle_ride_time, chaining_penalty


def generate_initial_solution(requests_dict, vehicles_schedule=None):
    """
    An alternative version to the initial solution build, which does not
    assume fixed vehicle schedules.
    """

    if vehicles_schedule is None:
        vehicles_schedule = init_fill_every_vehicle(requests_dict, nb_of_required_ser)

    if count_requests(requests_dict) == 0:
        return vehicles_schedule
    else:
        request_group = pop_request(requests_dict)

    candidate_position = find_best_position_for_request_group(vehicles_schedule, request_group)
    candidate_vehicle, candidate_pos_within_veh = candidate_position[0], candidate_position[1]

    insert_request_group2(vehicles_schedule, requests_dict, request_group, candidate_vehicle, candidate_pos_within_veh)
    return generate_initial_solution(requests_dict, vehicles_schedule)


def init_fill_every_vehicle(request_dict, nb_of_available_veh, seed=True):
    """
    Function that fills every vehicle with a request group to start.
    Standard, node ids are multiplied with a 1000 in order to accomodate
    earlier occurences & later occurences of stops in a schedule
    ( respectively then /10 or *10 for the next occurence)
    """
    vehicles_schedule = dict()

    for v in range(1, nb_of_available_veh+1):
        if seed is True:
            random.seed(1)

        request_group = pop_request(request_dict)
        remove_from_request_dictionairy(request_dict, request_group)

        o, d = get_od_from_request_group(request_group)
        pt = get_max_pick_time(request_group)

        vehicles_schedule[v] = dict()
        vehicles_schedule[v][str(o)+',0'] = [pt, request_group]
        vehicles_schedule[v][str(d)+',0'] = [pt + cost_matrix[(o, d)]]

    return vehicles_schedule


def find_best_position_for_request_group(vehicles_schedule, request_group, current_vehicle=1,
                                         best_pos_so_far=None, excluded_vehicles=None):
    """
    Function that returns the best possible position in the schedule for insertion,
    taking into account capacity constraints. In a recursive way, it tries to compare for every vehicle the respecitvely
    best costs for insertion. For whichever vehicle this representative cost is lowest, it is inserted in that vehicle,
    on that position.
    """

    if current_vehicle > nb_of_required_ser:
        return best_pos_so_far

    if not excluded_vehicles:
        excluded_vehicles = set()

    if current_vehicle in excluded_vehicles:
        current_vehicle += 1
        return find_best_position_for_request_group(vehicles_schedule, request_group,
                                                    current_vehicle, best_pos_so_far, excluded_vehicles)

    insertion_constraints = get_insertion_possibilities(vehicles_schedule, current_vehicle, request_group)

    for ins_con in insertion_constraints:
        matching_score = find_pos_cost_given_ins_cons(vehicles_schedule, current_vehicle, request_group, ins_con)
        if not best_pos_so_far or min(best_pos_so_far[2], matching_score) == matching_score:
            best_pos_so_far = current_vehicle, ins_con, round(matching_score, 2)

    current_vehicle += 1
    return find_best_position_for_request_group(vehicles_schedule, request_group, current_vehicle, best_pos_so_far)


def find_pos_cost_given_ins_cons(vehicles_schedule, vehicle, request_group, insertion_constraint=None):
    """
    Returns how a vehicles scores for accommodating a request group, GIVEN A INSERTION CONSTRAINT: this is based
    on the difference between the departure time at a stop and the max pickup time of a request group.

    On this level, the best possible postion is returned given a SINGLE 'insertion_constraint', which is given as an input.
    This constraint can either be:
    - 'insert d after', o: then, the request_group has to be inserted AFTER a node which fits the origin
    - 'insert o before', x': then, the origin is inserted in the schedule before a node x
    - 'on arc with o', o: then, the arc exists within the schedule and it might be inserted on this arc, starting at origin o
    - 'insert o after', x: then, the destination is within the schedule, and so the arc might be fitted RIGHT BEFORE d,
    and after a node x
    """

    request_group_max_pt = get_max_pick_time(request_group)
    o, d = get_od_from_request_group(request_group)
    # initialize at a very high cost
    detour_cost = 500
    dep_time_offset = 500

    # two subcases for 'insert d after', o : (1) the selected o is not the last node, (2) o is the last node
    if insertion_constraint[0] == 'insert d after' and \
            room_for_insertion_at_node(vehicles_schedule, vehicle, insertion_constraint[1]) > 0 and\
            get_next_node(vehicles_schedule, vehicle, insertion_constraint[1]):

        x = int(get_next_node(vehicles_schedule, vehicle, insertion_constraint[1])[0])

        detour_cost = cost_matrix[(o, d)] + cost_matrix[(d, x)] - cost_matrix[(o, x)]
        dep_time_offset = abs(request_group_max_pt - get_departure_time_at_node(vehicles_schedule,
                                                                                vehicle, insertion_constraint[1]))

    elif insertion_constraint[0] == 'insert d after' and \
            room_for_insertion_at_node(vehicles_schedule, vehicle, insertion_constraint[1]) > 0 and \
            not get_next_node(vehicles_schedule, vehicle, insertion_constraint[1]):

        detour_cost = 0
        dep_time_offset = abs(request_group_max_pt - get_departure_time_at_node(vehicles_schedule,
                                                                                vehicle, insertion_constraint[1]))

    # we don't have to check for capacity if it is the first node we're checking
    elif insertion_constraint[0] == 'insert o before':
        detour_cost = 0
        dep_time_offset = abs(get_departure_time_at_node(vehicles_schedule, vehicle, insertion_constraint[1])
                              - cost_matrix[o, d] - request_group_max_pt)

    elif insertion_constraint[0] == 'on arc with o: ' and \
            room_for_insertion_at_node(vehicles_schedule, vehicle, insertion_constraint[1],
                                       get_next_occ_of_node(vehicles_schedule, vehicle, insertion_constraint[1], d)) > 0:
        detour_cost = 0
        dep_time_offset = abs(get_departure_time_at_node(vehicles_schedule, vehicle, insertion_constraint[1])
                              - request_group_max_pt)

    elif insertion_constraint[0] == 'insert o after' and \
            room_for_insertion_at_node(vehicles_schedule, vehicle, insertion_constraint[1]) > 0:
        x = int(insertion_constraint[1][0])

        detour_cost = cost_matrix[(x, o)] + cost_matrix[(o, d)] - cost_matrix[(x, d)]
        dep_time_offset = abs(get_departure_time_at_node(vehicles_schedule, vehicle, insertion_constraint[1])
                              + cost_matrix[x, o] - request_group_max_pt)

    # we don't need to check for capacity in the following two cases
    elif insertion_constraint == 'in front':
        first_node = get_prev_node(vehicles_schedule, vehicle)
        detour_cost = chaining_penalty
        dep_time_offset = abs(get_departure_time_at_node(vehicles_schedule, vehicle, first_node) -
                              cost_matrix[(d, int(first_node[0]))] - request_group_max_pt + cost_matrix[(o, d)])

    elif insertion_constraint == 'back':
        last_node = get_next_node(vehicles_schedule, vehicle)
        detour_cost = 0
        dep_time_offset = abs(
            request_group_max_pt - get_departure_time_at_node(vehicles_schedule, vehicle, last_node))

    if get_last_arrival(vehicles_schedule, vehicle) > max_vehicle_ride_time:
        detour_cost = 500
        dep_time_offset = 500

    position_cost = detour_cost + dep_time_offset
    return position_cost


def insert_request_group(vehicles_schedule, requests_dict, request_group, vehicle, position, excluded_vehicles=None):
    """
    Inserts a request group in the specified vehicle and position within that vehicle (=start node and end node).
    The function calls an auxiliary function 'insert_stop_in_vehicle' whenever it is needed to insert a new stop.
    In all cases, the departure times at stops are corrected.
    """
    schedules_copy = copy.deepcopy(vehicles_schedule)
    requests_copy = copy.deepcopy(requests_dict)

    o, d = get_od_from_request_group(request_group)
    get_max_pick_time(request_group)
    node_to_insert_pax = None
    end_node = None

    if position[0] == 'insert d after':
        insert_stop_in_vehicle(schedules_copy, vehicle, node_type=d,
                               next_stop=get_next_node(schedules_copy, vehicle, position[1]))
        node_to_insert_pax = position[1]

    elif position[0] == 'insert o before':
        node_to_insert_pax = insert_stop_in_vehicle(schedules_copy, vehicle, node_type=o, next_stop=position[1])
    elif position[0] == 'on arc with o: ':
        node_to_insert_pax = position[1]
        end_node = get_next_occ_of_node(schedules_copy, vehicle, position[1], d)
    elif position[0] == 'insert o after':
        node_to_insert_pax = insert_stop_in_vehicle(schedules_copy, vehicle, node_type=o,
                                                    next_stop=get_next_node(schedules_copy, vehicle, position[1]))
    elif position == 'in front':
        node_to_insert_pax = insert_stop_in_vehicle(schedules_copy, vehicle, node_type=(o, d), next_stop='first stop')
    elif position == 'back':
        node_to_insert_pax = insert_stop_in_vehicle(schedules_copy, vehicle, node_type=(o, d))

    occupy_available_seats(schedules_copy, vehicle, requests_copy, request_group, node_to_insert_pax, end_node)
    update_dep_time_at_node(schedules_copy, vehicle, node_to_insert_pax)
    # update the departure time of all upcoming nodes
    for next_node in get_nodes_in_range(schedules_copy, vehicle, start_node=node_to_insert_pax):
        update_dep_time_at_node(schedules_copy, vehicle, next_node)

    if get_last_arrival(schedules_copy, vehicle) < max_vehicle_ride_time:
        vehicles_schedule = schedules_copy
        grouped_requests = requests_copy
        return vehicles_schedule, grouped_requests
    else:
        if excluded_vehicles is None:
            excluded_vehicles = set()
        excluded_vehicles.add(vehicle)
        position = find_best_position_for_request_group(vehicles_schedule, request_group,
                                                        current_vehicle=1, excluded_vehicles=excluded_vehicles)

        insert_request_group(vehicles_schedule, requests_dict, request_group, position[0], position[1], excluded_vehicles)


def insert_request_group2(vehicles_schedule, requests_dict, request_group, vehicle, position, excluded_vehicles=None):
    """
    Inserts a request group in the specified vehicle and position within that vehicle (=start node and end node).
    The function calls an auxiliary function 'insert_stop_in_vehicle' whenever it is needed to insert a new stop.
    In all cases, the departure times at stops are corrected.
    """
    # vehicles_schedule = copy.deepcopy(vehicles_schedule)
    # requests_dict = copy.deepcopy(requests_dict)

    o, d = get_od_from_request_group(request_group)
    get_max_pick_time(request_group)
    node_to_insert_pax = None
    end_node = None

    if position[0] == 'insert d after':
        insert_stop_in_vehicle(vehicles_schedule, vehicle, node_type=d,
                               next_stop=get_next_node(vehicles_schedule, vehicle, position[1]))
        node_to_insert_pax = position[1]

    elif position[0] == 'insert o before':
        node_to_insert_pax = insert_stop_in_vehicle(vehicles_schedule, vehicle, node_type=o, next_stop=position[1])
    elif position[0] == 'on arc with o: ':
        node_to_insert_pax = position[1]
        end_node = get_next_occ_of_node(vehicles_schedule, vehicle, position[1], d)
    elif position[0] == 'insert o after':
        node_to_insert_pax = insert_stop_in_vehicle(vehicles_schedule, vehicle, node_type=o,
                                                    next_stop=get_next_node(vehicles_schedule, vehicle, position[1]))
    elif position == 'in front':
        node_to_insert_pax = insert_stop_in_vehicle(vehicles_schedule, vehicle, node_type=(o, d), next_stop='first stop')
    elif position == 'back':
        node_to_insert_pax = insert_stop_in_vehicle(vehicles_schedule, vehicle, node_type=(o, d))

    occupy_available_seats(vehicles_schedule, vehicle, requests_dict, request_group, node_to_insert_pax, end_node)
    update_dep_time_at_node(vehicles_schedule, vehicle, node_to_insert_pax)
    # update the departure time of all upcoming nodes
    for next_node in get_nodes_in_range(vehicles_schedule, vehicle, start_node=node_to_insert_pax):
        update_dep_time_at_node(vehicles_schedule, vehicle, next_node)


def insert_stop_in_vehicle(vehicle_schedule, vehicle, node_type=None, next_stop=None):
    """
    Function that adds a new stop in the vehicle, in front of the 'next_stop' parameter. By default, if the node_type doesn't
    occur in the schedule already, the node is inserted as a key 'node_type, 0'. But if node_type already occurs, then this second
    element of the key is increased by 1. The value or content of the stop is initiated as an empty list.

    see: https://stackoverflow.com/questions/44390818/how-to-insert-key-value-pair-into-dictionary-at-a-specified-position
    """

    items = list(vehicle_schedule[vehicle].items())
    curr_occ = 0
    occ = dict()

    if type(node_type) is int:
        all_occ_of_node_type = get_all_occurrences_of_node(vehicle_schedule, vehicle, node_type)
        if len(all_occ_of_node_type) > 0:
            max_occ = max([int(t[-1]) for t in all_occ_of_node_type])
            curr_occ = max_occ + 1
    elif len(node_type) == 2:
        for n in node_type:
            all_occ_of_node_type = get_all_occurrences_of_node(vehicle_schedule, vehicle, n)
            occ[n] = 0
            if len(all_occ_of_node_type) > 0:
                max_occ = max([int(t[-1]) for t in all_occ_of_node_type])
                occ[n] = max_occ + 1

    if next_stop and next_stop != 'first stop':
        insert_before = list(vehicle_schedule[vehicle].keys()).index(next_stop)
        new_stop = str(node_type)+',' + str(curr_occ)
        items.insert(insert_before, (new_stop, [0.0]))
        vehicle_schedule[vehicle] = dict(items)

    elif next_stop == 'first stop':
        insert_before = list(vehicle_schedule[vehicle].keys()).index(get_prev_node(vehicle_schedule, vehicle))
        items.insert(insert_before, (str(node_type[1]) + ',' + str(occ[node_type[1]]), [0.0]))
        new_stop = str(node_type[0]) + ',' + str(occ[node_type[0]])
        items.insert(insert_before, (new_stop, [0.0]))
        vehicle_schedule[vehicle] = dict(items)

    elif not next_stop and type(node_type) == int:
        items = list(vehicle_schedule[vehicle].items())
        new_stop = str(node_type) + ',' + str(curr_occ)
        items.append((new_stop, [0.0]))
        vehicle_schedule[vehicle] = dict(items)

    else:
        items = list(vehicle_schedule[vehicle].items())
        new_stop = str(node_type[0]) + ',' + str(occ[node_type[0]])
        items.append((new_stop, [0.0]))
        items.append((str(node_type[1]) + ',' + str(occ[node_type[1]]), [0.0]))
        vehicle_schedule[vehicle] = dict(items)

    return new_stop


def occupy_available_seats(vehicles_schedule, vehicle, requests_dict, request_group, start_node, end_node=None):
    """
    Positions the available capacity within the vehicle. Part of the request group that can be added
    into the schedule is added and that same part is removed from the request dictionairy.
    The remaining part is kept in the request dictionairy.
    """

    if not start_node:
        return

    available_seats = room_for_insertion_at_node(vehicles_schedule, vehicle, start_node, end_node)
    portion_to_add = request_group[:min(available_seats, len(request_group))]

    # add portion to the schedule
    if not boarding_pass_at_node(vehicles_schedule, vehicle, start_node):
        vehicles_schedule[vehicle][start_node][0] = round(get_max_pick_time(portion_to_add), 2)
    vehicles_schedule[vehicle][start_node].append(portion_to_add)

    # remove it from request dictionairy
    o, d = get_od_from_request_group(request_group)
    idx_rq = requests_dict[(o, d)].index(request_group)
    if len(request_group[min(available_seats, len(request_group)):]) > 0:
        requests_dict[(o, d)][idx_rq] = request_group[min(available_seats, len(request_group)):]
    else:
        requests_dict[(o, d)].remove(requests_dict[(o, d)][idx_rq])


def update_dep_time_at_node(vehicles_schedule, vehicle, node):
    """
    Update the departure time of a vehicle at a certain stop.
    """
    imposed_dep_time_by_req_pt = 0

    if boarding_pass_at_node(vehicles_schedule, vehicle, node):
        imposed_dep_time_by_req_pt = max([get_max_pick_time(group) for group in vehicles_schedule[vehicle][node][1:]])

    previous_node = get_prev_node(vehicles_schedule, vehicle, node)
    if previous_node:
        previous_node_dep_time = get_departure_time_at_node(vehicles_schedule, vehicle, previous_node)
        imposed_dep_time_by_prev_stop = previous_node_dep_time + cost_matrix[(int(previous_node[0]), int(node[0]))]
    else:
        imposed_dep_time_by_prev_stop = np.float64()

    vehicles_schedule[vehicle][node][0] = round(max(imposed_dep_time_by_prev_stop, imposed_dep_time_by_req_pt), 2)

