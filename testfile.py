import requests_generation as rg
import od_traveltime_generation as od
import solution_generation as sg
import random

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

random.seed('05022022')
dict_requests = rg.convert_md_todict(lambdapeak, mupeak, demand_scenario)

total_requests = rg.generate_requests(dict_requests, peak_duration)
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

copy_cityrequests = tocity_requests.copy()
copy_groupedrequests = grouped_requests.copy()

initial = sg.create_initial_solution(copy_groupedrequests, 3, 5, current_veh=1,
                                     nb_of_vehicles=35, max_capacity=20)
