import pandas as pd
import pickle

from requests import get_od_from_request_group

from vehicle import get_last_arrival, locate_request_group_in_schedule

from requests import count_requests

from alt_solution_gen import generate_initial_solution, init_fill_every_vehicle, pop_request, \
    get_existing_arcs, get_existing_nodes, get_insertion_possibilities, get_all_occurrences_of_node, \
    get_next_node, get_prev_node, room_for_insertion_at_node, find_best_position_for_request_group, \
    insert_request_group, insert_request_group2, insert_stop_in_vehicle, get_departure_time_at_node

from solution_evaluation import calc_request_group_waiting_time, calc_request_group_invehicle_time, \
    get_objective_function_val, generate_waiting_time_dict, generate_in_vehicle_time_dict, generate_total_travel_time_dict

from parameters import network, lambdapeak, mupeak, demand_scenario, peak_duration, \
    req_max_cluster_time, cap_per_veh, max_services_per_vehicle, cost_matrix, grouped_requests, nb_of_required_ser


# ITERATIVE TESTS

# i = 0
# while i < 67:
#     request_group = pop_request(grouped_requests)
#     best_pos = find_best_position_for_request_group(initial_solution, request_group)
#     # print(best_pos)
#     #initial_solution, grouped_requests = insert_request_group(initial_solution, grouped_requests, request_group, best_pos[0], best_pos[1])
#     insert_request_group2(initial_solution, grouped_requests, request_group, best_pos[0], best_pos[1])
#     i += 1

# print(grouped_requests)
total_requests = count_requests(grouped_requests)

initial_solution = generate_initial_solution(grouped_requests)

for i in initial_solution:
    print('veh: ', i, ', stops: ', initial_solution[i])

print('GROUPED REQUESTS')
print(grouped_requests)

waiting_time_dict = generate_waiting_time_dict(initial_solution)
in_vehicle_time_dict = generate_in_vehicle_time_dict(initial_solution)
total_travel_time_dict = generate_total_travel_time_dict(in_vehicle_time_dict, waiting_time_dict)

print(get_objective_function_val(initial_solution)/total_requests)

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

with open('Exports/initial_solution.pickle', 'wb') as handle:
    pickle.dump(initial_solution, handle, protocol=pickle.HIGHEST_PROTOCOL)

