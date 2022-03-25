import pandas as pd
import pickle

import requests_generation as rg
import network_generation as netg
import solution_generation as sg
import solution_evaluation as se
import vehicle_generation as vg
import solution_visualisation as sv

from alt_solution_gen import generate_initial_solution, init_fill_every_vehicle, pop_request, get_existing_arcs

from parameters import network, lambdapeak, mupeak, demand_scenario, peak_duration, \
    req_max_cluster_time, cap_per_veh, max_services_per_vehicle, cost_matrix, grouped_requests, nb_of_required_ser

initial_solution = init_fill_every_vehicle(grouped_requests, nb_of_required_ser)
for i in initial_solution:
     print('veh: ', i, ', stops: ', initial_solution[i])

print(get_existing_arcs(initial_solution, 2))

# random_request = pop_request(grouped_requests)
# print(random_request)


# vehicles_schedules = sg.services_to_vehicles(initial, par.max_services_per_vehicle)
# #print(grouped_requests)
# print(vehicles_schedules[(3,1)])
#
# waiting_time_dict = se.calc_waiting_time(vehicles_schedules)
# #print(waiting_time_dict[(2, 2)])
# inveh_time_dict = se.calc_in_vehicle_time(vehicles_schedules)
# #print(inveh_time_dict[(2, 2)])
# total_tt_dict = se.calculate_ttt(inveh_time_dict, waiting_time_dict)
# #print(total_tt_dict)
#
# wt_stops = se.sum_total_tt(waiting_time_dict, level='stop')
# ivt_stops = se.sum_total_tt(inveh_time_dict, level='stop')
# sum_stops = se.sum_total_tt(total_tt_dict, level='stop')
# #print('sum stops= ', sum_stops)
#
# sum_vehicle = se.sum_total_tt(total_tt_dict, level='vehicle')
# #print('sum vehicles= ', sum_vehicle)
#
# sum_total = se.sum_total_tt(total_tt_dict, level='total')
# print('sum total= ', sum_total)
# print('average travel time per passenger = ', sum_total/len(list_all_requests))
#
# occ = se.calc_occupancy_rate(vehicles_schedules, par.cap_per_veh)
# #print(occ)
#
# # Convert to DF and export to excel:
#
# df_solution = sv.convert_to_dataframe(vehicles_schedules)
# df_wt = sv.convert_to_dataframe(wt_stops)
# df_ivt = sv.convert_to_dataframe(ivt_stops)
# df_occ = sv.convert_to_dataframe(occ)
#
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