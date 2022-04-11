import pandas as pd
import pickle

from requests import get_od_from_request_group

from vehicle import locate_request_group_in_schedule, is_empty_vehicle_schedule

from requests import count_requests

from static_operators import remove_request_group, find_best_position_for_request_group, select_random_request_groups

from solution_construct import generate_initial_solution, static_optimization, shuffle_solution

from solution_evaluation import calc_request_group_waiting_time, calc_request_group_invehicle_time, \
    get_objective_function_val, generate_waiting_time_dict, generate_in_vehicle_time_dict, generate_total_travel_time_dict, select_most_costly_request_groups

from parameters import network, lambdapeak, mupeak, demand_scenario, peak_duration, \
    req_max_cluster_time, cap_per_veh, max_services_per_vehicle, cost_matrix, grouped_requests, nb_of_required_ser


# ITERATIVE TESTS

# i = 0
# while i < 67:
#     request_group = pop_request(grouped_requests)
#     best_pos = find_best_position_for_request_group(initial_solution, request_group)
#     # print(best_pos)
#     #initial_solution, grouped_requests = insert_request_group(initial_solution, grouped_requests, request_group, best_pos[0], best_pos[1])
#     insert_request_group(initial_solution, grouped_requests, request_group, best_pos[0], best_pos[1])
#     i += 1

# print(grouped_requests)
total_requests = count_requests(grouped_requests)

initial_solution = generate_initial_solution(grouped_requests)

# for i in initial_solution:
#     print('veh: ', i, ', stops: ', initial_solution[i])

# print('GROUPED REQUESTS')
# print(grouped_requests)

print(get_objective_function_val(initial_solution))

# print(select_random_request_groups(initial_solution, required_amount=40))
shuffled_solution = shuffle_solution(initial_solution, intensity=50)

for i in shuffled_solution:
    print('veh: ', i, ', stops: ', initial_solution[i])

print(get_objective_function_val(shuffled_solution))

# optimized_solution, new_positions = static_optimization(initial_solution, required_requests_per_it=10, nb_of_iterations=20)
# print(get_objective_function_val(optimized_solution))
# print(new_positions)






# To dataframe

# df_solution = pd.DataFrame.from_dict(initial_solution, orient='columns')
# df_ivt = pd.DataFrame.from_dict(in_vehicle_time_dict, orient='columns')
# df_wt = pd.DataFrame.from_dict(waiting_time_dict, orient='columns')
#
# # TODO: vehicle occupancy monitoring?
#
# # col_names = ['dep_time', 'abboard_pax1', 'abboard_pax2', 'sum_wt', 'sum_ivt']
# df_all = pd.concat([df_solution, df_wt, df_ivt], axis=1)
# # df_all.columns = col_names
#
# df_all.to_excel("Exports/entire_solution.xlsx")

# Export to pickle

# with open('Exports/initial_solution.pickle', 'wb') as handle:
#     pickle.dump(initial_solution, handle, protocol=pickle.HIGHEST_PROTOCOL)

