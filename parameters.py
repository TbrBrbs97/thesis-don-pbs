from network_generation import import_network, generate_cost_matrix, get_network_boundaries
from requests import count_requests, get_od_from_request_group, get_scenario_mean_demand, \
    list_all_requests, convert_md_todict, generate_requests, count_requests_per_od, \
    size_request_groups_per_od, group_requests_dt

# GENERAL

v_mean = 50 # km/h
demand_scenario = 2
time_of_day = 1 #1 = peak, 0 = off-peak
peak_duration = 60 #min.

# NETWORK CHARACTERISTICS

network_size = 'small'
interstop_distance = 'half'

network = import_network(network_size, interstop_distance)
cost_matrix = generate_cost_matrix(network, v_mean)
network_dim = get_network_boundaries(network)

# REQUEST CHARACTERISTICS

req_max_cluster_time = 8 #min.

lambdapeak = get_scenario_mean_demand('city', network_size, scen=demand_scenario, peak=1)
mupeak = get_scenario_mean_demand('terminal', network_size, scen=demand_scenario, peak=1)

mean_demand = convert_md_todict(lambdapeak, mupeak, demand_scenario)
requests_per_od = generate_requests(mean_demand, peak_duration, seed=True)

list_all_requests = list_all_requests(requests_per_od)

grouped_requests = group_requests_dt(list_all_requests, req_max_cluster_time, requests_per_od.keys())
count_total_requests = count_requests(grouped_requests)
count_groups = count_requests_per_od(grouped_requests)
size_groups = size_request_groups_per_od(grouped_requests)

# VEHICLE CHARACTERISTICS

max_vehicle_ride_time = peak_duration + 2*cost_matrix[(network_dim[0], network_dim[2])] #min.
cap_per_veh = 20
nb_of_available_vehicles = 16

# OPTIMIZATION

M = 100000.0 # a very large number
opt_time_lim = 1 # minutes
disturbance_ratio = 0.1
shuffle_ratio = 0.5
stop_addition_penalty = 20