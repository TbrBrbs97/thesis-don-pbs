import network_generation as netg
import requests as rg

network_size = 'small'
interstop_distance = 'half'
v_mean = 50 # km/h
demand_scenario = 2
time_of_day = 1 #1 = peak, 0 = off-peak
peak_duration = 60 #min.
cap_per_veh = 20
req_max_cluster_time = 2 #min.
max_vehicle_ride_time = 70 #min.

chaining_penalty = 20 #min.

network = netg.import_network(network_size, interstop_distance)
cost_matrix = netg.generate_cost_matrix(network, v_mean)
network_dim = netg.get_network_boundaries(network)

max_services_per_vehicle = 3

lambdapeak = rg.get_scenario_mean_demand('city', network_size, scen=demand_scenario, peak=1)
mupeak = rg.get_scenario_mean_demand('terminal', network_size, scen=demand_scenario, peak=1)

mean_demand = rg.convert_md_todict(lambdapeak, mupeak, demand_scenario)
requests_per_od = rg.generate_requests(mean_demand, peak_duration, seed=True)

list_all_requests = rg.list_all_requests(requests_per_od)

grouped_requests = rg.group_requests_dt(list_all_requests, req_max_cluster_time, requests_per_od.keys())
count_groups = rg.count_requests_per_od(grouped_requests)
size_groups = rg.size_request_groups_per_od(grouped_requests)

nb_of_required_ser = round(len(list_all_requests)/(cap_per_veh*max_services_per_vehicle))