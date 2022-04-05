import pandas as pd
import pickle

import requests as rg
import network_generation as netg
import solution_generation as sg
import solution_evaluation as se
import vehicle as vg
import solution_visualisation as sv

from requests import get_od_from_request_group

from vehicle import get_last_arrival

from alt_solution_gen import generate_initial_solution, init_fill_every_vehicle, pop_request, \
    get_existing_arcs, get_existing_nodes, get_insertion_possibilities, get_all_occurrences_of_node, \
    get_next_node, get_prev_node, room_for_insertion_at_node, find_best_position_for_request_group, \
    insert_request_group, insert_stop_in_vehicle, get_departure_time_at_node

from parameters import network, lambdapeak, mupeak, demand_scenario, peak_duration, \
    req_max_cluster_time, cap_per_veh, max_services_per_vehicle, cost_matrix, grouped_requests, nb_of_required_ser

initial_solution = init_fill_every_vehicle(grouped_requests, nb_of_required_ser)

i = 0
while i < 13:
    request_group = pop_request(grouped_requests)
    best_pos = find_best_position_for_request_group(initial_solution, request_group)
    # print(best_pos)
    insert_request_group(initial_solution, request_group, best_pos[0], best_pos[1])
    i += 1

for i in initial_solution:
    print('veh: ', i, ', stops: ', initial_solution[i])
























# # maybe you need one column extra (abboard_pax3) ! Depends...
# col_names = ['dep_time', 'abboard_pax1', 'abboard_pax2', 'sum_wt', 'sum_ivt', 'veh_occ']
# df_all = pd.concat([df_solution, df_wt, df_ivt, df_occ], axis=1)
# df_all.columns = col_names
#
# df_all.to_excel("Exports/entire_solution.xlsx")
#
# ## Export to pickle
#
# with open('Exports/initial_solution.pickle', 'wb') as handle:
#     pickle.dump(vehicles_schedules, handle, protocol=pickle.HIGHEST_PROTOCOL)