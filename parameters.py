import network_generation as netg
import requests_generation as rg

network_size = 'small'
interstop_distance = 'half'
v_mean = 50 # km/h
demand_scenario = 2
time_of_day = 1 #1 = peak, 0 = off-peak
peak_duration = 60 #min.
cap_per_veh = 20
req_max_cluster_time = 2 #min.

network = netg.import_network(network_size, interstop_distance)
cost_matrix = netg.generate_cost_matrix(network, v_mean)
network_dim = netg.get_network_boundaries(network)

max_services_per_vehicle = 3

lambdapeak = rg.get_scenario_mean_demand('city', network_size, scen=demand_scenario, peak=1)
mupeak = rg.get_scenario_mean_demand('terminal', network_size, scen=demand_scenario, peak=1)