import pandas as pd
import pickle

import requests_generation as rg
import network_generation as netg
import solution_generation as sg
import solution_evaluation as se
import vehicle_generation as vg
import solution_visualisation as sv

#parameters
network_size = 'small'
demand_scenario = 2
time_of_day = 1 #1 = peak, 0 = off-peak
peak_duration = 60 #min.
v_mean = 50 #km/h
interstop_distance = 'half'
cap_per_veh = 20

req_max_cluster_time = 10 #min.

# requests
lambdapeak = rg.get_scenario_mean_demand('city', network_size, scen=demand_scenario, peak=1)
mupeak = rg.get_scenario_mean_demand('terminal', network_size, scen=demand_scenario, peak=1)

dict_requests = rg.convert_md_todict(lambdapeak, mupeak, demand_scenario)

total_requests = rg.generate_requests(dict_requests, peak_duration, seed=True)
OD_pairs = total_requests.keys()

list_all_requests = rg.list_all_requests(total_requests)
print('total request amount: ', len(list_all_requests))

grouped_requests = rg.group_requests_dt(list_all_requests, req_max_cluster_time, OD_pairs)
count_groups = rg.request_groups_per_od(grouped_requests)

# network
network = netg.import_network(network_size, interstop_distance)
od_matrix = netg.generate_tt_od(network, v_mean)

# solution check

# tocity_keys = [(1, 2), (2, 3), (1, 3)]
# toterminal_keys = [(3, 4), (3, 5), (4, 5)]
#
# filterByKey = lambda keys: {x: grouped_requests[x] for x in keys}
# tocity_requests = filterByKey(tocity_keys)
# toterminal_requests = filterByKey(toterminal_keys)

terminal, city, terminal_end = netg.get_network_boundaries(network)
network_dim = terminal, city, terminal_end

nb_of_required_veh = round(len(list_all_requests)/cap_per_veh + 10)
round_trips = {1, 2, 3, 4, 5, 6}


initial = sg.create_initial_solution(grouped_requests, city, terminal_end, network_dim, current_veh=1,
                                     nb_of_vehicles=nb_of_required_veh, round_trip_veh=round_trips,
                                     od_matrix=od_matrix, max_capacity=cap_per_veh)

vehicles_schedules = sg.services_to_vehicles(initial, network_dim, od_matrix, max_services_per_veh=5)
#print(grouped_requests)
print(vehicles_schedules)

waiting_time_dict = se.calc_waiting_time(vehicles_schedules)
inveh_time_dict = se.calc_in_vehicle_time(vehicles_schedules)
total_tt_dict = se.calculate_ttt(inveh_time_dict, waiting_time_dict)
#print(total_tt_dict)

wt_stops = se.sum_total_tt(waiting_time_dict, level='stop')
ivt_stops = se.sum_total_tt(inveh_time_dict, level='stop')
sum_stops = se.sum_total_tt(total_tt_dict, level='stop')
#print('sum stops= ', sum_stops)

sum_vehicle = se.sum_total_tt(total_tt_dict, level='vehicle')
#print('sum vehicles= ', sum_vehicle)

sum_total = se.sum_total_tt(total_tt_dict, level='total')
print('sum total= ', sum_total)
print('average travel time per passenger = ', sum_total/len(list_all_requests))

occ = se.calc_occupancy_rate(vehicles_schedules, cap_per_veh)
#print(occ)

# Convert to DF and export to excel:

df_solution = sv.convert_to_dataframe(vehicles_schedules)
df_wt = sv.convert_to_dataframe(wt_stops)
df_ivt = sv.convert_to_dataframe(ivt_stops)
df_occ = sv.convert_to_dataframe(occ)

# maybe you need one column extra (abboard_pax3) ! Depends...
col_names = ['dep_time', 'abboard_pax1', 'abboard_pax2', 'sum_wt', 'sum_ivt', 'veh_occ']
df_all = pd.concat([df_solution, df_wt, df_ivt, df_occ], axis=1)
df_all.columns = col_names

df_all.to_excel("Exports/entire_solution.xlsx")

## Export to pickle

with open('Exports/initial_solution.pickle', 'wb') as handle:
    pickle.dump(vehicles_schedules, handle, protocol=pickle.HIGHEST_PROTOCOL)