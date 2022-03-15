import network_generation as netg

network_size = 'small'
interstop_distance = 'half'
v_mean = 50 # km/h
demand_scenario = 2
time_of_day = 1 #1 = peak, 0 = off-peak
peak_duration = 60 #min.
cap_per_veh = 20
req_max_cluster_time = 10 #min.

network = netg.import_network(network_size, interstop_distance)
od_matrix = netg.generate_tt_od(network, v_mean)
network_dim = netg.get_network_boundaries(network)
