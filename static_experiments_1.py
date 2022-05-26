import pickle

from settings import v_mean, demand_scenario, demand_subscenario, degree_of_dynamism, \
    lead_time, nb_of_available_vehicles, steep_descent_intensity
from network_generation import import_network, generate_cost_matrix, \
    get_network_boundaries, generate_distance_matrix

from requests import get_scenario_mean_demand, list_individual_requests, convert_md_todict, \
    generate_static_requests_2, group_requests_dt, count_total_requests

from solution_construct import generate_initial_solution, static_optimization


# PARAMETERS
network_sizes = ['small', 'medium', 'large', 'real']
network_variants = ['half', 'more']
nb_of_samples = 2

for size in network_sizes:
    for variant in network_variants:
        sample = 1
        while sample < nb_of_samples:
            print('CURRENTLY RUNNING: ', size, variant, sample)
            network_size = size
            network_variant = variant
            random_seed = sample

            if network_size == 'small':
                peak_duration = 20  # min.
                opt_time_limit = 60
            elif network_size == 'medium':
                peak_duration = 40
                opt_time_limit = 120
            elif network_size == 'large':
                peak_duration = 60
                opt_time_limit = 180
            else:
                peak_duration = 120
                opt_time_limit = 480

            network = import_network(network_size, network_variant)
            cost_matrix = generate_cost_matrix(network, v_mean)
            distance_matrix = generate_distance_matrix(network)
            network_dim = get_network_boundaries(network)

            req_max_cluster_time = peak_duration / 8

            lambdapeak = get_scenario_mean_demand('city', network_size, scen=demand_scenario,
                                                  subscen=demand_subscenario, peak=1)
            mupeak = get_scenario_mean_demand('terminal', network_size, scen=demand_scenario,
                                              subscen=demand_subscenario, peak=1)

            if network_size != 'real':
                mean_demand = convert_md_todict(lambdapeak, mupeak, scen=demand_scenario)
            else:
                mean_demand = convert_md_todict(lambdapeak, mupeak, scen=demand_scenario, subscen=demand_subscenario)

            requests_per_od = generate_static_requests_2(mean_demand, peak_duration, set_seed=random_seed)
            total_nb_of_requests = count_total_requests(requests_per_od)

            all_static_requests, all_dynamic_requests = list_individual_requests(requests_per_od,
                                                                                 dod=degree_of_dynamism,
                                                                                 lead_time=lead_time,
                                                                                 set_seed=random_seed)

            grouped_requests = group_requests_dt(all_static_requests, req_max_cluster_time, requests_per_od.keys())

            # INITIAL SOLUTION
            initial_solution = generate_initial_solution(network, grouped_requests, nb_of_available_veh=nb_of_available_vehicles)
            init_name = 'Results/SE_1/' + network_size + '_' + network_variant + '_' + str(sample) + '_init'

            file_to_write_1 = open(init_name, "wb")
            pickle.dump(initial_solution, file_to_write_1)

            # OPTIMIZED SOLUTION
            optimized_solution, best_iteration = static_optimization(network, initial_solution,
                                                                     required_requests_per_it=steep_descent_intensity,
                                                                     time_limit=opt_time_limit)
            opt_name = 'Results/SE_1/' + network_size + '_' + network_variant + '_' + str(sample) + '_opt'
            file_to_write_2 = open(opt_name, "wb")
            pickle.dump(optimized_solution, file_to_write_2)

            sample += 1


