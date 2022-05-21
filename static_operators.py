import numpy as np
import random

from network_generation import cv, generate_cost_matrix, get_network_boundaries

from vehicle import locate_request_group_in_schedule, get_departure_time_at_node, is_empty_vehicle_schedule, \
    is_empty_stop, get_next_occ_of_node, get_pick_up_nodes_dest, get_nodes_in_range, \
    get_insertion_possibilities, room_for_insertion_at_node, get_next_node, get_prev_node, \
    get_last_arrival, get_all_occurrences_of_node, boarding_pass_at_node, count_boarding_pax_until_dest, \
    count_inveh_pax_over_node, get_occ

from requests import get_od_from_request_group, get_rep_pick_up_time

from settings import max_vehicle_ride_time, M, stop_addition_penalty, v_mean


def remove_request_group(network, vehicles_schedule, request_group):
    vehicle, node = locate_request_group_in_schedule(vehicles_schedule, request_group)
    o, d = get_od_from_request_group(request_group)

    max_pt = get_rep_pick_up_time(request_group)
    old_departure_time = get_departure_time_at_node(vehicles_schedule, vehicle, node)

    destination_node = get_next_occ_of_node(vehicles_schedule, vehicle, node, d)
    remaining_request_groups = [element for element in vehicles_schedule[vehicle][node][1:]
                                if all([x != y for x in element for y in request_group])]
    if len(remaining_request_groups) == 0:
        vehicles_schedule[vehicle][node] = [vehicles_schedule[vehicle][node][0]]
    else:
        vehicles_schedule[vehicle][node] = [vehicles_schedule[vehicle][node][0]] + remaining_request_groups

    if is_empty_stop(vehicles_schedule, vehicle, node) and \
            len(get_pick_up_nodes_dest(vehicles_schedule, vehicle, node)) == 0:
        del vehicles_schedule[vehicle][node]

    if is_empty_stop(vehicles_schedule, vehicle, destination_node) and \
            len(get_pick_up_nodes_dest(vehicles_schedule, vehicle, destination_node)) == 0:
        del vehicles_schedule[vehicle][destination_node]

    # check if the max pick up time is binding for the departure time at the stop
    if max_pt == old_departure_time and not is_empty_vehicle_schedule(vehicles_schedule, vehicle):
        for n in get_nodes_in_range(vehicles_schedule, vehicle):
            update_dep_time_at_node(vehicles_schedule, vehicle, n, network)


def find_best_position_for_request_group(network, vehicles_schedule, request_group, current_vehicle=1,
                                         best_pos_so_far=None, excluded_vehicles=None, capacity=20, depot='terminal'):
    """
    Function that returns the best possible position in the schedule for insertion,
    taking into account capacity constraints. In a recursive way, it tries to compare for every vehicle the respecitvely
    best costs for insertion. For whichever vehicle this representative cost is lowest, it is inserted in that vehicle,
    on that position.
    """

    if current_vehicle > len(list(vehicles_schedule)):
        return best_pos_so_far

    if not excluded_vehicles:
        excluded_vehicles = set()

    if current_vehicle in excluded_vehicles:
        current_vehicle += 1
        return find_best_position_for_request_group(network, vehicles_schedule, request_group,
                                                    current_vehicle, best_pos_so_far, excluded_vehicles)

    insertion_constraints = get_insertion_possibilities(vehicles_schedule, current_vehicle, request_group)

    for ins_con in insertion_constraints:
        matching_score = find_pos_cost_given_ins_cons(vehicles_schedule, current_vehicle, request_group, ins_con,
                                                      network, capacity, depot)
        if not best_pos_so_far or min(best_pos_so_far[2], matching_score) == matching_score:
            best_pos_so_far = current_vehicle, ins_con, round(matching_score, 2)

    current_vehicle += 1
    return find_best_position_for_request_group(network, vehicles_schedule, request_group, current_vehicle,
                                                best_pos_so_far, excluded_vehicles, capacity, depot)


def iter_find_best_position_for_request_group(network, vehicles_schedule, request_group, capacity, depot):
    """
    Function that returns the best possible position in the schedule for insertion,
    taking into account capacity constraints. In a recursive way, it tries to compare for every vehicle the respecitvely
    best costs for insertion. For whichever vehicle this representative cost is lowest, it is inserted in that vehicle,
    on that position.
    """

    current_vehicle = 1
    best_pos_so_far = None

    while current_vehicle <= len(list(vehicles_schedule)):

        insertion_constraints = get_insertion_possibilities(vehicles_schedule, current_vehicle, request_group)

        for ins_con in insertion_constraints:
            matching_score = find_pos_cost_given_ins_cons(vehicles_schedule, current_vehicle, request_group,
                                                          ins_con, network, capacity, depot)
            if not best_pos_so_far or min(best_pos_so_far[2], matching_score) == matching_score:
                best_pos_so_far = current_vehicle, ins_con, round(matching_score, 2)

        current_vehicle += 1

    return best_pos_so_far


def find_random_position_for_request_group(vehicles_schedule, request_group, current_vehicle=1):
    """
    Function that returns a feasible (that is, respecting the capacity constraint) position for a request group.
    The cost of this position does not matter. Also, it could very well be the same position as it was in before.
    """

    random_vehicle = random.choice(list(vehicles_schedule))
    while is_empty_vehicle_schedule(vehicles_schedule, random_vehicle):
        random_vehicle = random.choice(list(vehicles_schedule))

    insertion_constraints = get_insertion_possibilities(vehicles_schedule, random_vehicle, request_group)
    random_ins_cons = random.choice(insertion_constraints)

    return random_vehicle, random_ins_cons


def find_pos_cost_given_ins_cons(vehicles_schedule, vehicle, request_group, insertion_constraint,
                                 network, capacity, depot):
    """
    Returns how a vehicles scores for accommodating a request group, GIVEN AN INSERTION CONSTRAINT: this is based
    on the difference between the departure time at a stop and the max pickup time of a request group.

    On this level, the best possible position is returned given a SINGLE 'insertion_constraint', which is given as an input.
    This constraint can either be:
    - 'first entry': if the vehicle schedule is empty so far
    - 'insert d after', o: then, the request_group has to be inserted AFTER a node which fits the origin
    - 'insert o before', x': then, the origin is inserted in the schedule before a node x
    - 'on arc with o', o: then, the arc exists within the schedule and it might be inserted on this arc, starting at origin o
    - 'insert o after', x: then, the destination is within the schedule, and so the arc might be fitted RIGHT BEFORE d,
    and after a node x
    """
    cost_matrix = generate_cost_matrix(network, v_mean)
    network_dim = get_network_boundaries(network)

    if depot == 'terminal':
        dep = network_dim[0]
    elif depot == 'middle':
        dep = network_dim[1]
    else:
        dep = network_dim[2]

    o, d = get_od_from_request_group(request_group)
    request_group_rep_pt = get_rep_pick_up_time(request_group, method='max')
    # initialize at a very high cost
    detour_cost = M
    dep_time_offset = M

    last_node = None

    if not is_empty_vehicle_schedule(vehicles_schedule, vehicle):
        last_node = get_next_node(vehicles_schedule, vehicle)

    if insertion_constraint == 'first entry':
        detour_cost = 0.0
        dep_time_offset = 0.0

    default_multiplier = len(request_group)
    # default_multiplier = 1

    if capacity > 20: # additional correction factor when capacity increases.
        kappa = 0.5
    else:
        kappa = 0.1

    if type(insertion_constraint) == tuple:
        available_cap = room_for_insertion_at_node(vehicles_schedule, vehicle, insertion_constraint[1], capacity=capacity)
        feasible_portion = request_group[:min(len(request_group), available_cap)]
        default_multiplier = len(feasible_portion)
        # print(request_group_rep_pt, get_rep_pick_up_time(feasible_portion))
        request_group_rep_pt = min(request_group_rep_pt, get_rep_pick_up_time(feasible_portion, method='max'))

    # two subcases for 'insert d after', o : (1) the selected o is not the last node, (2) o is the last node
    if insertion_constraint[0] == 'insert d after' and \
            room_for_insertion_at_node(vehicles_schedule, vehicle, insertion_constraint[1], capacity=capacity) > 0 and \
            get_next_node(vehicles_schedule, vehicle, insertion_constraint[1]):

        x = get_next_node(vehicles_schedule, vehicle, insertion_constraint[1])

        waiting_passengers_mult = count_boarding_pax_until_dest(vehicles_schedule, vehicle, x, last_node)
        inveh_passenger_mult = count_inveh_pax_over_node(vehicles_schedule, vehicle, x)
        detour_cost = (cost_matrix[(o, d)] + cost_matrix[(d, cv(x))] -
                       cost_matrix[(o, cv(x))])*(default_multiplier + inveh_passenger_mult + waiting_passengers_mult)*kappa
        dep_time_offset = abs(request_group_rep_pt -
                              get_departure_time_at_node(vehicles_schedule, vehicle, insertion_constraint[1])) \
                           *(default_multiplier + inveh_passenger_mult + waiting_passengers_mult)*kappa


    # we don't affect other passenger by inserting a destination node after the existing schedule
    elif insertion_constraint[0] == 'insert d after' and \
            room_for_insertion_at_node(vehicles_schedule, vehicle, insertion_constraint[1], capacity=capacity) > 0 and \
            not get_next_node(vehicles_schedule, vehicle, insertion_constraint[1]):

        detour_cost = 0
        dep_time_offset = abs(request_group_rep_pt - get_departure_time_at_node(vehicles_schedule,
                                                                                vehicle, insertion_constraint[1]))*(default_multiplier)

    # we don't have to check for capacity if it is the first node we're checking
    elif insertion_constraint[0] == 'insert o before':
        waiting_passengers_mult = count_boarding_pax_until_dest(vehicles_schedule, vehicle,
                                                                insertion_constraint[1], last_node)
        detour_cost = 0
        dep_time_offset = abs(get_departure_time_at_node(vehicles_schedule, vehicle, insertion_constraint[1])
                              - cost_matrix[o, d] - request_group_rep_pt - cost_matrix[dep, o]
                              )*(default_multiplier + waiting_passengers_mult)*kappa

    elif insertion_constraint[0] == 'on arc with o: ' and \
            room_for_insertion_at_node(vehicles_schedule, vehicle, insertion_constraint[1],
                                       get_next_occ_of_node(vehicles_schedule, vehicle, insertion_constraint[1], d), capacity=capacity) > 0:
        waiting_passengers_mult = count_boarding_pax_until_dest(vehicles_schedule, vehicle, insertion_constraint[1],
                                                                last_node)
        inveh_passenger_mult = count_inveh_pax_over_node(vehicles_schedule, vehicle, insertion_constraint[1])
        detour_cost = -stop_addition_penalty
        dep_time_offset = abs(get_departure_time_at_node(vehicles_schedule, vehicle, insertion_constraint[1])
                              - request_group_rep_pt)*(default_multiplier + waiting_passengers_mult + inveh_passenger_mult)*kappa

    elif insertion_constraint[0] == 'insert o after' and \
            room_for_insertion_at_node(vehicles_schedule, vehicle, insertion_constraint[1], capacity=capacity) > 0:
        x = insertion_constraint[1]
        d = get_next_node(vehicles_schedule, vehicle, x)

        waiting_passengers_mult = count_boarding_pax_until_dest(vehicles_schedule, vehicle, d, last_node)
        inveh_passenger_mult = count_inveh_pax_over_node(vehicles_schedule, vehicle, d)

        detour_cost = (cost_matrix[(cv(x), o)] + cost_matrix[(o, cv(d))]
                       - cost_matrix[(cv(x), cv(d))])*(default_multiplier + waiting_passengers_mult + inveh_passenger_mult)*kappa
        dep_time_offset = abs(get_departure_time_at_node(vehicles_schedule, vehicle, insertion_constraint[1])
                              + cost_matrix[(cv(x), o)] - request_group_rep_pt)*(default_multiplier + (waiting_passengers_mult + inveh_passenger_mult))*kappa


    # we don't need to check for capacity in the following two cases
    elif insertion_constraint == 'in front':
        first_node = get_prev_node(vehicles_schedule, vehicle)
        waiting_passengers_mult = count_boarding_pax_until_dest(vehicles_schedule, vehicle, first_node, last_node)
        detour_cost = 0*stop_addition_penalty
        dep_time_offset = abs(get_departure_time_at_node(vehicles_schedule, vehicle, first_node) -
                              cost_matrix[(d, cv(first_node))] -
                              request_group_rep_pt - cost_matrix[(o, d)] -
                              cost_matrix[(dep, o)])*(default_multiplier + waiting_passengers_mult)*kappa

    elif insertion_constraint == 'back':
        last_node = get_next_node(vehicles_schedule, vehicle)
        detour_cost = cost_matrix[(cv(last_node), o)]
        dep_time_offset = abs(
            request_group_rep_pt - get_departure_time_at_node(vehicles_schedule, vehicle, last_node))*(default_multiplier)

    # penalize the entry if the vehicle already has a lengthy tour
    if not is_empty_vehicle_schedule(vehicles_schedule, vehicle) and \
            get_last_arrival(vehicles_schedule, vehicle) > max_vehicle_ride_time:
        detour_cost += M
        dep_time_offset += M

    position_cost = detour_cost + dep_time_offset
    return position_cost


def insert_request_group(network, vehicles_schedule, requests_dict, request_group, vehicle, position,
                         return_added_portion=False, ignore_request_dict=False, capacity=20, depot='terminal'):
    """
    Inserts a request group in the specified vehicle and position within that vehicle (=start node and end node).
    The function calls an auxiliary function 'insert_stop_in_vehicle' whenever it is needed to insert a new stop.
    In all cases, the departure times at stops are corrected.
    """

    if position == 'current pos':
        return

    o, d = get_od_from_request_group(request_group)
    node_to_insert_pax = None
    end_node = None
    added_portion = None

    if position[0] == 'insert d after':
        insert_stop_in_vehicle(vehicles_schedule, vehicle, node_type=d,
                               next_stop=get_next_node(vehicles_schedule, vehicle, position[1]), network=network, depot=depot)
        node_to_insert_pax = position[1]

    elif position[0] == 'insert o before':
        node_to_insert_pax = insert_stop_in_vehicle(vehicles_schedule, vehicle, node_type=o, next_stop=position[1], network=network, depot=depot)
    elif position[0] == 'on arc with o: ':
        node_to_insert_pax = position[1]
        end_node = get_next_occ_of_node(vehicles_schedule, vehicle, position[1], d)
    elif position[0] == 'insert o after':
        node_to_insert_pax = insert_stop_in_vehicle(vehicles_schedule, vehicle, node_type=o,
                                                    next_stop=get_next_node(vehicles_schedule, vehicle, position[1]), network=network, depot=depot)
    elif position == 'in front':
        node_to_insert_pax = insert_stop_in_vehicle(vehicles_schedule, vehicle, node_type=(o, d),
                                                    next_stop='first stop', network=network, depot=depot)
    elif position == 'back':
        node_to_insert_pax = insert_stop_in_vehicle(vehicles_schedule, vehicle, node_type=(o, d), network=network, depot=depot)

    elif position == 'first entry':
        node_to_insert_pax = insert_stop_in_vehicle(vehicles_schedule, vehicle, node_type=(o, d), network=network, depot=depot)

    if return_added_portion:
        added_portion = occupy_available_seats(vehicles_schedule, vehicle, requests_dict,
                                               request_group, node_to_insert_pax, end_node, return_added_portion,
                                               ignore_request_dict, capacity=capacity)
    else:
        occupy_available_seats(vehicles_schedule, vehicle, requests_dict,
                               request_group, node_to_insert_pax, end_node, return_added_portion, ignore_request_dict, capacity=capacity)
    update_dep_time_at_node(vehicles_schedule, vehicle, node_to_insert_pax, network)
    for next_node in get_nodes_in_range(vehicles_schedule, vehicle, start_node=node_to_insert_pax):
        update_dep_time_at_node(vehicles_schedule, vehicle, next_node, network)

    if return_added_portion:
        return added_portion


def insert_stop_in_vehicle(vehicle_schedule, vehicle, network, node_type=None, next_stop=None, depot='terminal'):
    """
    Function that adds a new stop in the vehicle, in front of the 'next_stop' parameter. By default, if the node_type doesn't
    occur in the schedule already, the node is inserted as a key 'node_type, 0'. But if node_type already occurs,
    then this second element of the key is increased by 1. The value or content of the stop is initiated as an empty list.

    see: https://stackoverflow.com/questions/44390818/how-to-insert-key-value-pair-into-dictionary-at-a-specified-position
    """
    cost_matrix = generate_cost_matrix(network, v_mean)
    network_dim = get_network_boundaries(network)

    if depot == 'terminal':
        dep = network_dim[0]
    elif depot == 'middle':
        dep = network_dim[1]
    else:
        dep = network_dim[2]

    items = list(vehicle_schedule[vehicle].items())
    curr_occ = 0
    occ = dict()

    if type(node_type) is int:
        all_occ_of_node_type = get_all_occurrences_of_node(vehicle_schedule, vehicle, node_type)
        if len(all_occ_of_node_type) > 0:
            max_occ = max([get_occ(t) for t in all_occ_of_node_type])
            curr_occ = max_occ + 1
    elif len(node_type) == 2:
        for n in node_type:
            all_occ_of_node_type = get_all_occurrences_of_node(vehicle_schedule, vehicle, n)
            occ[n] = 0
            if len(all_occ_of_node_type) > 0:
                max_occ = max([get_occ(t) for t in all_occ_of_node_type])
                occ[n] = max_occ + 1

    # if the next stop is the first node
    if next_stop and next_stop != 'first stop':
        insert_before = list(vehicle_schedule[vehicle]).index(next_stop)
        new_stop = str(node_type) + ',' + str(curr_occ)
        items.insert(insert_before, (new_stop, [float(cost_matrix[(dep, node_type)])]))
        vehicle_schedule[vehicle] = dict(items)

    elif next_stop == 'first stop':
        if is_empty_vehicle_schedule(vehicle_schedule, vehicle):
            print(vehicle, vehicle_schedule[vehicle])
        insert_before = list(vehicle_schedule[vehicle].keys()).index(get_prev_node(vehicle_schedule, vehicle))
        items.insert(insert_before, (str(node_type[1]) + ',' + str(occ[node_type[1]]),
                                     [0.0]))
        new_stop = str(node_type[0]) + ',' + str(occ[node_type[0]])
        items.insert(insert_before, (new_stop, [float(cost_matrix[(dep, node_type[0])])]))
        vehicle_schedule[vehicle] = dict(items)

    elif not next_stop and type(node_type) == int:
        items = list(vehicle_schedule[vehicle].items())
        new_stop = str(node_type) + ',' + str(curr_occ)
        items.append((new_stop, [0.0]))
        vehicle_schedule[vehicle] = dict(items)

    # if not next_stop and type(node_type) == tuple
    else:
        items = list(vehicle_schedule[vehicle].items())
        new_stop = str(node_type[0]) + ',' + str(occ[node_type[0]])
        items.append((new_stop, [float(cost_matrix[(dep, node_type[0])])]))
        items.append((str(node_type[1]) + ',' + str(occ[node_type[1]]),
                      [float(cost_matrix[(dep, node_type[0])] + cost_matrix[(node_type[0], node_type[1])])]))
        vehicle_schedule[vehicle] = dict(items)

    return new_stop


def occupy_available_seats(vehicles_schedule, vehicle, requests_dict, request_group, start_node,
                           end_node=None, return_added_portion=False, ignore_request_dict=False, capacity=20):
    """
    Positions the available capacity within the vehicle. Part of the request group that can be added
    Positions the available capacity within the vehicle. Part of the request group that can be added
    into the schedule is added and that same part is removed from the request dictionairy.
    The remaining part is kept in the request dictionairy.
    """

    if not start_node:
        return

    available_seats = room_for_insertion_at_node(vehicles_schedule, vehicle, start_node, end_node, capacity)
    portion_to_add = request_group[:min(available_seats, len(request_group))]

    # add request_group to the schedule
    if not boarding_pass_at_node(vehicles_schedule, vehicle, start_node):
        vehicles_schedule[vehicle][start_node][0] = max(round(get_rep_pick_up_time(portion_to_add), 2),
                                                        vehicles_schedule[vehicle][start_node][0])
    vehicles_schedule[vehicle][start_node].append(portion_to_add)

    # remove it from request dictionairy
    if ignore_request_dict is False:
        o, d = get_od_from_request_group(request_group)
        idx_rq = requests_dict[(o, d)].index(request_group)
        if len(request_group[min(available_seats, len(request_group)):]) > 0:
            requests_dict[(o, d)][idx_rq] = request_group[min(available_seats, len(request_group)):]
        else:
            requests_dict[(o, d)].remove(requests_dict[(o, d)][idx_rq])

    if return_added_portion:
        return portion_to_add


def update_dep_time_at_node(vehicles_schedule, vehicle, node, network):
    """
    Update the departure time of a vehicle at a certain stop.
    """
    cost_matrix = generate_cost_matrix(network, v_mean)
    imposed_dep_time_by_req_pt = 0

    if boarding_pass_at_node(vehicles_schedule, vehicle, node):
        imposed_dep_time_by_req_pt = max([get_rep_pick_up_time(group) for group in vehicles_schedule[vehicle][node][1:]])

    previous_node = get_prev_node(vehicles_schedule, vehicle, node)
    if previous_node:
        previous_node_dep_time = get_departure_time_at_node(vehicles_schedule, vehicle, previous_node)
        imposed_dep_time_by_prev_stop = previous_node_dep_time + cost_matrix[cv(previous_node), cv(node)]
    else:
        imposed_dep_time_by_prev_stop = np.float64()

    vehicles_schedule[vehicle][node][0] = round(max(imposed_dep_time_by_prev_stop,
                                                    imposed_dep_time_by_req_pt,
                                                    vehicles_schedule[vehicle][node][0]), 2)


def select_random_request_groups(vehicles_schedule, required_amount=1, random_request_groups=None):
    """
    Function that selects 'required_amount' request groups randomly from the schedule.
    """
    if random_request_groups is None:
        random_request_groups = []

    if required_amount == 0:
        return random_request_groups

    random_vehicle = random.choice(list(vehicles_schedule))
    while is_empty_vehicle_schedule(vehicles_schedule, random_vehicle):
        random_vehicle = random.choice(list(vehicles_schedule))

    random_stop = random.choice(list(vehicles_schedule[random_vehicle]))
    while is_empty_stop(vehicles_schedule, random_vehicle, random_stop):
        random_stop = random.choice(list(vehicles_schedule[random_vehicle]))

    random_request_group = random.choice(vehicles_schedule[random_vehicle][random_stop][1:])
    if random_request_group not in random_request_groups:
        random_request_groups.append(random_request_group)
        required_amount -= 1
        return select_random_request_groups(vehicles_schedule, required_amount, random_request_groups)

    else:
        required_amount -= 1
        return select_random_request_groups(vehicles_schedule, required_amount, random_request_groups)