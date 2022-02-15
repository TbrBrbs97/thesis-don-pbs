# given the number of requests and the size of the network, initiate a set of vehicles
# one out of so many vehicles returns at 3, others go from 3 > 5;
import requests_generation


def is_empty_vehicle(solution, vehicle):
    if any([len(solution[vehicle][s]) for s in solution[vehicle]]) != 0:
        return False
    else:
        return True


def create_vehicle_schedule_templates(lst_of_all_requests, max_capacity):
    total_req_amount = len(lst_of_all_requests)
    minimum_service_amounts = int(total_req_amount / max_capacity)
    # assuming three services per vehicle:
    min_vehicles_req = int(minimum_service_amounts / 3)

    return min_vehicles_req
