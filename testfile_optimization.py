# PACKAGES

import pickle
import copy
import pandas

import break_and_repair_op as br
import network_generation as netg
import solution_generation as sg
import solution_evaluation as se
import vehicle_generation as vg
import solution_visualisation as sv

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

dict = {(1, 1): {1: [3.8, [((1, 3), 0, 0), ((1, 3), 0.2, 0), ((1, 3), 0.4, 0), ((1, 3), 0.6, 0), ((1, 3), 0.8, 0), ((1, 3), 1.0, 0), ((1, 3), 1.2, 0), ((1, 3), 1.4, 0), ((1, 3), 1.6, 0), ((1, 3), 1.8, 0), ((1, 3), 2.0, 0), ((1, 3), 2.2, 0), ((1, 3), 2.4, 0), ((1, 3), 2.6, 0), ((1, 3), 2.8, 0), ((1, 3), 3.0, 0), ((1, 3), 3.2, 0), ((1, 3), 3.4, 0), ((1, 3), 3.6, 0), ((1, 3), 3.8, 0)]], 2: [9.77, [((1, 3), 0, 0), ((1, 3), 0.2, 0), ((1, 3), 0.4, 0), ((1, 3), 0.6, 0), ((1, 3), 0.8, 0), ((1, 3), 1.0, 0), ((1, 3), 1.2, 0), ((1, 3), 1.4, 0), ((1, 3), 1.6, 0), ((1, 3), 1.8, 0), ((1, 3), 2.0, 0), ((1, 3), 2.2, 0), ((1, 3), 2.4, 0), ((1, 3), 2.6, 0), ((1, 3), 2.8, 0), ((1, 3), 3.0, 0), ((1, 3), 3.2, 0), ((1, 3), 3.4, 0), ((1, 3), 3.6, 0), ((1, 3), 3.8, 0)]], 3: [15.74, [((3, 5), 0, 0), ((3, 5), 7.96, 0)], [((3, 4), 0, 0), ((3, 4), 7.96, 0)]], 4: [21.71, [((3, 5), 0, 0), ((3, 5), 7.96, 0)], [((4, 5), 0, 0)]], 5: [27.68]}}
#print([len(dict[(1, 1)][s]) > 1 for s in dict[(1, 1)] if s < vg.get_last_stop(dict, (1, 1))])

print('initial solution: ', initial_solution[(10, 1)])

request_to_be_removed = initial_solution[(9, 1)][1][1]
print(request_to_be_removed)

br.remove_request_group(test_solution, (9, 1), request_to_be_removed, od_matrix, network_dim)
print('original travel cost: ', se.get_objective_function_val(test_solution))
br.insert_request_group(test_solution, (10, 1), request_to_be_removed, od_matrix, network_dim)
print('new travel cost: ', se.get_objective_function_val(test_solution))

print('adapted solution: ')
print(test_solution[(10, 1)])
# Errors:
# Add_pax_to_veh doesn't account for correct departure times
# Sorting doesn't seem to work
