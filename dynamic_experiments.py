### IMPACT OF DIFFERENT DOD

import pickle

from settings import v_mean, lead_time, steep_descent_intensity, demand_scenario, demand_subscenario

from network_generation import import_network, generate_cost_matrix, \
    get_network_boundaries, generate_distance_matrix

from solution_evaluation import count_total_assigned_requests

from requests import get_scenario_mean_demand, list_individual_requests, convert_md_todict, \
    generate_static_requests_2, group_requests_dt, count_total_requests

from solution_construct import generate_initial_solution, static_optimization, dynamic_optimization, generate_dynamic_solution

opt_time_lim = 240
degrees_of_dynamism = [0.25, 0.5, 0.75]
random_seed = 1
network_size = 'real'
peak_duration = 120
network_variant = 'half'
nb_of_samples = 4

nb_of_available_vehicles = 16
capacity = 20
depot = 'terminal'

for dod in degrees_of_dynamism:
    sample = 1
    while sample < nb_of_samples:

        delta = 1/dod

        network = import_network(network_size, network_variant)
        cost_matrix = generate_cost_matrix(network, v_mean)
        distance_matrix = generate_distance_matrix(network)
        network_dim = get_network_boundaries(network)

        req_max_cluster_time = 15 # min.

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
        print(len(all_static_requests), len(all_dynamic_requests))

        grouped_requests = group_requests_dt(all_static_requests, req_max_cluster_time, requests_per_od.keys())

        initial_solution = generate_initial_solution(network, grouped_requests,
                                                     nb_of_available_veh=nb_of_available_vehicles,
                                                     capacity=capacity)
        assert count_total_assigned_requests(initial_solution) == len(all_static_requests)

        optimized_solution, best_iteration = static_optimization(network, initial_solution,
                                                                 required_requests_per_it=steep_descent_intensity,
                                                                 time_limit=opt_time_lim, capacity=capacity, depot=depot)
        assert count_total_assigned_requests(optimized_solution) == len(all_static_requests)

        opt_name = 'Results/DE_1/' + network_size + '_dod' + str(dod) + '_stat_opt.pickle'
        file_to_write_1 = open(opt_name, "wb")
        pickle.dump(optimized_solution, file_to_write_1)

        dynamic_solution = generate_dynamic_solution(network, optimized_solution, all_dynamic_requests,
                                                     lead_time=lead_time, peak_hour_duration=peak_duration,
                                                     capacity=capacity, depot=depot, delta=delta)
        print(count_total_assigned_requests(dynamic_solution))
        print(len(all_static_requests), len(all_dynamic_requests))
        assert count_total_assigned_requests(dynamic_solution) == len(all_static_requests) + len(all_dynamic_requests)

        opt_name = 'Results/DE_1/' + network_size + '_dod' + str(dod) + '_dyn_opt.pickle'
        file_to_write_2 = open(opt_name, "wb")
        pickle.dump(dynamic_solution, file_to_write_2)

    sample += 1