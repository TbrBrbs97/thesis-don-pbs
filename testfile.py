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

req_max_cluster_time = 10 #min.

# requests
lambdapeak = rg.get_scenario_mean_demand('city', network_size, scen=demand_scenario, peak=1)
mupeak = rg.get_scenario_mean_demand('terminal', network_size, scen=demand_scenario, peak=1)

dict_requests = rg.convert_md_todict(lambdapeak, mupeak, demand_scenario)

total_requests = rg.generate_requests(dict_requests, peak_duration, seed=True)
OD_pairs = total_requests.keys()

list_all_requests = rg.list_all_requests(total_requests)
grouped_requests = rg.group_requests_dt(list_all_requests, req_max_cluster_time, OD_pairs)
count_groups = rg.request_groups_per_od(grouped_requests)

# network
network = netg.import_network(network_size, interstop_distance)
od_matrix = netg.generate_tt_od(network, v_mean)

# solution check

tocity_keys = [(1, 2), (2, 3), (1, 3)]
toterminal_keys = [(3, 4), (3, 5), (4, 5)]

filterByKey = lambda keys: {x: grouped_requests[x] for x in keys}
tocity_requests = filterByKey(tocity_keys)
toterminal_requests = filterByKey(toterminal_keys)


terminal, city, terminal_end = netg.get_network_boundaries(network)
network_dim = terminal, city, terminal_end
round_trips = {1, 2, 3, 4}

initial = sg.create_initial_solution(grouped_requests, city, terminal_end, network_dim, current_veh=1,
                                     nb_of_vehicles=35, round_trip_veh=round_trips, max_capacity=20)

#print(initial)
#print(grouped_requests)

corrected_initial = sg.correct_dep_times(initial, od_matrix, round_trips, network_dim)
print(corrected_initial)

vehicles_schedules = sg.services_to_vehicles(corrected_initial, round_trips, network_dim)
print(vehicles_schedules.keys())

#waiting_time_dict = se.calc_waiting_time(corrected_initial)
#inveh_time_dict = se.calc_in_vehicle_time(corrected_initial)
#total_tt_dict = se.calculate_ttt(inveh_time_dict, waiting_time_dict)
#print(total_tt_dict)

#sum_stops = se.sum_total_tt(total_tt_dict, level='stop')
#print('sum stops= ', sum_stops)

#sum_vehicle = se.sum_total_tt(total_tt_dict, level='vehicle')
#print('sum vehicles= ', sum_vehicle)

#sum_total = se.sum_total_tt(total_tt_dict, level='total')
#print('sum total= ', sum_total)

#df = sv.convert_to_dataframe(corrected_initial)
#print(df)

#occ = se.calc_occupancy_rate(corrected_initial, 20)
#print(occ)

