import pandas as pd
import pickle
from pprint import PrettyPrinter, pprint

from requests import get_od_from_request_group

from vehicle import locate_request_group_in_schedule, is_empty_vehicle_schedule, \
    count_assigned_request_groups, room_for_insertion_at_node, get_copy_vehicles_schedule

from requests import count_requests, add_request_group_to_dict

from static_operators import remove_request_group, find_best_position_for_request_group, select_random_request_groups

from solution_construct import generate_initial_solution, static_optimization, disturb_solution, select_random_request_groups, init_fill_every_vehicle

from solution_evaluation import calc_request_group_waiting_time, calc_request_group_invehicle_time, \
    get_objective_function_val, generate_waiting_time_dict, generate_in_vehicle_time_dict, generate_total_travel_time_dict, select_most_costly_request_groups

from parameters import network, lambdapeak, mupeak, demand_scenario, peak_duration, \
    req_max_cluster_time, cap_per_veh, nb_of_available_vehicles, \
    cost_matrix, grouped_requests, nb_of_available_vehicles, opt_time_lim, all_static_requests, all_dynamic_requests

# import cProfile, pstats, io
# pr = cProfile.Profile()
# pr.enable()

# print(all_static_requests, all_dynamic_requests)

total_requests = count_requests(grouped_requests)

initial_solution, scores_dict = generate_initial_solution(grouped_requests)

for i in initial_solution:
    print('veh ', i, ': ', initial_solution[i])
print('objective func: ', get_objective_function_val(initial_solution, relative=False))


# print(get_objective_function_val(initial_solution))
# optimized_solution, new_positions = static_optimization(initial_solution, required_requests_per_it=2,
#                                                         time_limit=opt_time_lim)
# for i in optimized_solution:
#     print('veh ', i, ': ', optimized_solution[i])
# print('avg. travel time per passenger: ', get_objective_function_val(optimized_solution, relative=True))
#

# print(count_assigned_request_groups(optimized_solution))


# cProfiler

# pr.disable()
# s = io.StringIO()
# sortby = 'cumulative'
# ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
# ps.print_stats()
# print(s.getvalue())





