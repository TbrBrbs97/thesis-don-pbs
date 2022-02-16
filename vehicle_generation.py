# given the number of requests and the size of the network, initiate a set of vehicles
# one out of so many vehicles returns at 3, others go from 3 > 5;
import requests_generation as rg
import network_generation as ng


def is_empty_vehicle(solution, vehicle):
    if any([len(solution[vehicle][s]) for s in solution[vehicle]]) != 0:
        return False
    else:
        return True


def create_vehicle_schedule_templates(lst_of_all_requests, veh_capacity, network):
    total_req_amount = len(lst_of_all_requests)
    # assuming three services per vehicle:
    min_vehicles_req = int((total_req_amount / veh_capacity)/3)

    template_schedules = {}
    network_boundaries = ng.get_network_boundaries(network)

    # TODO: create exception vehicles to the start-end rule (e.g. the ones that drive 1 > 5)
    # because now, all of them drive 1 > 5
    for v in range(1, min_vehicles_req+1):
        template_schedules[v] = (network_boundaries, {s: [] for s in range(1, network_boundaries[2]+1)})

    return template_schedules
