from network_generation import import_network, generate_cost_matrix, \
    get_network_boundaries, generate_distance_matrix, calc_average_interstop_distance
from requests import count_requests, get_scenario_mean_demand, \
    list_individual_requests, convert_md_todict, generate_static_requests, \
    generate_static_requests_2, count_requests_per_od, size_request_groups_per_od, group_requests_dt, count_total_requests

# GENERAL

v_mean = 50  # km/h
demand_scenario = 2
demand_subscenario = 2
time_of_day = 1  # 1 = peak, 0 = off-peak
degree_of_dynamism = 0.0 # percent
lead_time = 1 # min.
random_seed = 8
depot = 'terminal'

# NETWORK CHARACTERISTICS

network_size = 'real'
network_variant = 'half' # this refers to the 1 in S1

if network_size == 'small':
    peak_duration = 20  # min.
elif network_size == 'medium':
    peak_duration = 40
elif network_size == 'large':
    peak_duration = 60
else:
    peak_duration = 120

network = import_network(network_size, network_variant)
cost_matrix = generate_cost_matrix(network, v_mean)
distance_matrix = generate_distance_matrix(network)
network_dim = get_network_boundaries(network)

average_interstop_distance = calc_average_interstop_distance(network)

# VEHICLE CHARACTERISTICS

max_vehicle_ride_time = peak_duration + cost_matrix[(network_dim[0], network_dim[2])]  #min.
cap_per_veh = 80
nb_of_available_vehicles = 4

# REQUEST CHARACTERISTICS

req_max_cluster_time = peak_duration / 4 #min.

lambdapeak = get_scenario_mean_demand('city', network_size, scen=demand_scenario, subscen=demand_subscenario, peak=1)
mupeak = get_scenario_mean_demand('terminal', network_size, scen=demand_scenario, subscen=demand_subscenario, peak=1)

if network_size != 'real':
    mean_demand = convert_md_todict(lambdapeak, mupeak, scen=demand_scenario)
else:
    mean_demand = convert_md_todict(lambdapeak, mupeak, scen=demand_scenario, subscen=demand_subscenario)

requests_per_od = generate_static_requests_2(mean_demand, peak_duration, set_seed=random_seed)
total_nb_of_requests = count_total_requests(requests_per_od)

all_static_requests, all_dynamic_requests = list_individual_requests(requests_per_od, dod=degree_of_dynamism,
                                                                     lead_time=lead_time, set_seed=random_seed)

grouped_requests = group_requests_dt(all_static_requests, req_max_cluster_time, requests_per_od.keys())
count_static_requests = count_requests(grouped_requests)
count_groups = count_requests_per_od(grouped_requests)
size_groups = size_request_groups_per_od(grouped_requests)

# OPTIMIZATION

M = 1000  # a very large number
opt_time_lim = 30 #minutes
# disturbance_ratio = max((cap_per_veh / 4000, 0.01))
reinitiation_threshold = 5
disturbance_threshold = 1 #iterations
disturbance_ratio = 0.01
shuffle_threshold = 50
shuffle_ratio = 0.25
steep_descent_intensity = 15
stop_addition_penalty = 0  # node addition penalty
delta = int(peak_duration / 4)  # min.
