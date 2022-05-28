import pandas as pd
import pickle
from pprint import PrettyPrinter, pprint

from requests import get_od_from_request_group

from vehicle import locate_request_group_in_schedule, is_empty_vehicle_schedule, \
    count_assigned_request_groups, room_for_insertion_at_node, get_insertion_possibilities, count_total_assigned_requests

from requests import count_requests, add_request_group_to_dict, count_requests_per_od

from static_operators import find_best_position_for_request_group, select_random_request_groups

from dynamic_operators import filter_dynamic_insertion_possibilities

from solution_construct import generate_initial_solution, static_optimization, \
    select_random_request_groups, init_fill_every_vehicle, \
    generate_dynamic_solution, iter_generate_initial_solution

from solution_evaluation import calc_request_group_waiting_time, calc_request_group_invehicle_time, \
    get_objective_function_val, generate_waiting_time_dict, generate_in_vehicle_time_dict, \
    generate_total_travel_time_dict, select_most_costly_request_groups, calc_total_vehicle_kilometers, sum_total_travel_time

from settings import network, lambdapeak, mupeak, demand_scenario, peak_duration, \
    req_max_cluster_time, cap_per_veh, nb_of_available_vehicles, \
    cost_matrix, grouped_requests, nb_of_available_vehicles, opt_time_lim, all_static_requests, \
    all_dynamic_requests, lead_time, steep_descent_intensity, degree_of_dynamism, \
    network_dim, distance_matrix, average_interstop_distance, requests_per_od, mean_demand, \
    count_groups, network_size, shuffle_threshold, depot, max_vehicle_ride_time

total_requests = count_requests(grouped_requests)
print(total_requests)
# print(count_requests_per_od(grouped_requests))
# print(max_vehicle_ride_time)

# print(grouped_requests)
# print(mean_demand)
# print(count_groups)
# print(requests_per_od)

# print(cost_matrix)
# print(network)
# print(average_interstop_distance)

## TEST LOAD REAL NETWORK

# sheet_lambda = 0
# sheet_mu = 1
# path_name = 'Data/Demand rates/DemandInputReal.xlsx'
# df_lambda = pd.read_excel(path_name, engine='openpyxl', sheet_name=sheet_lambda,header=0, index_col=(0,1,2), dtype=float)
# df_mu = pd.read_excel(path_name, engine='openpyxl', sheet_name=sheet_mu, header=0, index_col=(0,1,2), dtype=float)


## INITIAL SOLUTION

initial_solution = generate_initial_solution(network, grouped_requests,
                                             nb_of_available_veh=nb_of_available_vehicles,
                                             capacity=cap_per_veh, depot=depot)
print(count_total_assigned_requests(initial_solution))

for i in initial_solution:
    print('veh ', i, ': ', initial_solution[i])

print('objective func: ', get_objective_function_val(initial_solution, relative=False))
print('assigned ind. requests', count_total_assigned_requests(initial_solution))
print('assigned request groups', count_assigned_request_groups(initial_solution))

waiting_time = generate_waiting_time_dict(initial_solution)
in_veh_time = generate_in_vehicle_time_dict(initial_solution)

print('avg. waiting time: ', sum_total_travel_time(waiting_time))
print('avg. in-vehicle time: ', sum_total_travel_time(in_veh_time))

print('city requests avg. TT: ', get_objective_function_val(initial_solution, relative=True, direction='city'))
print('terminal requests avg. TT: ', get_objective_function_val(initial_solution, relative=True, direction='terminal'))

## OPTIMIZED STATIC SOLUTION

# optimized_solution, best_iteration = static_optimization(network, initial_solution,
#                                                          required_requests_per_it=steep_descent_intensity,
#                                                          time_limit=opt_time_lim, capacity=cap_per_veh, depot=depot)
# for i in optimized_solution:
#     print('veh ', i, ': ', optimized_solution[i])
# print('overall objective function: ', get_objective_function_val(optimized_solution, relative=False),
#       'at iteration: ', best_iteration)
# print('avg. travel time per passenger: ', get_objective_function_val(optimized_solution, relative=True))


# ## DYNAMIC SOLUTION
#
# if degree_of_dynamism > 0.0:
#     dynamic_initial_solution = generate_dynamic_solution(network, optimized_solution, all_dynamic_requests,
#                                                          lead_time=lead_time, peak_hour_duration=peak_duration,
#                                                          capacity=cap_per_veh, depot=depot)
#     for i in dynamic_initial_solution:
#         print('veh ', i, ': ', dynamic_initial_solution[i])
#     print('objective func: ', get_objective_function_val(dynamic_initial_solution, relative=False))
#     print('avg. travel time per passenger: ', get_objective_function_val(dynamic_initial_solution, relative=True))




