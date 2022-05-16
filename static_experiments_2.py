import pickle

from parameters import v_mean, demand_scenario, demand_subscenario, \
    degree_of_dynamism, lead_time, steep_descent_intensity, opt_time_lim

from network_generation import import_network, generate_cost_matrix, \
    get_network_boundaries, generate_distance_matrix

from requests import get_scenario_mean_demand, list_individual_requests, convert_md_todict, \
    generate_static_requests_2, group_requests_dt, count_total_requests

from solution_construct import generate_initial_solution, static_optimization

# SETTINGS

req_max_cluster_times = [1, 5, 10, 20]
resource_scenarios = [(4, 80), (16, 20), (80, 4)]
periods = [60, 120]
depot_allocation = ['terminal', 'middle', 'center']

network_size = 'real'
network_variant = 'half'
nb_of_samples = 3

network = import_network(network_size, network_variant)
cost_matrix = generate_cost_matrix(network, v_mean)
distance_matrix = generate_distance_matrix(network)
network_dim = get_network_boundaries(network)

lambdapeak = get_scenario_mean_demand('city', network_size, scen=demand_scenario,
                                      subscen=demand_subscenario, peak=1)
mupeak = get_scenario_mean_demand('terminal', network_size, scen=demand_scenario,
                                  subscen=demand_subscenario, peak=1)

if network_size != 'real':
    mean_demand = convert_md_todict(lambdapeak, mupeak, scen=demand_scenario)
else:
    mean_demand = convert_md_todict(lambdapeak, mupeak, scen=demand_scenario, subscen=demand_subscenario)

# MAX CLUSTER TIME

for h in req_max_cluster_times:

    peak_duration = 60
    nb_of_available_vehicles = 16
    capacity = 20
    req_max_cluster_time = h
    sample = 0

    while sample < nb_of_samples:
        print('CURRENTLY RUNNING: ', h, 'max cluster time', sample)
        random_seed = sample

        requests_per_od = generate_static_requests_2(mean_demand, peak_duration, set_seed=random_seed)
        total_nb_of_requests = count_total_requests(requests_per_od)

        all_static_requests, all_dynamic_requests = list_individual_requests(requests_per_od,
                                                                             dod=degree_of_dynamism,
                                                                             lead_time=lead_time,
                                                                             set_seed=random_seed)

        grouped_requests = group_requests_dt(all_static_requests, req_max_cluster_time, requests_per_od.keys())

        # INITIAL SOLUTION
        initial_solution = generate_initial_solution(network, grouped_requests,
                                                     nb_of_available_veh=nb_of_available_vehicles, capacity=capacity)
        # init_name = 'Results/' + network_size + '_' + str(sample) + '_clust_' + str(h) + '_init'
        #
        # file_to_write_1 = open(init_name, "wb")
        # pickle.dump(initial_solution, file_to_write_1)

        # OPTIMIZED SOLUTION
        optimized_solution, best_iteration = static_optimization(network, initial_solution,
                                                                 required_requests_per_it=steep_descent_intensity,
                                                                 time_limit=opt_time_lim, capacity=capacity)
        opt_name = 'Results/' + network_size + '_' + str(sample) + '_clust_' + str(h) + '_opt.pickle'
        file_to_write_2 = open(opt_name, "wb")
        pickle.dump(optimized_solution, file_to_write_2)

        sample += 1

# RESOURCE ALLOCATION

for tup in resource_scenarios:

    peak_duration = 60
    nb_of_available_vehicles = tup[0]
    capacity = tup[1]
    req_max_cluster_time = 20
    sample = 0

    while sample < nb_of_samples:
        print('CURRENTLY RUNNING: ', tup, 'resource scen.', sample)
        random_seed = sample

        requests_per_od = generate_static_requests_2(mean_demand, peak_duration, set_seed=random_seed)
        total_nb_of_requests = count_total_requests(requests_per_od)

        all_static_requests, all_dynamic_requests = list_individual_requests(requests_per_od,
                                                                             dod=degree_of_dynamism,
                                                                             lead_time=lead_time,
                                                                             set_seed=random_seed)

        grouped_requests = group_requests_dt(all_static_requests, req_max_cluster_time, requests_per_od.keys())

        # INITIAL SOLUTION
        initial_solution = generate_initial_solution(network, grouped_requests,
                                                     nb_of_available_veh=nb_of_available_vehicles, capacity=capacity)
        # init_name = 'Results/' + network_size + '_' + str(sample) + '_clust_' + str(h) + '_init'
        #
        # file_to_write_1 = open(init_name, "wb")
        # pickle.dump(initial_solution, file_to_write_1)

        # OPTIMIZED SOLUTION
        optimized_solution, best_iteration = static_optimization(network, initial_solution,
                                                                 required_requests_per_it=steep_descent_intensity,
                                                                 time_limit=opt_time_lim, capacity=capacity)
        opt_name = 'Results/' + network_size + '_' + str(sample) + '_' + str(nb_of_available_vehicles) + 'veh_' \
                   + str(capacity) + 'cap_' + '_opt.pickle'
        file_to_write_2 = open(opt_name, "wb")
        pickle.dump(optimized_solution, file_to_write_2)

        sample += 1

# PEAK DURATION

for phd in periods:

    peak_duration = phd
    nb_of_available_vehicles = 16
    capacity = 20
    req_max_cluster_time = 20
    sample = 0

    while sample < nb_of_samples:
        print('CURRENTLY RUNNING: ', phd, 'peak duration (min.)', sample)
        random_seed = sample

        requests_per_od = generate_static_requests_2(mean_demand, peak_duration, set_seed=random_seed)
        total_nb_of_requests = count_total_requests(requests_per_od)

        all_static_requests, all_dynamic_requests = list_individual_requests(requests_per_od,
                                                                             dod=degree_of_dynamism,
                                                                             lead_time=lead_time,
                                                                             set_seed=random_seed)

        grouped_requests = group_requests_dt(all_static_requests, req_max_cluster_time, requests_per_od.keys())

        # INITIAL SOLUTION
        initial_solution = generate_initial_solution(network, grouped_requests,
                                                     nb_of_available_veh=nb_of_available_vehicles, capacity=capacity)
        # init_name = 'Results/' + network_size + '_' + str(sample) + '_clust_' + str(h) + '_init'
        #
        # file_to_write_1 = open(init_name, "wb")
        # pickle.dump(initial_solution, file_to_write_1)

        # OPTIMIZED SOLUTION
        optimized_solution, best_iteration = static_optimization(network, initial_solution,
                                                                 required_requests_per_it=steep_descent_intensity,
                                                                 time_limit=opt_time_lim, capacity=capacity)
        opt_name = 'Results/' + network_size + '_' + str(sample) + '_' + str(phd) + 'phd' + '_opt.pickle'
        file_to_write_2 = open(opt_name, "wb")
        pickle.dump(optimized_solution, file_to_write_2)

        sample += 1


# DEPOT POSITION

for dep in depot_allocation:

    peak_duration = 60
    nb_of_available_vehicles = 16
    capacity = 20
    req_max_cluster_time = 20
    sample = 0

    while sample < nb_of_samples:
        print('CURRENTLY RUNNING: ', dep, 'as depot position', sample)
        random_seed = sample

        requests_per_od = generate_static_requests_2(mean_demand, peak_duration, set_seed=random_seed)
        total_nb_of_requests = count_total_requests(requests_per_od)

        all_static_requests, all_dynamic_requests = list_individual_requests(requests_per_od,
                                                                             dod=degree_of_dynamism,
                                                                             lead_time=lead_time,
                                                                             set_seed=random_seed)

        grouped_requests = group_requests_dt(all_static_requests, req_max_cluster_time, requests_per_od.keys())

        # INITIAL SOLUTION
        initial_solution = generate_initial_solution(network, grouped_requests,
                                                     nb_of_available_veh=nb_of_available_vehicles, capacity=capacity,
                                                     depot=dep)
        # init_name = 'Results/' + network_size + '_' + str(sample) + '_clust_' + str(h) + '_init'
        #
        # file_to_write_1 = open(init_name, "wb")
        # pickle.dump(initial_solution, file_to_write_1)

        # OPTIMIZED SOLUTION
        optimized_solution, best_iteration = static_optimization(network, initial_solution,
                                                                 required_requests_per_it=steep_descent_intensity,
                                                                 time_limit=opt_time_lim, capacity=capacity,
                                                                 depot=dep)
        opt_name = 'Results/' + network_size + '_' + str(sample) + '_' + dep + '_dep' + '_opt.pickle'
        file_to_write_2 = open(opt_name, "wb")
        pickle.dump(optimized_solution, file_to_write_2)

        sample += 1

