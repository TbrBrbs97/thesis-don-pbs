# PACKAGES

import pickle
import copy
import time
import pandas

import break_and_repair as br
import network_generation as netg
import requests as rg
import solution_generation as sg
import solution_evaluation as se
import vehicle as vg
import solution_visualisation as sv
import static_optimization as so

# PARAMETERS & OD-MATRIX

network_size = 'small'
interstop_distance = 'half'
v_mean = 50 # km/h

network = netg.import_network(network_size, interstop_distance)
od_matrix = netg.generate_cost_matrix(network, v_mean)
network_dim = netg.get_network_boundaries(network)

# IMPORT INITIAL SOLUTION

with open('Exports/initial_solution.pickle', 'rb') as handle:
    initial_solution = pickle.load(handle)

# TESTS

test_solution = copy.deepcopy(initial_solution)

# r1 = [((3, 5), 47.76, 0), ((3, 5), 55.72, 0)]
# br.remove_request_group(test_solution, r1)

print(se.get_objective_function_val(initial_solution))
new_solution = so.static_opt(test_solution, treated_requests_per_it=3, nb_of_iterations=2)
print(se.get_objective_function_val(new_solution))
