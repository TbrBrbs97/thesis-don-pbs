# This is what a vehicle schedule will look like:

# e.g. {1: {stop 1: [dep_t, ((1,3), p_t, s_t), ...], stop 2: [dep_t, ((1,2), p_t, s_t), ((1,3), p_t, s_t), ...], ...}}
#    veh_nb   stop   dep_t

import copy

import vehicle_generation as vg
import requests_generation as rg


def count_requests(request_dict, od=None):
    count = 0

    if od is None:
        for k in request_dict.keys():
            count += len([j for i in request_dict[k] for j in i])
    else:
        count += len([j for i in request_dict[od] for j in i])

    return count


def occupy_available_capacity(request_dict, index_rg, rg, vehicles_dict, curr_veh, max_capacity,
                              round_trip, od, od_matrix, network_dim):
    # given the available capacity on a vehicle, add (at most, can be less!) that portion of passengers
    # from the request group and add the rest to the next request group from the same OD!

    # this function should encompass: available_capacity, add_pax_to_veh, update requests!

    curr_available_cap = available_capacity(vehicles_dict, curr_veh, max_capacity, od)

    if od == (network_dim[0], network_dim[1]):
        allowable_add = 10
    else:
        allowable_add = 100

    if curr_available_cap > 0:

        portion_to_add = rg[:min(len(rg), curr_available_cap, allowable_add)]
        # TODO: do we merge these with the next group or not?
        leftover_pax = rg[min(len(rg), curr_available_cap, allowable_add):]

        if len(portion_to_add) > 0:
            add_pax_to_veh(vehicles_dict, curr_veh, od, portion_to_add, od_matrix, network_dim, round_trip)
            update_request_dict(request_dict, od, index_rg, portion_to_add)

    else:
        return None


def select_request_group(request_dict, od):

    index = 0

    while len(request_dict[od][index]) == 0:
        if index < len(request_dict[od])-1:
            index += 1
        else:
            return None

    return index, request_dict[od][index]


def available_capacity(vehicles_dict, curr_veh, max_capacity, od):
    #this is defined on a link-basis between two nodes (e.g. between 1 and 2)
    # The occupied load between o and d are all passengers with origin: 1 and destination != 1
    occupied_spots = set(())

    # check for all stops beyond the starting position until the ending
    for r in range(od[0], od[1]):
        if len(vehicles_dict[curr_veh][r]) != 0:
            x = {j for i in vehicles_dict[curr_veh][r][1:] for j in i}
            occupied_spots = occupied_spots.union(x)

    return max_capacity - len(occupied_spots)


def add_pax_to_veh(vehicles_dict, curr_veh, od, portion_rg, od_matrix, network_dim, round_trip=None):

    # remember it might be possible to revisit a stop again (later implementation)
    # For now: first check if stop is already in the schedule; if it is, then add passengers to it

    if round_trip:
        if curr_veh in round_trip:
            last_stop = network_dim[2]
        else:
            last_stop = network_dim[1]
    else:
        last_stop = vg.get_last_stop(vehicles_dict, curr_veh)

    for s in range(1, last_stop+1):

        # add the portion of request group if s is within the range of OD & adjust the departure time

        if s in range(od[0], od[1]):
            # if no departure time is there yet, just add a dummy dep. time
            if vg.is_empty_stop(vehicles_dict, curr_veh, s):
                vehicles_dict[curr_veh][s].append(0)

            vehicles_dict[curr_veh][s].append(portion_rg)

        # adjust the dep time of all stops in the case they are visited!
        if not vg.is_empty_stop(vehicles_dict, curr_veh, s) and s != last_stop:
            vehicles_dict[curr_veh][s][0] = calc_dep_time(vehicles_dict, curr_veh, s, od_matrix, network_dim)

        elif s == last_stop:
            calc_arrival_times(vehicles_dict, curr_veh, s, od_matrix, network_dim)

    return None


def calc_dep_time(solution, service, stop, od_matrix, network_dim):
    # this is the desired pickup time of the last passenger in a group of requests

    imposed_dep_time_by_req_pt = max([rg.get_max_pick_time(group) for group in solution[service][stop][1:]])

    previous_stop, dep_time = vg.get_previous_stop_dep_time(solution, service, stop, network_dim)
    if (previous_stop, dep_time) != (1, 0):
        imposed_dep_time_by_prev_stop = dep_time + od_matrix[(previous_stop, stop)]
    else:
        imposed_dep_time_by_prev_stop = 0

    return round(max(imposed_dep_time_by_prev_stop, imposed_dep_time_by_req_pt), 2)


def calc_arrival_times(solution, service, last_stop, od_matrix, network_dim):

    previous_stop, prev_dep_time = vg.get_previous_stop_dep_time(solution, service, last_stop, network_dim)
    travel_time = od_matrix[previous_stop, last_stop]

    if vg.is_empty_stop(solution, service, last_stop):
        solution[service][last_stop].append(round(prev_dep_time + travel_time, 2))
    else:
        solution[service][last_stop][0] = round(prev_dep_time + travel_time, 2)


def update_request_dict(request_dict, od, index_rg, portion_rg):
    for p in portion_rg:
        request_dict[od][index_rg].remove(p)

    return None


def create_initial_solution(request_dict, start, end, network_dim,
                            current_veh, nb_of_vehicles, round_trip_veh,
                            max_capacity, od_matrix, vehicles_schedule=None):
    
    # given that WT is perceived more expensive than IVT, we aim to mix passengers with different destinations

    if vehicles_schedule is None:
        request_dict = copy.deepcopy(request_dict)
        vehicles_schedule = {}
        
    if count_requests(request_dict) == 0 or current_veh > nb_of_vehicles:
        return vehicles_schedule
    
    if current_veh not in vehicles_schedule.keys():
        vehicles_schedule[current_veh] = {}
        for s in range(1, network_dim[2]+1):
            # can be changed later, in order to make loops possible & revisiting stops
            # predefine the possible stopping places for each vehicle 1-->3
            vehicles_schedule[current_veh][s] = []

    #you always take the next first request in line > because you always delete request groups / change vehicles

    # this is the section we are currently investigating (two most outerward ends)

    od = start, end

    if select_request_group(request_dict, od) is not None:
        index_rg, rg = select_request_group(request_dict, od)
        occupy_available_capacity(request_dict, index_rg, rg, vehicles_schedule, current_veh, max_capacity, round_trip_veh, od, od_matrix, network_dim)

    # 5/2: updated this - the search should continue for every vehicle, regardless if the vehicle is deemed full at some point
    # there might be room elsewhere, so still check for instances backwards

    med = end - 1
    if start == med == network_dim[1]:

        #TODO: close the current schedule: adjust the departure time with OD-matrix + make it return to the depot
        #vehicles have a number + an available point in time + they either return to the depot directly OR via the other stops

        start, end = network_dim[0], network_dim[1]
        return create_initial_solution(request_dict, start, end, network_dim, current_veh,
                                       nb_of_vehicles, round_trip_veh, max_capacity, od_matrix, vehicles_schedule)

    elif start == med:

        #TODO: close the current schedule: adjust the departure time with OD-matrix + make it return to the depot
        #vehicles have a number + an available point in time + they either return to the depot directly OR via the other stops

        current_veh += 1

        if current_veh in round_trip_veh:
            start, end = network_dim[1], network_dim[2]
        else:
            start, end = network_dim[0], network_dim[1]

        return create_initial_solution(request_dict, start, end, network_dim, current_veh,
                                       nb_of_vehicles, round_trip_veh, max_capacity, od_matrix, vehicles_schedule)

    else:     #see if you can add requests in the backward direction
        od = med, end

        if not select_request_group(request_dict, od):
            index_rg, rg = select_request_group(request_dict, od)
            occupy_available_capacity(request_dict, index_rg, rg, vehicles_schedule, current_veh,
                                      max_capacity, round_trip_veh, od, od_matrix, network_dim)

        if count_requests(request_dict, (start, med)) != 0:
            return create_initial_solution(request_dict, start, med, network_dim, current_veh,
                                           nb_of_vehicles, round_trip_veh, max_capacity, od_matrix, vehicles_schedule)
        else:
            return create_initial_solution(request_dict, med, end, network_dim, current_veh,
                                           nb_of_vehicles, round_trip_veh, max_capacity, od_matrix, vehicles_schedule)

## Create vehicle indices, instead of services


def services_to_vehicles(solution, network_dim, od_matrix, max_services_per_veh=3):

    added_services = set(())
    new_solution = {}

    z = 0

    for v in range(0, len(solution.keys())):
        ser = 1
        i = 1

        key_v = index_to_key(solution, v)

        if len(solution[key_v]) != 0 and key_v not in added_services:
            # initiate the vehicle number: only goes up if a new service is able to start
            z += 1
            new_solution[(z, ser)] = solution[key_v]
            # also pay attention to the difference between roundtrip / non-roundtrip vehicles!
            while i < len(solution.keys())-1 and ser <= max_services_per_veh:
                # the vehicle arrival needs to be updated as another service is added to a schedule!

                # get the key for the next candidate in chain in the original solution
                next_possible_key = index_to_key(solution, i+1)

                if next_possible_key not in added_services:
                    if vg.get_vehicle_availability(new_solution, (z, ser), network_dim, od_matrix) \
                            < vg.get_vehicle_first_departure(solution, next_possible_key, network_dim):
                                #and (ser in round_trip_veh) == (i+1 in round_trip_veh):
                        new_solution[(z, ser+1)] = solution[next_possible_key]
                        # empty the original schedule so we know it has been added already
                        added_services.add(next_possible_key)
                        ser += 1
                i += 1
        added_services.add(key_v)

    return new_solution

# ADD TO GENERAL FUNCTIONS SCRIPT?


def index_to_key(dictionairy, index):
    # function that takes an index as an input and returns the corresponding key
    keys_list = list(dictionairy.keys())
    return keys_list[index]


def key_to_index(dictionairy, key):
    # function that takes a key as an input and returns the corresponding index
    keys_list = list(dictionairy.keys())
    k = 0
    while keys_list[k] != key:
        k += 1
    return k


def get_request_group_position(solution, request_group):
    for service in solution.keys():
        for stop in solution[service]:
            if stop != vg.get_last_stop(solution, service) and not vg.is_empty_stop(solution, service, stop):
                for group in solution[service][stop][1:]:
                    if any([x == y for x in group for y in request_group[1]]):
                        position = service, stop, solution[service][stop][1:].index(group)+1
                        return position




