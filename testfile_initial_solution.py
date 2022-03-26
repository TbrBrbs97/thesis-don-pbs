import pandas as pd
import pickle

import requests_generation as rg
import network_generation as netg
import solution_generation as sg
import solution_evaluation as se
import vehicle_generation as vg
import solution_visualisation as sv

from alt_solution_gen import generate_initial_solution, init_fill_every_vehicle, pop_request, \
    get_existing_arcs, get_existing_nodes, arc_in_vehicle, get_all_occurrences_of_node, get_next_node, get_prev_node

from parameters import network, lambdapeak, mupeak, demand_scenario, peak_duration, \
    req_max_cluster_time, cap_per_veh, max_services_per_vehicle, cost_matrix, grouped_requests, nb_of_required_ser

initial_solution = init_fill_every_vehicle(grouped_requests, nb_of_required_ser)
for i in initial_solution:
     print('veh: ', i, ', stops: ', initial_solution[i])

# portion_matching_od = arc_in_vehicle(initial_solution, 1, (2, 3))
# print(portion_matching_od)
# all_occ_of_node = get_all_occurrences_of_node(initial_solution, 1, 3)
print(get_existing_nodes(initial_solution, 1))
print(get_next_node(initial_solution, 1, '1,0'))



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