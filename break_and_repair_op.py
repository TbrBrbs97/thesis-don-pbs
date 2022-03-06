import requests_generation as rg
import solution_generation as sg
import vehicle_generation as vg
import numpy as np
import solution_evaluation as se

# perhaps create a 'dumpster' in which removed requests are put? Then create a Not-None return for removal functions


def remove_request_group(solution, service, request_group, od_matrix, network_dim):
    first_cut, end_cut = rg.get_od_from_request_group(request_group)
    old_departure_time = vg.get_stop_dep_time(solution, service, first_cut)

    # only retain values which do not correspond to the request_group removed
    for s in range(first_cut, end_cut):
        retained_requests = [[value] for group in
                             solution[service][s][1:] for value in group if value not in request_group]
        solution[service][s] = [solution[service][s][0], retained_requests]
        # if not a single request is retained for the stop, render the list empty
        if type(solution[service][s][0]) is np.float64 and len(solution[service][s][1]) == 0:
            solution[service][s] = []

    # check if the max pick up time is binding for the departure time at the stop
    if rg.get_max_pick_time(request_group) == old_departure_time and vg.is_empty_vehicle(solution, service) is False:
        # TODO: check if statement below still holds
        # correct the departure times at other stops (check if removing a request doesn't make departure time 'too early')
        # correct the departure times of other services of the same service
        update_dep_times(solution, service, (first_cut, end_cut), od_matrix, network_dim)
    elif vg.is_empty_vehicle(solution, service):
        update_service_sequence(solution, service, 'removal')

    return None


# TODO: Do we do the check for available capacity in the outer or inner function?
# If we do it in the outer functions, we can control which portion is 'sent' in as request group better
# so, then within this next function, we assume that the insertion is feasible!

def insert_request_group(solution, service, request_group, od_matrix, network_dim):
    first_ins, end_ins = rg.get_od_from_request_group(request_group)

    # original arrival, before addition:
    original_arrival = vg.get_vehicle_availability(solution, service, network_dim, od_matrix)
    previous_stop = sorted((list(vg.get_served_stops(solution, service))))[-2]
    original_pre_arrival = vg.get_stop_dep_time(solution, service, previous_stop)

    # add pax & update departure times at the current stop & at next stops
    sg.add_pax_to_veh(solution, service, (first_ins, end_ins), request_group)

    for s in range(first_ins, end_ins):
        # re-sort the requests according to pickup time
        solution[service][s][1:].sort(key=lambda x: rg.get_max_pick_time(x))

    # correct the vehicle arrival time
    last_stop = vg.get_last_stop(solution, service)
    previous_stop = sorted((list(vg.get_served_stops(solution, service))))[-2]
    solution[service][last_stop][0] = original_arrival + \
                                      vg.get_stop_dep_time(solution, service, previous_stop) - original_pre_arrival

    # correct the departure times of other services of the same vehicle
    dep_time_diff = vg.get_vehicle_availability(solution, service, network_dim, od_matrix) - original_arrival
    update_dep_times_next_services(solution, service, dep_time_diff)

    return None


def update_dep_times(solution, service, od, od_matrix, network_dim):
    # TODO: break it into two functions: backward constraint
    #  & forward adaptations > depending on whether you deal with insertion or deletion, you can call one or the other

    if len(solution[service][od[0]]) == 0:
        curr_stop = vg.get_first_stop(solution, service)
    else:
        curr_stop = od[0]

    candidate_dep_time = max([rg.get_max_pick_time(group) for group in solution[service][curr_stop][1:]])

    # you have to look at the previous non-empty (and thus visited stop!)

    # adapt dep time at the current stop, considering the lower bound set by departure time at the previous stop.
    # Make the distinction: if the removal is in the first stop,
    if curr_stop != network_dim[0] and curr_stop != vg.get_first_stop(solution, service):
        candidate_dep_time = max(vg.get_stop_dep_time(solution, service, curr_stop-1)) + od_matrix((curr_stop-1, curr_stop)
                                                                                               , candidate_dep_time)

    # if the stop where the removed passengers originate is the first stop, look at the previous service (if there is any)!
    elif service[1] != 1 and curr_stop != vg.get_first_stop(solution, service):
        previous_service_arr = vg.get_vehicle_availability(solution, (service[0], service[1]-1), network_dim, od_matrix)
        candidate_dep_time = max(candidate_dep_time, previous_service_arr)
    else:
        candidate_dep_time = candidate_dep_time

    # After calculating the difference and the backward check, apply the new candidate departure time
    # TODO: here we take the absolute difference, but check whether it could also work for insertion later with '+'!
    dep_time_diff = candidate_dep_time - vg.get_stop_dep_time(solution, service, curr_stop)
    solution[service][curr_stop][0] = candidate_dep_time

    # adapt forward departure times (i.e. at the next stops)
    next_stops = range(curr_stop+1, vg.get_last_stop(solution, service)+1)

    for stop in next_stops:
        if stop == vg.get_last_stop(solution, service):
            max_imposed_dep_time = vg.get_stop_dep_time(solution, service, stop)
            solution[service][stop][0] = max_imposed_dep_time + dep_time_diff
        else:
            max_imposed_dep_time = max([rg.get_max_pick_time(group) for group in solution[service][stop][1:]])
            # The future departure times are diminished, ONLY in the case that they are not constrained by
            # the departure times
            solution[service][stop][0] = max(solution[service][stop][0] + dep_time_diff, max_imposed_dep_time)

    # update the departure times of the next services of the same vehicle!
    update_dep_times_next_services(solution, service, dep_time_diff)

    return None


def update_dep_times_next_services(solution, service, dep_time_diff):
    for ser in vg.get_services_per_vehicle(solution, service)[service[1]:]:
        for stop in solution[ser]:
            max_imposed_dep_time = max([rg.get_max_pick_time(group) for group in solution[service][stop][1:]])
            # The future departure times are diminished, ONLY in the case that they are not constrained by
            # the departure times
            solution[service][stop][0] = max(solution[service][stop][0] + dep_time_diff, max_imposed_dep_time)
    return None


def update_service_sequence(solution, service, instance='removal'):
    # this function deletes a service from a vehicle
    # first: decide what the position of the service is within the vehicle

    if instance is 'removal':
        services_per_veh = vg.get_services_per_vehicle(solution, service[0])
        if len(services_per_veh) > 1:
            for k in services_per_veh:
                if k[1] > service[1]:
                    solution[(k[0], k[1]-1)] = solution[(k[0], k[1])]
                if k == services_per_veh[-1]:
                    del solution[k]
        else:
            return None
    # if instance is 'addition'


    return None


def is_feasible_insertion(solution, service, request_group):
    return None

    # Check feasibility of insertion! > i.e. some threshold on the max difference in pickup time?
    # Check occupancy!


def swap_req_between_veh(solution, service_1, service_2, request_group_1, request_group_2):
    return None


# check if request is reinserted correctly: i.e. it appears in the schedule for as long as the drop-off location
# has not been reached.

# adapt the departure times


def internal_stop_swap(solution, service, new_order):
    # swaps the order of the stops within a vehicle schedule.
    return None

