#  Packages

import pickle
import pandas

import break_and_repair_op
import solution_generation
import solution_evaluation
import solution_visualisation

# Import initial solution

with open('Exports/initial_solution.pickle', 'rb') as handle:
    initial_solution = pickle.load(handle)

print(initial_solution[(1, 1)])