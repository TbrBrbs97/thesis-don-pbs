# This is what a vehicle schedule will look like:

# e.g. {1: {stop 1: [dep_t, ((1,3), p_t, s_t), ...], stop 2: [dep_t, ((1,2), p_t, s_t), ((1,3), p_t, s_t), ...], ...}}
#    veh_nb   stop   dep_t


def count_requests(request_dict, od=None):
    count = 0

    if od is None:
        for k in request_dict.keys():
            count += len([j for i in request_dict[k] for j in i])
    else:
        count += len([j for i in request_dict[od] for j in i])

    return count


def calc_dep_time(vehicles_dict, curr_veh, od, portion_rg):
    # this is the desired pickup time of the last passenger in a group of requests

    if portion_rg[-1][1] > vehicles_dict[curr_veh][od[0]][0]:
        return portion_rg[-1][1]
    else:
        return vehicles_dict[curr_veh][od[0]][0]


def occupy_available_capacity(request_dict, index_rg, rg, vehicles_dict, curr_veh, max_capacity, od):
    # given the available capacity on a vehicle, add (at most, can be less!) that portion of passengers
    # from the request group and add the rest to the next request group from the same OD!

    # TODO: add parameter - 'allowed to add' and by default make it very large, for (1,3) e.g. make is specific
    # this function should encompass: available_capacity, add_pax_to_veh, update requests!

    curr_available_cap = available_capacity(vehicles_dict, curr_veh, max_capacity, od)

    if od == (1, 3):
        allowable_add = 10
    else:
        allowable_add = 100

    if curr_available_cap > 0:

        portion_to_add = rg[:min(len(rg), curr_available_cap, allowable_add)]
        # TODO: do we merge these with the next group or not?
        leftover_pax = rg[min(len(rg), curr_available_cap, allowable_add):]

        if len(portion_to_add) > 0:
            add_pax_to_veh(vehicles_dict, curr_veh, od, portion_to_add)
            update_requests(request_dict, od, index_rg, portion_to_add)

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

    # this means passengers (1,3) will have to be mentioned to be present in stop 2 as well!
    # e.g. {1: {stop 1: [dep_t, ((1,3), p_t, s_t), ...], stop 2: [dep_t, ((1,2), p_t, s_t), ((1,3), p_t, s_t), ...], ...}}


def add_pax_to_veh(vehicles_dict, curr_veh, od, portion_rg):

    # remember it might be possible to revisit a stop again (later implementation)
    # For now: first check if stop is already in the schedule; if it is, then add passengers to it

    for s in range(od[0], od[1]):

        # if no departure time is there yet, just add a dummy dep. time
        if len(vehicles_dict[curr_veh][s]) == 0:
            vehicles_dict[curr_veh][s].append(0)

        # adjust the departure time and add the portion of request group
        vehicles_dict[curr_veh][s][0] = calc_dep_time(vehicles_dict, curr_veh, od, portion_rg)
        vehicles_dict[curr_veh][s].append(portion_rg)

    return None


def update_requests(request_dict, od, index_rg, portion_rg):
    for p in portion_rg:
        request_dict[od][index_rg].remove(p)

    return None


def create_initial_solution(request_dict, start, end, 
                            current_veh, nb_of_vehicles, max_capacity, vehicles_schedule=None):
    
    # given that WT is perceived more expensive than IVT, we aim to mix passengers with different destinations

    if vehicles_schedule is None:
        request_dict = request_dict.copy()
        vehicles_schedule = {}
        
    if count_requests(request_dict) == 0 or current_veh > nb_of_vehicles:
        return vehicles_schedule
    
    if current_veh not in vehicles_schedule.keys():
        # TODO: make it so that depending on the vehicle ID, there is a schedule template! > function that checks this
        vehicles_schedule[current_veh] = {}
        for s in range(1, end+1):
            # can be changed later, in order to make loops possible & revisiting stops
            # predefine the possible stopping places for each vehicle 1-->3
            vehicles_schedule[current_veh][s] = []

    #you always take the first request in line > because you always delete request groups / change vehicles

    # this is the section we are currently investigating (two most outerward ends)

    od = start, end

    if select_request_group(request_dict, od) is not None:
        index_rg, rg = select_request_group(request_dict, od)
        occupy_available_capacity(request_dict, index_rg, rg, vehicles_schedule, current_veh, max_capacity, od)

    # 5/2: updated this - the search should continue for every vehicle, regardless if the vehicle is deemed full at some point
    # there might be room elsewhere, so still check for instances backwards

    med = end - 1
    if start == med: # or occupy_available_capacity(request_dict, rg, vehicles_schedule, current_veh, max_capacity, od) is None:

        #TODO: close the current schedule: adjust the departure time with OD-matrix + make it return to the depot
        #vehicles have a number + an available point in time + they either return to the depot directly OR via the other stops

        current_veh += 1
        start, end = 1, 3
        return create_initial_solution(request_dict, start, end, current_veh,
                                       nb_of_vehicles, max_capacity, vehicles_schedule)
    else:     #see if you can add requests in the backward direction
        od = med, end

        if select_request_group(request_dict, od) is not None:
            index_rg, rg = select_request_group(request_dict, od)
            occupy_available_capacity(request_dict, index_rg, rg, vehicles_schedule, current_veh, max_capacity, od)

        if count_requests(request_dict, (start, med)) != 0:
            return create_initial_solution(request_dict, start, med, current_veh,
                                           nb_of_vehicles, max_capacity, vehicles_schedule)
        else:
            return create_initial_solution(request_dict, med, end, current_veh,
                                           nb_of_vehicles, max_capacity, vehicles_schedule)


def correct_dep_times(solution, od_matrix):

    solution = solution.copy()

    for v in solution.keys():
        stop_ids = list(solution[v].keys())
        for s in range(2, len(solution[v])):
            travel_time = od_matrix[(stop_ids[s-1], stop_ids[s])]
            solution[v][s][0] = solution[v][s-1][0] + travel_time
    return solution
