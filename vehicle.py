from requests import get_od_from_request_group, get_max_pick_time

from parameters import cap_per_veh, req_max_cluster_time, cost_matrix, network_dim


def get_served_stops(solution, vehicle):
    # this is only for vehicle v!
    # check for every stop what the origin and destination of stops are
    served_stops = set(())
    for s in solution[vehicle]:
        for rg in range(1, len(solution[vehicle][s])):
            for req in solution[vehicle][s][rg]:
                served_stops.add(req[0][0])  # add the origin and destination
                served_stops.add(req[0][1])

    return served_stops


def get_stop_dep_time(solution, service, stop):
    if stop in solution[service].keys() and not is_empty_stop(solution, service, stop):
        return solution[service][stop][0]
    else:
        return 0


def get_previous_stop_dep_time(solution, service, stop, network_dim):

    if stop > network_dim[0]:
        previous_stop = stop-1
        while is_empty_stop(solution, service, previous_stop) and previous_stop > network_dim[0]:
            previous_stop -= 1
    else:
        previous_stop = stop

    return previous_stop, get_stop_dep_time(solution, service, previous_stop)


def get_first_stop(solution, service):
    stop = 1

    while stop <= len(solution[service]):
        if len(solution[service][stop]) != 0:
            return stop
        stop += 1


def get_last_stop(solution, service):
    # this function can only be called after the initial schedule is made!
    stop = 1

    while stop <= len(solution[service]):
        if len(solution[service][stop]) == 1:
            return stop
        stop += 1


def get_vehicle_availability(solution, service, network_dim, od_matrix):

    # if the last stops equals the terminal, then it has made a round trip
    if get_last_stop(solution, service) == network_dim[2]:
        return solution[service][network_dim[2]][0]
    else:
        # here you have to add the time driving back from the city center to the terminal!
        return solution[service][network_dim[1]][0] + od_matrix[(network_dim[1], network_dim[0])]


def get_vehicle_first_departure(solution, key, network_dim):
    s = network_dim[0]
    while len(solution[key][s]) == 0:
        s += 1
    return solution[key][s][0]


def get_services_per_vehicle(solution, vehicle):
    # returns a list of of services per vehicle
    return [k for k in solution.keys() if k[0] == vehicle]


# FROM HERE ARE NEW FUNCTIONS


def get_insertion_possibilities(vehicles_schedule, vehicle, request_group):
    """
    Returns all possible insertions (not checked with capacity yet) for a request group.
    """

    o, d = get_od_from_request_group(request_group)

    if not is_empty_vehicle_schedule(vehicles_schedule, vehicle):
        positions_at_origin = [('insert d after', node) for node in vehicles_schedule[vehicle] if int(node[0]) == o
                               and get_next_occ_of_node(vehicles_schedule, vehicle, node, d) is None]
        positions_before_first_stop = [('insert o before', node) for node in vehicles_schedule[vehicle]
                                       if int(node[0]) == d and get_prev_node(vehicles_schedule, vehicle, node) is None]
        positions_on_existing_arc = [('on arc with o: ', node) for node in vehicles_schedule[vehicle]
                                     if int(node[0]) == o and get_next_occ_of_node(vehicles_schedule, vehicle, node, d) is not None]
        positions_before_dest = [('insert o after', node) for node in vehicles_schedule[vehicle] if
                                 get_next_node(vehicles_schedule, vehicle, node) is not None and
                                 int(get_next_node(vehicles_schedule, vehicle, node)[0]) == d and node not in
                                 [tup[1] for tup in positions_on_existing_arc]]
        default_positions = ['in front', 'back']

        insertion_constraints = positions_at_origin + positions_before_dest + positions_before_first_stop + \
                                positions_on_existing_arc + default_positions

    else:
        insertion_constraints = ['first entry']

    return insertion_constraints


def get_prev_node(vehicles_schedule, vehicle, node=None):
    """
    Returns the previous node to the node given as input in the schedule.
    If the parameter 'node' is None, then the fucntion returns the first node
    """
    nodes_in_vehicle = get_existing_nodes(vehicles_schedule, vehicle)

    if node:
        index_of_node = nodes_in_vehicle.index(node)
        if index_of_node > 0:
            return nodes_in_vehicle[index_of_node - 1]
        else:
            return None
    else:
        return nodes_in_vehicle[0]


def get_next_node(vehicles_schedule, vehicle, node=None):
    """
    Returns the next node to the node given as input in the schedule.
    If the parameter 'node' is None, then the function returns the last node
    """
    nodes_in_vehicle = get_existing_nodes(vehicles_schedule, vehicle)

    if node:
        index_of_node = nodes_in_vehicle.index(node)
        if index_of_node < len(nodes_in_vehicle)-1:
            return nodes_in_vehicle[index_of_node + 1]
        else:
            return None
    else:
        return nodes_in_vehicle[-1]


def get_nodes_in_range(vehicles_schedule, vehicle, start_node=None, end_node=None, start_included=False):
    """
    Returns all nodes in a given range
    """
    all_nodes = get_existing_nodes(vehicles_schedule, vehicle)

    if not start_node and end_node:
        idx_end_node = all_nodes.index(end_node)
        return all_nodes[:idx_end_node]
    elif start_node and not end_node:
        idx_start_node = all_nodes.index(start_node)
        if start_node:
            return all_nodes[idx_start_node:]
        else:
            return all_nodes[idx_start_node + 1:]
    elif start_node and end_node:
        idx_start_node = all_nodes.index(start_node)
        idx_end_node = all_nodes.index(end_node)
        if start_included:
            return all_nodes[idx_start_node:idx_end_node + 1]
        else:
            return all_nodes[idx_start_node + 1:idx_end_node + 1]
    else:
        return all_nodes


def get_existing_arcs(vehicles_schedule, vehicle):
    """
    Function that returns a list of the already present arcs in the vehicle schedule, created
    by the pick-up and drop-off of passengers.
    """

    nodes = list(vehicles_schedule[vehicle].keys())
    return [(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)]


def get_existing_nodes(vehicles_schedule, vehicle, node_type=None):
    """
    Function that returns the list of existing nodes/stops in a vehicle schedule.
    The parameter node_type allows to specify whether or not
    """

    if not node_type:
        return [node for node in vehicles_schedule[vehicle]]
    else:
        return [node for node in vehicles_schedule[vehicle] if int(node[0]) == node_type]


def get_all_occurrences_of_node(vehicles_schedule, vehicle, node_type):
    """
    Function that returns a list of all occurences of a certain stop
    in the schedule of a vehicle. We only need to know if either the origin or the destination is within the vehicle.
    """

    return [n for n in vehicles_schedule[vehicle] if int(n[0]) == node_type]


def get_next_occ_of_node(vehicles_schedule, vehicle, start_node, target_node):
    all_nodes = get_existing_nodes(vehicles_schedule, vehicle)
    idx_start_node = all_nodes.index(start_node)

    for idx in range(idx_start_node+1, len(all_nodes)):
        if int(all_nodes[idx][0]) == target_node:
            return all_nodes[idx]


def room_for_insertion_at_node(vehicles_schedule, vehicle, start_node, end_node=None):
    """
    Returns the available capacity for insertion at a node 'node'. The function essentially diminishes the capacity
    per vehicle (which is a parameter) with the amount of request which obey the following criteria:
    1) All requests boarding at 'node'
    2) All requests boarding between 'node' and the destination node (if the end node is specified)
    3) The requests boarding at any node before 'node', and also having a drop-off node after 'node'.
    """

    pax_from_prev_stops = count_inveh_pax_over_node(vehicles_schedule, vehicle, start_node)
    pax_boarding_until_end = count_boarding_pax_until_dest(vehicles_schedule, vehicle, start_node, end_node)

    return cap_per_veh - (pax_boarding_until_end + pax_from_prev_stops)


def count_boarding_pax_until_dest(vehicles_schedule, vehicle, start_node, end_node=None):
    """
    Function that returns
    """
    count = 0

    if not end_node:
        if boarding_pass_at_node(vehicles_schedule, vehicle, start_node):
            count += sum(
                [len(request_group) for request_group in vehicles_schedule[vehicle][start_node][1:]])
    else:
        for n in get_nodes_in_range(vehicles_schedule, vehicle, start_node, end_node, start_included=True):
            if boarding_pass_at_node(vehicles_schedule, vehicle, n):
                count += sum(
                    [len(request_group) for request_group in vehicles_schedule[vehicle][n][1:]])

    return count


def count_inveh_pax_over_node(vehicles_schedule, vehicle, start_node):
    """
    Function that counts the nb of passengers who enter the vehicle before 'start_node',
    and remain in the vehicle until after 'start_node'.
    """
    all_nodes = get_existing_nodes(vehicles_schedule, vehicle)
    index_curr_node = all_nodes.index(start_node)
    all_previous_nodes = all_nodes[:index_curr_node]

    inveh_pax = 0

    for start_node in all_previous_nodes:
        # print(boarding_pass_at_node(vehicles_schedule, vehicle, start_node))
        if boarding_pass_at_node(vehicles_schedule, vehicle, start_node):
            for group in vehicles_schedule[vehicle][start_node][1:]:
                group_origin, group_destination = get_od_from_request_group(group)
                destination_node = get_next_occ_of_node(vehicles_schedule, vehicle, all_nodes[0], group_destination)
                if destination_node not in all_previous_nodes:
                    inveh_pax += len(group)

    return inveh_pax


def locate_request_group_in_schedule(vehicles_schedule, request_group):
    """
    Function that returns the vehicle and the node at which a request group is located in the vehicle schedule.
    """
    for vehicle in vehicles_schedule:
        for node in vehicles_schedule[vehicle]:
            if request_group in vehicles_schedule[vehicle][node][1:]:
                return vehicle, node


def boarding_pass_at_node(vehicles_schedule, vehicle, node):
    return False if len(vehicles_schedule[vehicle][node]) <= 1 else True


def get_departure_time_at_node(vehicles_schedule, vehicle, node):
    return vehicles_schedule[vehicle][node][0]


def get_last_arrival(vehicle_schedule, vehicle):
    all_nodes = get_existing_nodes(vehicle_schedule, vehicle)
    return get_departure_time_at_node(vehicle_schedule, vehicle, all_nodes[-1]) \
        if not is_empty_vehicle_schedule(vehicle_schedule, vehicle) else 0.0


def is_empty_vehicle_schedule(vehicles_schedule, vehicle):
    return True if all([is_empty_stop(vehicles_schedule, vehicle, stop) for stop in vehicles_schedule[vehicle]]) \
        else False


def is_empty_stop(vehicles_schedule, vehicle, node):
    return True if len(vehicles_schedule[vehicle][node]) <= 1 else False


def get_pick_up_nodes_dest(vehicles_schedule, vehicle, node):
    all_previous_nodes = get_nodes_in_range(vehicles_schedule, vehicle, start_node=None, end_node=node)

    pick_up_nodes = []
    for n in all_previous_nodes:
        for request_group in vehicles_schedule[vehicle][n][1:]:
            o, d = get_od_from_request_group(request_group)
            if get_next_occ_of_node(vehicles_schedule, vehicle, n, d) == node:
                pick_up_nodes.append(n)

    return set(pick_up_nodes)