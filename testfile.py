import numpy
import pandas as pd
import pickle
import numpy as np
import matplotlib.pyplot as plt
from pprint import PrettyPrinter, pprint

from requests import get_od_from_request_group

from vehicle import locate_request_group_in_schedule, is_empty_vehicle_schedule, \
    count_assigned_request_groups, room_for_insertion_at_node, get_insertion_possibilities, \
    count_total_assigned_requests, requests_per_node

from requests import count_requests, add_request_group_to_dict, count_requests_per_od

from static_operators import find_best_position_for_request_group, select_random_request_groups

from dynamic_operators import filter_dynamic_insertion_possibilities

from solution_construct import generate_initial_solution, static_optimization, \
    select_random_request_groups, init_fill_every_vehicle, \
    generate_dynamic_solution, iter_generate_initial_solution, disturb_2

from solution_evaluation import calc_request_group_waiting_time, calc_request_group_invehicle_time, \
    get_objective_function_val, generate_waiting_time_dict, generate_in_vehicle_time_dict, \
    generate_total_travel_time_dict, select_most_costly_request_groups, calc_total_vehicle_kilometers, sum_total_travel_time

from settings import network, lambdapeak, mupeak, demand_scenario, peak_duration, \
    req_max_cluster_time, cap_per_veh, nb_of_available_vehicles, \
    cost_matrix, grouped_requests, nb_of_available_vehicles, opt_time_lim, all_static_requests, \
    all_dynamic_requests, lead_time, steep_descent_intensity, degree_of_dynamism, \
    network_dim, distance_matrix, average_interstop_distance, requests_per_od, mean_demand, \
    count_groups, network_size, shuffle_threshold, depot, max_vehicle_ride_time, oneway_distance, oneway_duration, delta, \
    disturbance_ratio

# total_requests = count_requests(grouped_requests)
# print(total_requests)

# print(all_dynamic_requests)
# print(len(all_static_requests))

# print(all_static_requests)
# hist_data = [tup[0][2] for tup in all_dynamic_requests]
# n, bins, patches = plt.hist(x=hist_data, bins='auto', color='#0504aa',
#                             alpha=0.7, rwidth=0.85, density=False)
# plt.grid(axis='y', alpha=0.75)
# plt.xlabel('Value')
# plt.ylabel('Frequency')
# plt.title('Distribution of pick up times: Pi = 120 min.')
# maxfreq = n.max()
# # Set a clean upper y-axis limit.
# plt.ylim(ymax=maxfreq + 10)
# plt.show()

# print('oneway dist: ', oneway_distance)
# print('oneway dur: ', oneway_duration)
# print(count_requests_per_od(grouped_requests))
# print(max_vehicle_ride_time)

# print(np.mean([len(veh) for od in grouped_requests for veh in grouped_requests[od]]))
# print(mean_demand)
# print(count_groups)
# print(requests_per_od)

# print(cost_matrix)
# print(network)
# print(average_interstop_distance)

## INITIAL SOLUTION

initial_solution = generate_initial_solution(network, grouped_requests,
                                             nb_of_available_veh=nb_of_available_vehicles,
                                             capacity=cap_per_veh, depot=depot)
print(count_total_assigned_requests(initial_solution))

# for veh in initial_solution:
#     print('veh ', veh, ': ', initial_solution[veh])
#
print('objective func: ', get_objective_function_val(network, initial_solution, relative=False))
# print(requests_per_node(initial_solution))
# print('assigned ind. requests', count_total_assigned_requests(initial_solution))
# print('assigned request groups', count_assigned_request_groups(initial_solution))
#
# waiting_time = generate_waiting_time_dict(initial_solution)
# in_veh_time = generate_in_vehicle_time_dict(network, initial_solution)
#
# print('avg. waiting time: ', sum_total_travel_time(waiting_time))
# print('avg. in-vehicle time: ', sum_total_travel_time(in_veh_time))
#
# print('city requests avg. TT: ', get_objective_function_val(network, initial_solution, relative=True, direction='city'))
# print('terminal requests avg. TT: ', get_objective_function_val(network, initial_solution, relative=True, direction='terminal'))
#
# print('in-advance TT:', get_objective_function_val(network, initial_solution, relative=False, direction='all', dynamic_filter=False))
# print('real-time TT:', get_objective_function_val(network, initial_solution, relative=False, direction='all', dynamic_filter=True))
#
# # disturb_2(network, initial_solution, disturbance=disturbance_ratio)
#
## OPTIMIZED STATIC SOLUTION

# optimized_solution, best_iteration = static_optimization(network, initial_solution,
#                                                          required_requests_per_it=steep_descent_intensity,
#                                                          time_limit=opt_time_lim, capacity=cap_per_veh, depot=depot)
# for veh in optimized_solution:
#     print('veh ', veh, ': ', optimized_solution[veh])
# print('overall objective function: ', get_objective_function_val(network, optimized_solution, relative=False),
#       'at iteration: ', best_iteration)
# print('avg. travel time per passenger: ', get_objective_function_val(network, optimized_solution, relative=True))
#
# print('objective func: ', get_objective_function_val(network, optimized_solution, relative=False))
# print('assigned ind. requests', count_total_assigned_requests(optimized_solution))
# print('assigned request groups', count_assigned_request_groups(optimized_solution))
# #
# waiting_time = generate_waiting_time_dict(optimized_solution)
# in_veh_time = generate_in_vehicle_time_dict(network, optimized_solution)
#
# print('avg. waiting time: ', sum_total_travel_time(waiting_time))
# print('avg. in-vehicle time: ', sum_total_travel_time(in_veh_time))
#
# print('city requests avg. TT: ', get_objective_function_val(network, optimized_solution, relative=True, direction='city'))
# print('terminal requests avg. TT: ', get_objective_function_val(network, optimized_solution, relative=True, direction='terminal'))
#
# print('in-advance TT:', get_objective_function_val(network, optimized_solution, relative=False, direction='all', dynamic_filter=False))
# print('real-time TT:', get_objective_function_val(network, optimized_solution, relative=False, direction='all', dynamic_filter=True))
#


## DYNAMIC SOLUTION

# if degree_of_dynamism > 0.0:
#     dynamic_initial_solution = generate_dynamic_solution(network, optimized_solution, all_dynamic_requests,
#                                                          lead_time=lead_time, peak_hour_duration=peak_duration,
#                                                          capacity=cap_per_veh, depot=depot, delta=delta)
#     for veh in dynamic_initial_solution:
#         print('veh ', veh, ': ', dynamic_initial_solution[veh])
#     print('objective func: ', get_objective_function_val(network, dynamic_initial_solution, relative=False))
#     print('avg. travel time per passenger: ', get_objective_function_val(network, dynamic_initial_solution, relative=True))
#
#     print('in-advance TT:', get_objective_function_val(network, dynamic_initial_solution, relative=False, direction='all', dynamic_filter=False))
#     print('real-time TT:', get_objective_function_val(network, dynamic_initial_solution, relative=False, direction='all', dynamic_filter=True))
#
#     print('in-advance travellers', count_total_assigned_requests(dynamic_initial_solution, dynamic=False))
#     print('real-time travellers', count_total_assigned_requests(dynamic_initial_solution, dynamic=True))

