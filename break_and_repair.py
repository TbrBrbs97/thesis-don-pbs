import numpy as np
import copy

from vehicle import locate_request_group_in_schedule, get_departure_time_at_node

from requests import get_od_from_request_group

from parameters import cost_matrix, cap_per_veh

# perhaps create a 'dumpster' in which removed requests are put? Then create a Not-None return for removal functions


def remove_request_group(vehicles_schedule, request_group):
    vehicle, node = locate_request_group_in_schedule(vehicles_schedule, request_group)
    o, d = get_od_from_request_group(request_group)
    old_departure_time = get_departure_time_at_node(vehicles_schedule, vehicle, node)

    # TODO:
    #   You will need to not only delete the stop where passenger get on the bus,
    #   but also the next occurence of the drop-off node if this drop-off node
    #   only serves the passengers who were just removed.
    #   >> So write a function that can detect whether this is such a stop.

    # only retain values which do not correspond to the request_group removed
    for s in range(first_cut, end_cut):
        retained_requests = [value for group in
                             vehicles_schedule[vehicle][s][1:] for value in group if value not in request_group]
        vehicles_schedule[service][s] = [vehicles_schedule[service][s][0], retained_requests]
        # if not a single request is retained for the stop, render the list empty
        # or vehicles_schedule[service][s][0] == 0.0)
        if type(vehicles_schedule[service][s][0]) is np.float64 and len(vehicles_schedule[service][s][1]) == 0:
            vehicles_schedule[service][s] = []

    # check if the max pick up time is binding for the departure time at the stop
    if rg.get_max_pick_time(request_group) == old_departure_time and vg.is_empty_vehicle(vehicles_schedule, service) is False:
        # TODO: check if statement below still holds
        # correct the departure times at other stops (check if removing a request doesn't make departure time 'too early')
        # correct the departure times of other services of the same service
        update_dep_times(vehicles_schedule, service, (first_cut, end_cut))
    elif vg.is_empty_vehicle(vehicles_schedule, service):
        update_service_sequence(vehicles_schedule, service, 'removal')

    return None


def insert_request_group(solution, service, request_group):
    first_ins, end_ins = rg.get_od_from_request_group(request_group)

    # original arrival, before addition:
    original_arrival = vg.get_vehicle_availability(solution, service, network_dim, od_matrix)

    # add pax & update departure times at the current stop & at next stops
    sg.add_pax_to_veh(solution, service, (first_ins, end_ins), request_group, od_matrix, network_dim)

    # TODO: sorting does not work!
    for s in range(first_ins, end_ins):
        # re-sort the requests according to pickup time
        solution[service][s][1:].sort(key=lambda x: rg.get_max_pick_time(x))

    # correct the departure times of other services of the same vehicle
    dep_time_diff = vg.get_vehicle_availability(solution, service, network_dim, od_matrix) - original_arrival
    update_dep_times_next_services(solution, service, dep_time_diff)

    return None


def update_dep_times(solution, service, od):

    if len(solution[service][od[0]]) == 0:
        curr_stop = vg.get_first_stop(solution, service)
    else:
        curr_stop = od[0]

    candidate_dep_time = max([rg.get_max_pick_time(group) for group in solution[service][curr_stop][1:]])

    # you have to look at the previous non-empty (and thus visited stop!)

    # adapt dep time at the current stop, considering the lower bound set by departure time at the previous stop.
    # Make the distinction: if the removal is in the first stop,
    if curr_stop != network_dim[0] and curr_stop != vg.get_first_stop(solution, service):
        candidate_dep_time = max(vg.get_stop_dep_time(solution, service, curr_stop-1)) + od_matrix((curr_stop-1, curr_stop), candidate_dep_time)

    # if the stop where the removed passengers originate is the first stop, look at the previous service (if there is any)!
    elif service[1] != 1 and curr_stop != vg.get_first_stop(solution, service):
        previous_service_arr = vg.get_vehicle_availability(solution, (service[0], service[1]-1), network_dim, od_matrix)
        candidate_dep_time = max(candidate_dep_time, previous_service_arr)
    else:
        candidate_dep_time = candidate_dep_time

    # After calculating the difference and the backward check, apply the new candidate departure time
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
    #TODO: if  is 'addition'

    return None


def single_most_costly_request(solution, attempts_so_far=None):
    # function that returns the request with the highest opportunity cost and its position.

    if attempts_so_far is None:
        attempts_so_far = []

    most_expensive_so_far = None

    for service in solution:
        for stop in solution[service]:
            if stop != vg.get_last_stop(solution, service) and not vg.is_empty_stop(solution, service, stop):
                for group in solution[service][stop][1:]:
                    if group not in attempts_so_far and rg.get_od_from_request_group(group)[0] == stop:
                        temp_solution = copy.deepcopy(solution)

                        original_obj_func_val = se.get_objective_function_val(solution)
                        remove_request_group(temp_solution, group)
                        new_obj_func_val = se.get_objective_function_val(temp_solution)

                        delta_obj_func_val = round((original_obj_func_val - new_obj_func_val) / len(group), 2)

                        if most_expensive_so_far is None or delta_obj_func_val > most_expensive_so_far[2]:
                            most_expensive_so_far = service, group, delta_obj_func_val
                            attempts_so_far.append(group)

    return most_expensive_so_far


def list_most_costly_requests(solution, selected_amount=1, excluded_requests=None, results=None):

    if results is None:
        results = []

    if excluded_requests is None:
        excluded_requests = []

    if selected_amount == 1:
        selected_request = single_most_costly_request(solution, excluded_requests)
        results.append(selected_request)
        return results

    else:
        selected_request = single_most_costly_request(solution, excluded_requests)
        results.append(selected_request)
        excluded_requests.append(selected_request)
        selected_amount -= 1
        return list_most_costly_requests(solution, selected_amount, excluded_requests, results)


def find_best_insertion(solution, request_group, excluded_insertion=None, start=0):
    '''
    Return the best position (service) to insert a request.
    Function looks for starting stop with departure time which is closest to
    The idea is that inserting requests in that place will be the least disruptive,
    to all next requests as well.

    The parameter excluded insertion allows you to forbid a certain position for insertion
    (e.g. the previous position the request was in). But by default, it is not given.
    >> excluded insertion needs to be a tuple of format:  (service, stop)

    Note: this functions assumes there is room for insertion!! >> you have to check whether that
    is true in an outer function!

    '''

    reference_pickup_time = rg.get_max_pick_time(request_group)
    pickup_node = rg.get_od_from_request_group(request_group)[0]

    closest_match_so_far = None

    to_be_checked_services = list(solution.keys())[start:]
    solution = {k: solution[k] for k in to_be_checked_services}

    for service in solution:
        for stop in solution[service]:
            # stop can be empty as well, but it has to be the pickup_node
            if stop != vg.get_last_stop(solution, service) and stop == pickup_node:
                if excluded_insertion is None or (service, stop) != excluded_insertion:
                    dep_time = vg.get_stop_dep_time(solution, service, stop)
                    delta_dep_time = round(abs(dep_time - reference_pickup_time), 2)
                    if not closest_match_so_far or delta_dep_time < closest_match_so_far[1]:
                            #or vg.is_empty_stop(solution, service, stop):
                        closest_match_so_far = (service, stop), delta_dep_time

    return closest_match_so_far

    # Check feasibility of insertion! > i.e. some threshold on the max difference in pickup time?
    # Check occupancy!


def find_first_available_best_insertion(solution, request_group, excluded_insertions, start=0):
    '''
    Function that, given a request group, finds the best insertion in a vehicle where there
    is still available capacity!

    '''
    od = rg.get_od_from_request_group(request_group)
    # Running the function below hardly makes sense if it is already removed from the schedule
    #curr_pos = sg.get_request_group_position(solution, request_group)[0]

    best_insertion_so_far = find_best_insertion(solution, request_group, excluded_insertions, start)
    candidate_service = best_insertion_so_far[0][0]

    if sg.available_capacity(solution, candidate_service, cap_per_veh, od) >= len(request_group):
        return best_insertion_so_far
    else:
        # the previously checked service is not eligable, due to the capacity constraint
        excluded_insertions.append(candidate_service)
        start += 1
        return find_first_available_best_insertion(solution, request_group, excluded_insertions, start)


def get_random_requests(solution, nb_of_requests, excluded_requests=None):
    '''
    Function that returns the position 'number_of_requests' amount of requests, which are not
    in excluded requests.
    '''
    return None


