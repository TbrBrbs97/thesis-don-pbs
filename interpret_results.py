import os
import pandas as pd
from network_generation import generate_cost_matrix, import_network
from solution_evaluation import generate_waiting_time_dict, generate_in_vehicle_time_dict, \
    generate_total_travel_time_dict, generate_distance_matrix, get_objective_function_val, \
    sum_total_travel_time, calc_total_vehicle_kilometers, calc_occupancy_rate
from vehicle import count_total_assigned_requests, count_assigned_request_groups

directory = 'Results'
network = None

# STATIC EXPERIMENTS 1
export = dict()

for filename in os.listdir(directory):
    file = os.path.join(directory, filename)
    vehicles_schedule = pd.read_pickle(file)

    if 'small' in filename and 'half' in filename:
        network = import_network('small', 'half')
    elif 'small' in filename and 'more' in filename:
        network = import_network('small', 'more')
    if 'medium' in filename and 'half' in filename:
        network = import_network('medium', 'half')
    elif 'medium' in filename and 'more' in filename:
        network = import_network('medium', 'more')
    if 'large' in filename and 'half' in filename:
        network = import_network('large', 'half')
    elif 'large' in filename and 'more' in filename:
        network = import_network('large', 'more')
    if 'real' in filename and 'half' in filename:
        network = import_network('real', 'half')
    elif 'real' in filename and 'more' in filename:
        network = import_network('real', 'more')

    total_passenger_count = count_total_assigned_requests(vehicles_schedule)
    total_travel_time = get_objective_function_val(vehicles_schedule, relative=False)
    passenger_travel_time = get_objective_function_val(vehicles_schedule, relative=True)
    total_vehicle_kms = calc_total_vehicle_kilometers(network, vehicles_schedule)

    export[filename] = [total_passenger_count, total_travel_time, passenger_travel_time, total_vehicle_kms]

df = pd.DataFrame.from_dict(export, orient='index')
headers = ['total pass. count', 'total travel time', 'travel time per pass.', 'total veh. kms']
pd.DataFrame.to_csv(df, path_or_buf='Results/static_experiments_1.csv', header=headers)