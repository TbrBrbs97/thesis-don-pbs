import pandas as pd
import pickle
from pprint import PrettyPrinter, pprint

from requests import get_od_from_request_group

from vehicle import locate_request_group_in_schedule, is_empty_vehicle_schedule, \
    count_assigned_request_groups, count_total_assigned_requests, room_for_insertion_at_node, get_insertion_possibilities

from requests import count_requests, add_request_group_to_dict

from static_operators import remove_request_group, find_best_position_for_request_group, select_random_request_groups

from dynamic_operators import filter_dynamic_insertion_possibilities

from solution_construct import generate_initial_solution, static_optimization, \
    disturb_solution, select_random_request_groups, init_fill_every_vehicle, \
    generate_dynamic_solution, iter_generate_initial_solution

from solution_evaluation import calc_request_group_waiting_time, calc_request_group_invehicle_time, \
    get_objective_function_val, generate_waiting_time_dict, generate_in_vehicle_time_dict, \
    generate_total_travel_time_dict, select_most_costly_request_groups

from parameters import network, lambdapeak, mupeak, demand_scenario, peak_duration, \
    req_max_cluster_time, cap_per_veh, nb_of_available_vehicles, \
    cost_matrix, grouped_requests, nb_of_available_vehicles, opt_time_lim, all_static_requests, \
    all_dynamic_requests, lead_time, steep_descent_intensity, degree_of_dynamism, \
    network_dim, distance_matrix, average_interstop_distance, requests_per_od, mean_demand, count_groups, network_size


# import cProfile, pstats, io
# pr = cProfile.Profile()
# pr.enable()

total_requests = count_requests(grouped_requests)
# print(grouped_requests)
# print(mean_demand)
# print(count_groups)
# print(total_requests)
# print(cost_matrix)
# print(network)
# print(average_interstop_distance)


## INITIAL SOLUTION

initial_solution = generate_initial_solution(grouped_requests)
print('objective func: ', get_objective_function_val(initial_solution, relative=False))
print(count_total_assigned_requests(initial_solution))

for i in initial_solution:
    print('veh ', i, ': ', initial_solution[i])

request_group_test = [((8, 15), 34.96, 0), ((8, 15), 35.55, 0), ((8, 15), 38.8, 0)]
print('the cost of this request group: ', calc_request_group_invehicle_time(initial_solution, request_group_test)+
      calc_request_group_waiting_time(initial_solution, request_group_test))


# test evaluation
# mcr = select_most_costly_request_groups(initial_solution, required_amount=steep_descent_intensity)
# print('the cost of this request group: ', calc_request_group_invehicle_time(initial_solution, mcr[0])+
#       calc_request_group_waiting_time(initial_solution, mcr[0]))
# remove_request_group(initial_solution, mcr[0])
# print(mcr)
# print('objective func: ', get_objective_function_val(initial_solution))


## OPTIMIZED STATIC SOLUTION

optimized_solution = static_optimization(initial_solution, required_requests_per_it=steep_descent_intensity,
                                         time_limit=opt_time_lim)
for i in optimized_solution:
    print('veh ', i, ': ', optimized_solution[i])
print('overal objective function: ', get_objective_function_val(optimized_solution, relative=False))
print('avg. travel time per passenger: ', get_objective_function_val(optimized_solution, relative=True))

# ## DYNAMIC SOLUTION
#
# if degree_of_dynamism > 0.0:
#     dynamic_initial_solution = generate_dynamic_solution(optimized_solution, all_dynamic_requests,
#                                                          lead_time=lead_time, peak_hour_duration=peak_duration)
#     for i in dynamic_initial_solution:
#         print('veh ', i, ': ', dynamic_initial_solution[i])
#     print('objective func: ', get_objective_function_val(dynamic_initial_solution, relative=False))
#     print('avg. travel time per passenger: ', get_objective_function_val(dynamic_initial_solution, relative=True))


# cProfiler

# pr.disable()
# s = io.StringIO()
# sortby = 'cumulative'
# ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
# ps.print_stats()
# print(s.getvalue())





