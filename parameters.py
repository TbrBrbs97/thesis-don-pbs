from network_generation import import_network, generate_cost_matrix, \
    get_network_boundaries, generate_distance_matrix, calc_average_interstop_distance
from requests import count_requests, get_scenario_mean_demand, \
    list_individual_requests, convert_md_todict, generate_static_requests, \
    generate_static_requests_2, count_requests_per_od, size_request_groups_per_od, group_requests_dt

# GENERAL
v_mean = 50  # km/h
demand_scenario = 3
time_of_day = 1  # 1 = peak, 0 = off-peak
peak_duration = 60  # min.
degree_of_dynamism = 0.0 # percent
lead_time = 5 # min.
random_seed = 7

# NETWORK CHARACTERISTICS

network_size = 'medium'
interstop_distance = 'half'

network = import_network(network_size, interstop_distance)
cost_matrix = generate_cost_matrix(network, v_mean)
distance_matrix = generate_distance_matrix(network)
network_dim = get_network_boundaries(network)

average_interstop_distance = calc_average_interstop_distance(network)

# VEHICLE CHARACTERISTICS

max_vehicle_ride_time = peak_duration + cost_matrix[(network_dim[0], network_dim[2])]  #min.
cap_per_veh = 20
nb_of_available_vehicles = 16

# REQUEST CHARACTERISTICS

req_max_cluster_time = cap_per_veh / 2 #min.

lambdapeak = get_scenario_mean_demand('city', network_size, scen=demand_scenario, peak=1)
mupeak = get_scenario_mean_demand('terminal', network_size, scen=demand_scenario, peak=1)

mean_demand = convert_md_todict(lambdapeak, mupeak, demand_scenario)
requests_per_od = generate_static_requests_2(mean_demand, peak_duration, set_seed=random_seed)

all_static_requests, all_dynamic_requests = list_individual_requests(requests_per_od, dod=degree_of_dynamism,
                                                                     lead_time=lead_time, set_seed=random_seed)

grouped_requests = group_requests_dt(all_static_requests, req_max_cluster_time, requests_per_od.keys())
count_total_requests = count_requests(grouped_requests)
count_groups = count_requests_per_od(grouped_requests)
size_groups = size_request_groups_per_od(grouped_requests)

# OPTIMIZATION

M = 1000  # a very large number
opt_time_lim = 10  # minutes
disturbance_ratio = 0.1
shuffle_ratio = 0.5 # not really used
steep_descent_intensity = 1
stop_addition_penalty = 0 # node addition penalty
delta = int(peak_duration / 4)  # min.
