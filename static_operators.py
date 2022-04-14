import numpy as np
import copy
import random

from vehicle import locate_request_group_in_schedule, get_departure_time_at_node, is_empty_vehicle_schedule, \
    is_empty_stop, get_next_occ_of_node, get_pick_up_nodes_dest, get_nodes_in_range, \
    get_insertion_possibilities, room_for_insertion_at_node, get_next_node, get_prev_node, \
    get_last_arrival, get_all_occurrences_of_node, boarding_pass_at_node, count_boarding_pax_until_dest, count_inveh_pax_over_node

from requests import get_od_from_request_group, get_max_pick_time, add_request_group_to_dict

from parameters import cost_matrix, cap_per_veh, nb_of_required_ser, max_vehicle_ride_time, M, stop_addition_penalty

# perhaps create a 'dumpster' in which removed requests are put? Then create a Not-None return for removal functions


def remove_request_group(vehicles_schedule, request_group):
    vehicle, node = locate_request_group_in_schedule(vehicles_schedule, request_group)
    o, d = get_od_from_request_group(request_group)

    max_pt = get_max_pick_time(request_group)
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
            update_dep_time_at_node(vehicles_schedule, vehicle, n)


def find_first_best_improvement_for_request_group(vehicles_schedule, request_group, original_score=None, current_vehicle=1,
                                                  best_improvement=None):
    "Find the first best improving position for a request group, in stead of looking for the best spot"

    if current_vehicle > nb_of_required_ser:
        return best_improvement

    insertion_constraints = get_insertion_possibilities(vehicles_schedule, current_vehicle, request_group)

    improvement_found = False
    i = 0
    while improvement_found is False or i < len(insertion_constraints):
        current_score = find_pos_cost_given_ins_cons(vehicles_schedule, current_vehicle, request_group, insertion_constraints[i])
        if not best_improvement:
            best_improvement = current_vehicle, insertion_constraints[i], round(current_score, 2)
            i += 1
        elif current_score < best_improvement[2]:
            best_improvement = current_vehicle, insertion_constraints[i], round(current_score, 2)
            improvement_found = True
            return best_improvement
        else:
            i += 1

    if improvement_found is False:
        current_vehicle += 1
        return find_first_best_improvement_for_request_group(vehicles_schedule, request_group, original_score, current_vehicle)


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


def find_pos_cost_given_ins_cons(vehicles_schedule, vehicle, request_group, insertion_constraint):
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

    request_group_max_pt = get_max_pick_time(request_group)
    o, d = get_od_from_request_group(request_group)
    # initialize at a very high cost
    detour_cost = M
    dep_time_offset = M

    last_node = None

    if not is_empty_vehicle_schedule(vehicles_schedule, vehicle):
        last_node = get_next_node(vehicles_schedule, vehicle)

    if insertion_constraint == 'first entry':
        detour_cost = 0.0
        dep_time_offset = 0.0

    # two subcases for 'insert d after', o : (1) the selected o is not the last node, (2) o is the last node
    elif insertion_constraint[0] == 'insert d after' and \
            room_for_insertion_at_node(vehicles_schedule, vehicle, insertion_constraint[1]) > 0 and \
            get_next_node(vehicles_schedule, vehicle, insertion_constraint[1]):

        x = get_next_node(vehicles_schedule, vehicle, insertion_constraint[1])

        waiting_passengers_mult = count_boarding_pax_until_dest(vehicles_schedule, vehicle, x, last_node)
        inveh_passenger_mult = count_inveh_pax_over_node(vehicles_schedule, vehicle, x)
        detour_cost = (cost_matrix[(o, d)] + cost_matrix[(d, int(x[0]))] -
                       cost_matrix[(o, int(x[0]))])*(1 + waiting_passengers_mult) + stop_addition_penalty
        dep_time_offset = abs(request_group_max_pt - get_departure_time_at_node(vehicles_schedule, vehicle,
                                                                                insertion_constraint[1]))*inveh_passenger_mult

    # we don't affect other passenger by inserting a destination node after the existing schedule
    elif insertion_constraint[0] == 'insert d after' and \
            room_for_insertion_at_node(vehicles_schedule, vehicle, insertion_constraint[1]) > 0 and \
            not get_next_node(vehicles_schedule, vehicle, insertion_constraint[1]):

        detour_cost = 0
        dep_time_offset = abs(request_group_max_pt - get_departure_time_at_node(vehicles_schedule,
                                                                                vehicle, insertion_constraint[1]))

    # we don't have to check for capacity if it is the first node we're checking
    elif insertion_constraint[0] == 'insert o before':
        waiting_passengers_mult = count_boarding_pax_until_dest(vehicles_schedule, vehicle,
                                                                insertion_constraint[1], last_node)
        detour_cost = 0
        dep_time_offset = abs(get_departure_time_at_node(vehicles_schedule, vehicle, insertion_constraint[1])
                              - cost_matrix[o, d] - request_group_max_pt)*(1 + waiting_passengers_mult)

    elif insertion_constraint[0] == 'on arc with o: ' and \
            room_for_insertion_at_node(vehicles_schedule, vehicle, insertion_constraint[1],
                                       get_next_occ_of_node(vehicles_schedule, vehicle, insertion_constraint[1],
                                                            d)) > 0:
        waiting_passengers_mult = count_boarding_pax_until_dest(vehicles_schedule, vehicle, insertion_constraint[1],
                                                             last_node)
        inveh_passenger_mult = count_inveh_pax_over_node(vehicles_schedule, vehicle, insertion_constraint[1])
        detour_cost = -stop_addition_penalty
        dep_time_offset = abs(get_departure_time_at_node(vehicles_schedule, vehicle, insertion_constraint[1])
                              - request_group_max_pt)*(1 + waiting_passengers_mult + inveh_passenger_mult)

    elif insertion_constraint[0] == 'insert o after' and \
            room_for_insertion_at_node(vehicles_schedule, vehicle, insertion_constraint[1]) > 0:
        x = insertion_constraint[1]
        d = get_next_node(vehicles_schedule, vehicle, x)

        waiting_passengers_mult = count_boarding_pax_until_dest(vehicles_schedule, vehicle, d,
                                                             last_node)
        inveh_passenger_mult = count_inveh_pax_over_node(vehicles_schedule, vehicle, d)

        detour_cost = (cost_matrix[(int(x[0]), o)] + cost_matrix[(o, int(d[0]))]
                       - cost_matrix[(int(x[0]), int(d[0]))])*(waiting_passengers_mult + inveh_passenger_mult)
        dep_time_offset = abs(get_departure_time_at_node(vehicles_schedule, vehicle, insertion_constraint[1])
                              + cost_matrix[int(x[0]), o] - request_group_max_pt)*(1 + (waiting_passengers_mult + inveh_passenger_mult))

    # we don't need to check for capacity in the following two cases
    elif insertion_constraint == 'in front':
        first_node = get_prev_node(vehicles_schedule, vehicle)
        # here you add a penalty for adding requests in front, because it is often too cheap
        # detour_cost = chaining_penalty * (len(get_nodes_in_range(vehicles_schedule, vehicle)) - penalty_threshold)

        waiting_passengers_mult = count_boarding_pax_until_dest(vehicles_schedule, vehicle, first_node,
                                                                last_node)
        detour_cost = stop_addition_penalty
        dep_time_offset = abs(get_departure_time_at_node(vehicles_schedule, vehicle, first_node) -
                              cost_matrix[(d, int(first_node[0]))] -
                              request_group_max_pt + cost_matrix[(o, d)])*(1 + waiting_passengers_mult)

    elif insertion_constraint == 'back':
        last_node = get_next_node(vehicles_schedule, vehicle)
        detour_cost = cost_matrix[(int(last_node[0]), o)]
        dep_time_offset = abs(
            request_group_max_pt - get_departure_time_at_node(vehicles_schedule, vehicle, last_node))

    # penalize the entry if the vehicle already has a lengthy tour
    if not is_empty_vehicle_schedule(vehicles_schedule, vehicle) and \
            get_last_arrival(vehicles_schedule, vehicle) > max_vehicle_ride_time:
        detour_cost += M
        dep_time_offset += M

    position_cost = detour_cost + dep_time_offset
    return position_cost


def insert_request_group(vehicles_schedule, requests_dict, request_group, vehicle, position):
    """
    Inserts a request group in the specified vehicle and position within that vehicle (=start node and end node).
    The function calls an auxiliary function 'insert_stop_in_vehicle' whenever it is needed to insert a new stop.
    In all cases, the departure times at stops are corrected.
    """

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
        node_to_insert_pax = insert_stop_in_vehicle(vehicles_schedule, vehicle, node_type=(o, d),
                                                    next_stop='first stop')
    elif position == 'back':
        node_to_insert_pax = insert_stop_in_vehicle(vehicles_schedule, vehicle, node_type=(o, d))

    if not is_empty_vehicle_schedule(vehicles_schedule, vehicle):
        occupy_available_seats(vehicles_schedule, vehicle, requests_dict, request_group, node_to_insert_pax, end_node)
        update_dep_time_at_node(vehicles_schedule, vehicle, node_to_insert_pax)
        # update the departure time of all upcoming nodes
        for next_node in get_nodes_in_range(vehicles_schedule, vehicle, start_node=node_to_insert_pax):
            update_dep_time_at_node(vehicles_schedule, vehicle, next_node)
    elif position == 'first entry':
        o, d = get_od_from_request_group(request_group)
        pt = get_max_pick_time(request_group)

        vehicles_schedule[vehicle][str(o) + ',0'] = [pt, request_group]
        vehicles_schedule[vehicle][str(d) + ',0'] = [round(pt + cost_matrix[(o, d)], 2)]


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
        insert_before = list(vehicle_schedule[vehicle]).index(next_stop)
        new_stop = str(node_type) + ',' + str(curr_occ)
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
        return select_random_request_groups(vehicles_schedule, required_amount, random_request_groups)

    else:
        required_amount -= 1
        return select_random_request_groups(vehicles_schedule, required_amount, random_request_groups)