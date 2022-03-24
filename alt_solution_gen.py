import random
import copy

from requests_generation import count_requests, get_od_from_request_group, get_max_pick_time
from solution_generation import available_capacity

from parameters import network_dim, cap_per_veh, cost_matrix


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
        insert_in_best_position(vehicles_schedule, request_group)
        # try to insert a request in the current position (find_closest_match?)
        # make this a seperate function

    # recursive part
    # remove the request group from the request dictionairy
    # return alt_create_initial_solution(requests_dict, current_service, nb_of_available_veh, vehicles_schedule)

# if no spot in the current veh, or current veh > max_tour_length:
    # return solution with new vehicle


def init_fill_every_vehicle(request_dict, nb_of_available_veh):
    '''
    Function that fills every vehicle with a request group to start.
    Standard, node ids are multiplied with a 1000 in order to accomodate
    earlier occurences & later occurences of stops in a schedule
    ( respectively then /10 or *10 for the next occurence)
    '''
    vehicles_schedule = dict()

    for v in range(1, nb_of_available_veh+1):
        request_group = pop_request(request_dict)
        o, d = get_od_from_request_group(request_group)
        pt = get_max_pick_time(request_group)

        vehicles_schedule[v] = dict()
        vehicles_schedule[v][str(o)+',0'] = [pt, request_group]
        vehicles_schedule[v][str(d)+',0'] = [pt + cost_matrix[(o, d)]]

        request_dict[(o, d)].remove(request_group)

    return vehicles_schedule


def pop_request(request_dictionairy):
    '''
    Function that returns a random request group from the request dictionairy
    '''

    random_od_pair = random.choice(list(request_dictionairy))
    while count_requests(request_dictionairy, random_od_pair) == 0:
        random_od_pair = random.choice(list(request_dictionairy))

    return random.choice(request_dictionairy[random_od_pair])


def find_best_insertion(vehicle_schedule, request_group, start_vehicle=1):
    '''
    Function that returns the best possible position in the schedule for insertion,
    taking into account capacity constraints & the marginal cost of insertion
    (detour).

    TODO: make this a recursive function: call until start_vehicle = nb_of_vehicles
    '''

    best_insertion_so_far = None

    for service in vehicle_schedule:
        # 1: 1, 2, 6, 2, ..., 4,   >> (1, 2), (2, 3), (3, 4), (4, 6)
        current_arcs = get_existing_arcs(vehicle_schedule, service)

        # for the arcs where there is capacity left:
            # 1. check if the (o,d) (= also an arc) of the current request group for the current vehicle matches
            # with any of these arcs >> if so, try to insert here. Replace best_insertion_so_far if it is None or if it
            # is a better position than the previous one.

            # 2. Try to insert in between any arc combination where there is capacity left. Replace best_insertion_so_far
            # if it is None or if it is a better position than the previous one.

        # TODO:
        #  - First, you look for best vehicle - difference dep.time & pick-up OR closest stop
        #  - Second, you find the exact position within the chosen vehicle

        # elif there is no capacity left in between existing arcs + secondary condition; departure time is before 60 min.
            # try to add in chain to the existing arcs

    # if no feasible insertion was found in the current schedule (i.e. best_insertion_so_far remains None),
    # add a new service/vehicle to the schedule and insert the request group there.


def insert_request_group(vehicles_schedule, request_group, position):
    return None


def get_existing_arcs(vehicles_schedule, service):
    '''
    Function that returns a list of the already present arcs in the vehicle schedule, created
    by the pick-up and drop-off of passengers.
    '''

    nodes = list(vehicles_schedule[service].keys())
    return [(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)]