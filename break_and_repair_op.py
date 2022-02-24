import requests_generation as rg
import solution_generation as sg


def remove_request_group(solution, vehicle, request_group):
    first_cut, end_cut = rg.get_od_from_request_group(request_group)

    for s in range(first_cut, end_cut):
        solution[vehicle][s].remove([request_group])

    # update departure times at the current stop (only if the latest request group was removed!)
    # correct the departure times at other stops (check if removing a request doesn't make departure time 'too early')
    # correct the departure times of other services of the same vehicle

    return None


# TODO: Do we do the check for available capacity in the outer or inner function?
# If we do it in the outer functions, we can control which portion is 'sent' in as request group better
# so, then within this next function, we assume that the insertion is feasible!

def insert_request_group(solution, vehicle, request_group):
    od = rg.get_od_from_request_group(request_group)
    sg.add_pax_to_veh(solution, vehicle, od, request_group)

    return None

    # update departure times at the current stop (only if the latest request group was removed!)
    # correct the departure times at other stops (check if adding a request doesn't make departure time 'too early')
    # correct the departure times of other services of the same vehicle


def is_feasible_insertion(solution, vehicle, request_group):
    return None

    # Check feasibility of insertion! > i.e. some threshold on the max difference in pickup time?


def swap_req_between_veh(solution, vehicle_1, vehicle_2, request_group_1, request_group_2):
    return None


# check if request is reinserted correctly: i.e. it appears in the schedule for as long as the drop-off location
# has not been reached.

# adapt the departure times


def internal_stop_swap(solution, vehicle, new_order):
    # swaps the order of the stops within a vehicle schedule.
    return None

# find inspiration in papers