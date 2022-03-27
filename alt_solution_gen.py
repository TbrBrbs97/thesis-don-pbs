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
    request_assignment = dict()

    for v in range(1, nb_of_available_veh+1):
        if seed is True:
            random.seed(1)

        request_group = pop_request(request_dict)
        o, d = get_od_from_request_group(request_group)
        pt = get_max_pick_time(request_group)

        vehicles_schedule[v] = dict()
        vehicles_schedule[v][str(o)+',0'] = [pt, request_group]
        vehicles_schedule[v][str(d)+',0'] = [pt + cost_matrix[(o, d)]]

        # request_dict[(o, d)].remove(request_group)
        # request_assignment[str(request_group)] = [str(o)+',0', pt, str(d)+',0', pt + cost_matrix[(o, d)]]

    return vehicles_schedule #, request_assignment


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
    taking into account capacity constraints. In a recursive way, it tries to compare for every vehicle the respecitvely
    best costs for insertion. For whichever vehicle this representative cost is lowest, it is inserted there.

    # TODO:
    # - First, you look for best vehicle - difference dep.time & pick-up OR closest stop
    # - Second, you find the exact position within the chosen vehicle

    '''

    o, d = get_od_from_request_group(request_group)
    request_group_max_pt = get_max_pick_time(request_group)

    if current_vehicle > nb_of_required_ser:
        return vehicles_schedule

    insertion_constraints = get_insertion_possibilities(vehicles_schedule, current_vehicle, (o, d))

    if insertion_constraints:
        for ins_con in insertion_constraints:
            matching_score = find_best_position_within_vehicle(vehicles_schedule, request_group, ins_con, current_vehicle)
            if max(best_pos_so_far[1], matching_score) == matching_score or best_pos_so_far is None:
                best_pos_so_far = current_vehicle, matching_score
    else: # in all other cases, you position the request group either in front of existing chain / behind it
        matching_score = find_best_position_within_vehicle(vehicles_schedule, request_group, None, current_vehicle)
        if max(best_pos_so_far[1], matching_score) == matching_score or best_pos_so_far is None:
            best_pos_so_far = current_vehicle, matching_score

    # else: > if neither o or d are in the schedule
        # if the dep time at o < the dep at the starting stop + driving time, add it before
        # in the case o > dep_t at the last stop + driving time, chain the arc in the end

    current_vehicle += 1
    return find_best_position_for_request_group(vehicles_schedule, request_group, current_vehicle, best_pos_so_far)


def find_best_position_within_vehicle(vehicles_schedule, request_group, insertion_constraint, vehicle):
    '''
    Returns how a vehicles scores for accommodating a request group: this is based
    on the difference between the departure time at a stop and the max pickup time of a request group.

    On this level, the best possible postion is returned given the 'insertion_constraint', which is given as an input.
    This constraint can either be:
    - Origin, destination: then, the request_group has to be inserted AFTER a node which fits the origin
    - The origin: then, the request_group has to be inserted AFTER a node which fits the origin
    - The destination: then, the request_group has to be inserted RIGHT BEFORE a node which fits the destination

    As there might be multiple occurences where the insertion constraint hold true (e.g. ['2,0', '2,1', ...]),
    the function returns the best position among those locations.
    '''

    o, d = get_od_from_request_group(request_group)
    request_group_max_pt = get_max_pick_time(request_group)

    if insertion_constraint:
        occ_of_node = get_all_occurrences_of_node(vehicles_schedule, vehicle, insertion_constraint)
        best_matching_pos = calc_best_matching_position(vehicles_schedule, vehicle, request_group_max_pt, (o, d),
                                                            occ_of_node, insertion_constraint)

        return best_matching_pos
    else: # check for an insertion in this vehicle before or after the already existing schedule
        return None


def calc_best_matching_position(vehicles_schedule, vehicle, max_pt_rg, od_rg, occurrences, insertion_constraint):
    '''
    Given that there are multiple occurences of a node (e.g. ['2,0', '2,1', ...])
    '''
    # best_matching_node = previous_node, next_node, matching_score
    best_matching_position = None

    # if both the origin & dest. can be found as an arc, or if only the origin can be found as an arc
    if insertion_constraint == od_rg or insertion_constraint[0] == od_rg[0]:
        for node in occurrences:
            dep_time = get_departure_time_at_node(vehicles_schedule, vehicle, node)
            delta_dep_time = abs(dep_time - max_pt_rg)

            if best_matching_position is None or delta_dep_time < best_matching_position[1]\
                    and room_for_insertion_at_node(vehicles_schedule, vehicle, node) > 0:
                best_matching_position = node, delta_dep_time
    # if only the destionation can be found as an arc
    elif insertion_constraint[0] == od_rg[1]:
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
    else: # meaning that neither origin or destination of the rg appear in the schedule of the vehicle
        return None


    return best_matching_position


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
    if index_of_node < len(nodes_in_vehicle)-1:
        return nodes_in_vehicle[index_of_node + 1]
    else:
        return None


def get_insertion_possibilities(vehicles_schedule, current_vehicle, od_tup):
    '''
    Returns all possible insertions (not checked with capacity yet) for a request group with
    'od_tup'.
    '''

    o, d = od_tup

    positions_at_origin = [('insert d after', node) for node in vehicles_schedule[current_vehicle] if int(node[0]) == o
                           and get_next_occ_of_node(vehicles_schedule, current_vehicle, node, d) is None]
    positions_before_first_stop = [('insert o before', node) for node in vehicles_schedule[current_vehicle]
                                   if int(node[0]) == d and get_prev_node(vehicles_schedule, current_vehicle, node) is None]
    positions_on_existing_arc = [('on arc with o: ', node) for node in vehicles_schedule[current_vehicle]
                                   if int(node[0]) == d and get_next_occ_of_node(vehicles_schedule, current_vehicle, node, d) is not None]
    positions_before_dest = [('insert o after', node) for node in vehicles_schedule[current_vehicle] if
                             get_next_node(vehicles_schedule, current_vehicle, node) is not None and
                             int(get_next_node(vehicles_schedule, current_vehicle, node)[0]) == d and node not in
                             [tup[1] for tup in positions_on_existing_arc]]

    return positions_at_origin + positions_before_dest + positions_before_first_stop + positions_on_existing_arc


def get_existing_arcs(vehicles_schedule, vehicle):
    '''
    Function that returns a list of the already present arcs in the vehicle schedule, created
    by the pick-up and drop-off of passengers.
    '''

    nodes = list(vehicles_schedule[vehicle].keys())
    return [(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)]


def get_existing_nodes(vehicles_schedule, vehicle, node_type=None):
    '''
    Function that returns the list of existing nodes/stops in a vehicle schedule.
    The parameter node_type allows to specify whether or not
    '''
    if not node_type:
        return [node for node in vehicles_schedule[vehicle]]
    else:
        return [node for node in vehicles_schedule[vehicle] if int(node[0]) == node_type]


def get_all_occurrences_of_node(vehicles_schedule, vehicle, insertion_constraint):
    '''
    Function that returns a list of all occurences of a certain stop
    in the schedule of a vehicle. We only need to know if either the origin or the destination is within the vehicle.
    '''

    return [n for n in vehicles_schedule[vehicle] if int(n[0]) == insertion_constraint[0]]


def get_next_occ_of_node(vehicles_schedule, vehicle, start_node, target_node):
    all_nodes = get_existing_nodes(vehicles_schedule, vehicle)
    idx_start_node = all_nodes.index(start_node)

    for idx in range(idx_start_node, len(all_nodes)):
        if vehicles_schedule[vehicle][all_nodes[idx]][0] == target_node:
            return all_nodes[idx]


def room_for_insertion_at_node(vehicles_schedule, vehicle, node):
    '''
    Returns the available capacity for insertion at a node 'node'. The function essentially diminishes the capacity
    per vehicle (which is a parameter) with the amount of request which obey the following criteria:
    1) The requests already boarding the vehicle at 'node';
    2) The requests boarding at any node before 'node', and also having a drop-off node after 'node'.

    '''

    pax_boarding_at_current_stop = 0
    pax_from_prev_stops = 0

    if boarding_pass_at_node(vehicles_schedule, vehicle, node):
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
        if boarding_pass_at_node(vehicles_schedule, vehicle, node):
            for group in vehicles_schedule[vehicle][node][1:]:
                group_origin, group_destination = get_od_from_request_group(group)
                idx_occ, destination_node = get_next_occ_of_node(vehicles_schedule, vehicle, all_nodes[0], group_destination)
                if destination_node not in all_previous_nodes:
                    transit_pax += len(group)

    return transit_pax


def boarding_pass_at_node(vehicles_schedule, vehicle, node):
    return True if len(vehicles_schedule[vehicle][node]) == 1 else False


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




