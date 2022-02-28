# given the number of requests and the size of the network, initiate a set of vehicles
# one out of so many vehicles returns at 3, others go from 3 > 5;
import requests_generation as rg
import network_generation as ng


def is_empty_vehicle(solution, vehicle):
    if any([len(solution[vehicle][s]) for s in solution[vehicle]]) != 0:
        return False
    else:
        return True


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
    if stop in solution[service].keys():
        if len(solution[service][stop]) != 0:
            return solution[service][stop][0]
    else:
        return None


def get_first_stop(solution, service):
    stop = 1

    while stop <= len(solution[service]):
        if len(solution[service][stop]) != 0:
            return stop
        stop += 1


def get_last_stop(solution, service):
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


#UNUSED FOR NOW
def get_vehicle_key_from_value(solution, value):
    for key in solution:
        if all(solution[key]) == value:
            return key