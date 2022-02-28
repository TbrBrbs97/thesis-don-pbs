import requests_generation as rg
import solution_generation as sg
import vehicle_generation as vg
import solution_evaluation as se

# perhaps create a 'dumpster' in which removed requests are put? Then create a Not-None return for removal functions


def remove_request_group(solution, service, request_group, od_matrix, network_dim):
    first_cut, end_cut = rg.get_od_from_request_group(request_group)

    # only retain values which do not correspond to the request_group removed
    for s in range(first_cut, end_cut):
        retained_requests = [[value] for group in
                             solution[service][s][1:] for value in group if value not in request_group]
        solution[service][s] = [solution[service][s][0], retained_requests]

    if rg.get_max_pick_time(request_group) == vg.get_stop_dep_time(solution, service, first_cut):
        # TODO: check if this is still needed
        # correct the departure times at other stops (check if removing a request doesn't make departure time 'too early')
        # correct the departure times of other services of the same service
        update_dep_times(solution, service, (first_cut, end_cut), od_matrix, network_dim)

    return None


# TODO: Do we do the check for available capacity in the outer or inner function?
# If we do it in the outer functions, we can control which portion is 'sent' in as request group better
# so, then within this next function, we assume that the insertion is feasible!

def insert_request_group(solution, service, request_group):
    od = rg.get_od_from_request_group(request_group)
    sg.add_pax_to_veh(solution, service, od, request_group)

    return None

    # sort the requests according to pickup time?
    # update departure times at the current stop (only if the latest request group was removed!)
    # correct the departure times at other stops (check if adding a request doesn't make departure time 'too early')
    # correct the departure times of other services of the same service


def update_dep_times(solution, service, od, od_matrix, network_dim):
    candidate_dep_time = max([rg.get_max_pick_time(group) for group in solution[service][od[0]][1:]])

    # adapt dep time at the current stop, considering the lower bound set by departure time at the previous stop.
    # Make the distinction: if the removal is in the first stop,
    if od[0] != network_dim[0]:
        candidate_dep_time = max(vg.get_stop_dep_time(solution, service, od[0]-1)) + od_matrix((od[0]-1, od[0])
                                                                                               , candidate_dep_time)
    # if the stop where the removed passengers originate is the first stop, look at the previous service (if there is any)!
    elif service[1] != 1 and od[0] == network_dim[0]:
        previous_service_arr = vg.get_vehicle_availability(solution, (service[0], service[1]-1), network_dim, od_matrix)
        candidate_dep_time = max(candidate_dep_time, previous_service_arr)
    # if it is the first service and
    else:
        candidate_dep_time = candidate_dep_time

    dep_time_diff = candidate_dep_time - vg.get_stop_dep_time(solution, service, od[0])

    # adapt forward departure times (i.e. at the next stops)
    next_stops = range(od[0], vg.get_last_stop(solution, service)+1)

    for stop in next_stops:
        max_imposed_dep_time = max([rg.get_max_pick_time(group) for group in solution[service][stop][1:]])
        # The future departure times are diminished, ONLY in the case that they are not constrained by
        # the departure times
        solution[service][stop][0] = max(solution[service][stop][0]-dep_time_diff, max_imposed_dep_time)

    # update the departure times of the next services of the same vehicle!
    last_service = vg.get_services_per_vehicle(solution, service)
    current_service = service[1]

    solution[service][od[0]][0] = candidate_dep_time

    return None




def is_feasible_insertion(solution, service, request_group):
    return None

    # Check feasibility of insertion! > i.e. some threshold on the max difference in pickup time?


def swap_req_between_veh(solution, service_1, service_2, request_group_1, request_group_2):
    return None


# check if request is reinserted correctly: i.e. it appears in the schedule for as long as the drop-off location
# has not been reached.

# adapt the departure times


def internal_stop_swap(solution, service, new_order):
    # swaps the order of the stops within a vehicle schedule.
    return None

