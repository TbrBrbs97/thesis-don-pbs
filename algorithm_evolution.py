
import pickle

from settings import v_mean, degree_of_dynamism, lead_time, steep_descent_intensity, depot

from network_generation import import_network, generate_cost_matrix, \
    get_network_boundaries, generate_distance_matrix

from requests import get_scenario_mean_demand, list_individual_requests, convert_md_todict, \
    generate_static_requests_2, group_requests_dt, count_total_requests

from solution_construct import generate_initial_solution, static_optimization

# SETTINGS

network_size = 'real'
network_variant = 'half'

opt_time_lim = 240
peak_duration = 120
nb_of_available_vehicles = 16
capacity = 20
req_max_cluster_time = 15

network = import_network(network_size, network_variant)
cost_matrix = generate_cost_matrix(network, v_mean)
distance_matrix = generate_distance_matrix(network)
network_dim = get_network_boundaries(network)

demand_scenario = 2
demand_subscenario = 2


lambdapeak = get_scenario_mean_demand('city', network_size, scen=demand_scenario,
                                      subscen=demand_subscenario, peak=1)
mupeak = get_scenario_mean_demand('terminal', network_size, scen=demand_scenario,
                                  subscen=demand_subscenario, peak=1)

if network_size != 'real':
    mean_demand = convert_md_todict(lambdapeak, mupeak, scen=demand_scenario)
else:
    mean_demand = convert_md_todict(lambdapeak, mupeak, scen=demand_scenario, subscen=demand_subscenario)

sample = 1
print('CURRENTLY RUNNING scenario: ', demand_scenario, 'and subscenario:', demand_subscenario)
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
                                             nb_of_available_veh=nb_of_available_vehicles,
                                             capacity=capacity, depot=depot)

# OPTIMIZED SOLUTION
optimized_solution, best_iteration, list_solutions = static_optimization(network, initial_solution,
                                                                    required_requests_per_it=steep_descent_intensity,
                                                                time_limit=opt_time_lim, capacity=capacity, depot=depot,
                                                                record_state=True)
list_name = 'Results/SE_0/vns_evolution.pickle'
files_to_write_0 = open(list_name, "wb")
pickle.dump(list_solutions, files_to_write_0)

opt_name = 'Results/SE_0/' + network_size + '_scen' + str(demand_scenario) + '_subscen' + str(demand_subscenario) + '_opt.pickle'
file_to_write_2 = open(opt_name, "wb")
pickle.dump(optimized_solution, file_to_write_2)

