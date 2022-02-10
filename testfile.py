import requests_generation as rg
import od_traveltime_generation as od
import solution_generation as sg
import traveltime_evaluation as te

#parameters
network_size = 'small'
demand_scenario = 2
time_of_day = 1 #1 = peak, 0 = off-peak
peak_duration = 60 #min.
v_mean = 50 #km/h
interstop_distance = 'half'

req_max_cluster_time = 5 #min.

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
network = od.import_network(network_size, interstop_distance)
od_matrix = od.generate_tt_od(network, v_mean)

# solution check

tocity_keys = [(1, 2), (2, 3), (1, 3)]
toterminal_keys = [(3, 4), (3, 5), (4, 5)]

filterByKey = lambda keys: {x: grouped_requests[x] for x in keys}
tocity_requests = filterByKey(tocity_keys)
toterminal_requests = filterByKey(toterminal_keys)

initial = sg.create_initial_solution(grouped_requests, 1, 3, current_veh=1,
                                     nb_of_vehicles=35, max_capacity=20)

corrected_initial = sg.correct_dep_times(initial, od_matrix)
#print(corrected_initial[6])

waiting_time_dict = te.calc_waiting_time(corrected_initial)
inveh_time_dict = te.calc_in_vehicle_time(corrected_initial, od_matrix)
total_tt_dict = te.calculate_ttt(inveh_time_dict, waiting_time_dict)
print(total_tt_dict[6])

sum_stops = te.sum_total_tt(total_tt_dict, level='stop')
print('sum stops= ', sum_stops)

sum_vehicle = te.sum_total_tt(total_tt_dict, level='vehicle')
print('sum vehicles= ', sum_vehicle)

sum_total = te.sum_total_tt(total_tt_dict, level='total')
print('sum total= ', sum_total)

