def count_requests(request_dict):
    count = 0
    for k in request_dict.keys():
        count += len([j for i in request_dict[k] for j in i])

    return count

def calc_dep_time(request_group):
    # this is the desired pickup time of the last passenger in a group of requests
    return request_group[-1][1]

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


def add_pax_to_veh(vehicles_dict, curr_veh, od, rg):
    dep_time = calc_dep_time(rg)
    # this may adding a stop to the vehicles schedule! >> but not necissarily!
    # remember it might be possible to revisit a stop again (later implementation)
    # For now: first check if stop is already in the schedule; if it is, then add passengers to it

    for s in range(od[0], od[1]):

        if len(vehicles_dict[curr_veh][s]) == 0:
            vehicles_dict[curr_veh][s].append(0)

        # adjust the departure time
        vehicles_dict[curr_veh][s][0] = dep_time

        vehicles_dict[curr_veh][s].append(rg)

        # adjust the departure time of the future stops! >> add (dep_time - curr_dep_t)

    return None


#TEST

#routes = {1: {1: [1.3783385157453578, [((1, 3), 0, 0), ((1, 3), 0.1403039226465128, 0), ((1, 3), 0.20978743783730414, 0), ((1, 3), 0.21631632923156086, 0), ((1, 3), 0.4281202641242935, 0), ((1, 3), 0.5071587541090863, 0), ((1, 3), 1.0027513055631039, 0), ((1, 3), 1.0863795908753289, 0), ((1, 3), 1.1665300400841745, 0), ((1, 3), 1.3783385157453578, 0)]], 2: [], 3: []}}

#Curr_veh = 1
#Max_capacity = 20
#OD = 1, 3

#available_capacity(routes, Curr_veh, Max_capacity, OD)
