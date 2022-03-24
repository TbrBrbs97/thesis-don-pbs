import requests_generation as rg

from parameters import cap_per_veh, req_max_cluster_time, cost_matrix, network_dim


def is_empty_vehicle(solution, vehicle):
    if all([is_empty_stop(solution, vehicle, stop) for stop in solution[vehicle] if stop < get_last_stop(solution, vehicle)]):
        return True
    else:
        return False


def is_empty_stop(solution, vehicle, stop):
    if len(solution[vehicle][stop]) == 0:
        return True
    else:
        return False


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


