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

# print('initial solution: ', initial_solution[(2, 1)])
# print('original travel cost: ', se.get_objective_function_val(initial_solution))

# # REMOVE
# request_to_be_removed = initial_solution[(1, 1)][1][1]
# od = rg.get_od_from_request_group(request_to_be_removed)
# print(od[0])

#
# print('requests to be removed: ', request_to_be_removed)
#
#
# br.remove_request_group(test_solution, (1, 1), request_to_be_removed, od_matrix, network_dim)
#
# # REINSERT
# br.insert_request_group(test_solution, (2, 1), request_to_be_removed, od_matrix, network_dim)
# print('new solution: ', test_solution[(2, 1)])
# print('new travel cost: ', se.get_objective_function_val(test_solution))

best_to_remove = br.select_most_costly_request(test_solution, od_matrix, network_dim)
print(best_to_remove)

# [:2] because we don't need the position of the request group within the group
excluded_pos = sg.get_request_group_position(test_solution, best_to_remove)[:2]
best_to_reinsert = br.find_best_insertion(test_solution, best_to_remove, excluded_pos)
print(best_to_reinsert)
print(vg.is_empty_stop(test_solution, (4,1), 1))
#print(test_solution)
