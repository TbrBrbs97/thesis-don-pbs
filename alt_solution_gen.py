import random
import copy

from requests_generation import count_requests, get_od_from_request_group, get_max_pick_time
from solution_generation import available_capacity

from parameters import network_dim, cap_per_veh, cost_matrix, nb_of_required_ser


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
        candidate_vehicle = find_best_vehicle_for_request_group(vehicles_schedule, request_group)
        best_position_within_veh = \
            find_best_position_within_vehicle(vehicles_schedule, request_group, candidate_vehicle)


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


def find_best_vehicle_for_request_group(vehicle_schedule, request_group, current_vehicle=1, best_vehicle_so_far=None):
    '''
    Function that returns the best possible position in the schedule for insertion,
    taking into account capacity constraints & the marginal cost of insertion
    (detour).

    TODO: make this a recursive function: call until start_vehicle = nb_of_vehicles
    TODO: evaluate waiting time & travel time incremement per case

    # TODO:
    #   - First, you look for best vehicle - difference dep.time & pick-up OR closest stop
    #   - Second, you find the exact position within the chosen vehicle

    '''
    if best_vehicle_so_far is None:
        best_vehicle_so_far = 1

    o, d  = get_od_from_request_group(request_group)
    request_group_max_pt = get_max_pick_time(request_group)

    if current_vehicle > nb_of_required_ser:
        return vehicle_schedule

    if arc_in_vehicle(vehicle_schedule, current_vehicle, (o, d)) == (o, d) and \
            remaining_capacity(vehicle_schedule, current_vehicle, (o, d)) > 0:
        # the following function needs to know which portion of the arc is within the vehicle
        matching_score = calculate_matching_score(vehicle_schedule, current_vehicle, (o, d))
        best_vehicle_so_far = current_vehicle,  matching_score
        # matching score is on the basis of the dep_time difference with the origin in this case

    # if o in schedule + capacity left in between o and the next stop:
        # here
        # add the request group at o and make the vehicle detour via d, before going to the next
        # if solution is better:
            # best_insertion_so_far = vehicle, position, score (=dep_time_difference)
    # if d in schedule + capacity left in between the previous stop and d:
        # add the request between the previous stop and d and make detour via o
    # else: > if neither o or d are in the schedule
        # if the dep time at o < the dep at the starting stop + driving time, add it before
        # in the case o > dep_t at the last stop + driving time, chain the arc in the end

    current_vehicle += 1
    return find_best_vehicle_for_request_group(vehicle_schedule, request_group, current_vehicle, best_vehicle_so_far)


def arc_in_vehicle(vehicle_schedule, current_vehicle, od_tup):
    return None


def find_best_position_within_vehicle(vehicle_schedule, request_group, vehicle):
    return None


def insert_request_group(vehicles_schedule, request_group, vehicle, position):
    return None


def get_existing_arcs(vehicles_schedule, service):
    '''
    Function that returns a list of the already present arcs in the vehicle schedule, created
    by the pick-up and drop-off of passengers.
    '''

    nodes = list(vehicles_schedule[service].keys())
    return [(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)]


def remaining_capacity(vehicle_schedule, service, arc):
    '''
    Returns the available capacity on a given arc,
    taken into account the number of available seates parameter
    '''
    # this is defined on a link-basis between two nodes (e.g. between 1 and 2)
    # The occupied load between o and d are all passengers with origin: 1 and destination != 1
    occupied_spots = set(())

    # check for all stops beyond the starting position until the ending
    for a in range(arc[0], arc[1]):
        if len(vehicle_schedule[service][a]) != 0:
            x = {j for i in vehicle_schedule[service][a][1:] for j in i}
            occupied_spots = occupied_spots.union(x)

    return cap_per_veh - len(occupied_spots)


def calculate_matching_score(vehicle_schedule, current_vehicle, od_tup):
    matching_score = 0
    return matching_score