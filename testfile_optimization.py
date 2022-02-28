# PACKAGES

import pickle
import copy
import pandas

import break_and_repair_op as br
import network_generation as netg
import solution_generation as sg
import solution_evaluation as se
import solution_visualisation as sv

# PARAMETERS & OD-MATRIX

network_size = 'small'
interstop_distance = 'half'
v_mean = 50 # km/h

network = netg.import_network(network_size, interstop_distance)
od_matrix = netg.generate_tt_od(network, v_mean)


# IMPORT INITIAL SOLUTION

with open('Exports/initial_solution.pickle', 'rb') as handle:
    initial_solution = pickle.load(handle)

# TESTS

#test_solution = copy.deepcopy(initial_solution)

#request_to_be_removed = initial_solution[(1, 1)][1][1]
#br.remove_request_group(test_solution, (1, 1), request_to_be_removed, od_matrix)

#print(request_to_be_removed)
#print(br.get_max_pick_time(request_to_be_removed))
#print(initial_solution[(1, 1)])
#print(test_solution[(1, 1)])