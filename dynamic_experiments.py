### IMPACT OF DIFFERENT DOD

import pickle

from settings import v_mean, lead_time, steep_descent_intensity, demand_scenario, demand_subscenario

from network_generation import import_network, generate_cost_matrix, \
    get_network_boundaries, generate_distance_matrix

from requests import get_scenario_mean_demand, list_individual_requests, convert_md_todict, \
    generate_static_requests_2, group_requests_dt, count_total_requests

from solution_construct import generate_initial_solution, static_optimization, dynamic_optimization, generate_dynamic_solution

opt_time_lim = 240
degrees_of_dynamism = [0.25, 0.5, 0.75]
random_seed = 1
network_size = 'real'
peak_duration = 120
network_variant = 1

nb_of_available_vehicles = 16
capacity = 20
depot = 'terminal'

for dod in degrees_of_dynamism:

    network = import_network(network_size, network_variant)
    cost_matrix = generate_cost_matrix(network, v_mean)
    distance_matrix = generate_distance_matrix(network)
    network_dim = get_network_boundaries(network)

    req_max_cluster_time = peak_duration / 4  # min.

    lambdapeak = get_scenario_mean_demand('city', network_size, scen=demand_scenario, subscen=demand_subscenario,
                                          peak=1)
    mupeak = get_scenario_mean_demand('terminal', network_size, scen=demand_scenario, subscen=demand_subscenario,
                                      peak=1)

    if network_size != 'real':
        mean_demand = convert_md_todict(lambdapeak, mupeak, scen=demand_scenario)
    else:
        mean_demand = convert_md_todict(lambdapeak, mupeak, scen=demand_scenario, subscen=demand_subscenario)

    requests_per_od = generate_static_requests_2(mean_demand, peak_duration, set_seed=random_seed)
    total_nb_of_requests = count_total_requests(requests_per_od)

    all_static_requests, all_dynamic_requests = list_individual_requests(requests_per_od, dod=dod,
                                                                         lead_time=lead_time, set_seed=random_seed)

    grouped_requests = group_requests_dt(all_static_requests, req_max_cluster_time, requests_per_od.keys())

    initial_solution = generate_initial_solution(network, grouped_requests,
                                                 nb_of_available_veh=nb_of_available_vehicles,
                                                 capacity=capacity)

    optimized_solution, best_iteration = static_optimization(network, initial_solution,
                                                             required_requests_per_it=steep_descent_intensity,
                                                             time_limit=opt_time_lim, capacity=capacity, depot=depot)
    opt_name = 'Results/DE_1/' + network_size + '_dod' + str(dod) + '_stat_opt.pickle'
    file_to_write_1 = open(opt_name, "wb")
    pickle.dump(optimized_solution, file_to_write_1)

    dynamic_solution = generate_dynamic_solution(network, optimized_solution, all_dynamic_requests,
                                                 lead_time=lead_time, peak_hour_duration=peak_duration,
                                                 capacity=capacity, depot=depot)
    opt_name = 'Results/DE_1/' + network_size + '_dod' + str(dod) + '_dyn_opt.pickle'
    file_to_write_2 = open(opt_name, "wb")
    pickle.dump(optimized_solution, file_to_write_2)