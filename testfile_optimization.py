# PACKAGES

import pickle
import copy
import time
import pandas

import break_and_repair_op as br
import network_generation as netg
import requests_generation as rg
import solution_generation as sg
import solution_evaluation as se
import vehicle_generation as vg
import solution_visualisation as sv
import static_optimization as so

# PARAMETERS & OD-MATRIX

network_size = 'small'
interstop_distance = 'half'
v_mean = 50 # km/h

network = netg.import_network(network_size, interstop_distance)
od_matrix = netg.generate_tt_od(network, v_mean)
network_dim = netg.get_network_boundaries(network)

# IMPORT INITIAL SOLUTION

with open('Exports/initial_solution.pickle', 'rb') as handle:
    initial_solution = pickle.load(handle)

# TESTS

test_solution = copy.deepcopy(initial_solution)

print(se.get_objective_function_val(initial_solution))
new_solution = so.static_opt(test_solution, nb_of_iterations=10)
print(se.get_objective_function_val(new_solution))
