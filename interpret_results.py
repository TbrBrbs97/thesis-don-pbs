import os
import pandas as pd
import matplotlib.pyplot as plt
from network_generation import generate_cost_matrix, import_network
from solution_evaluation import generate_waiting_time_dict, generate_in_vehicle_time_dict, \
    generate_total_travel_time_dict, generate_distance_matrix, get_objective_function_val, \
    sum_total_travel_time, calc_total_vehicle_kilometers, calc_request_group_invehicle_time, \
    calc_request_group_waiting_time
from vehicle import count_total_assigned_requests, list_assigned_travellers, count_assigned_request_groups_2

# ADJUST NAMING BEFORE RUNNING !!

directory = 'Results/DE_1'
output_name = 'dynamic_experiments_1_3005'
network = None

# GENERATE EXPORT

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
    else:
        network = import_network('real', 'half')

    waiting_time = generate_waiting_time_dict(vehicles_schedule)
    in_veh_time = generate_in_vehicle_time_dict(network, vehicles_schedule)

    total_passenger_count = count_total_assigned_requests(vehicles_schedule, dynamic=False)
    total_travel_time = get_objective_function_val(network, vehicles_schedule, relative=False)
    summed_waiting_time = sum_total_travel_time(waiting_time)
    summed_in_veh_time = sum_total_travel_time(in_veh_time)
    passenger_travel_time = get_objective_function_val(network, vehicles_schedule, relative=True)
    total_vehicle_kms = calc_total_vehicle_kilometers(network, vehicles_schedule)

    assigned_request_groups = count_assigned_request_groups_2(vehicles_schedule)

    city_travellers_tt = get_objective_function_val(network, vehicles_schedule, relative=True, direction='city')
    terminal_travellers_tt = get_objective_function_val(network, vehicles_schedule, relative=True, direction='terminal')

    count_city_travellers = count_total_assigned_requests(vehicles_schedule, direction='city')
    count_terminal_travellers = count_total_assigned_requests(vehicles_schedule, direction='terminal')

    city_wt_dict = generate_waiting_time_dict(vehicles_schedule, direction='city')
    city_ivt_dict = generate_in_vehicle_time_dict(network, vehicles_schedule, direction='city')

    terminal_wt_dict = generate_waiting_time_dict(vehicles_schedule, direction='terminal')
    terminal_ivt_dict = generate_in_vehicle_time_dict(network, vehicles_schedule, direction='terminal')

    city_travellers_wt = sum_total_travel_time(city_wt_dict) / count_city_travellers
    city_travellers_ivt = sum_total_travel_time(city_ivt_dict) / count_city_travellers
    terminal_travellers_wt = sum_total_travel_time(terminal_wt_dict) / max(count_terminal_travellers, 1)
    terminal_travellers_ivt = sum_total_travel_time(terminal_ivt_dict) / max(count_terminal_travellers, 1)

    in_advance_travellers =  count_total_assigned_requests(vehicles_schedule, dynamic=False) - \
                             count_total_assigned_requests(vehicles_schedule, dynamic=True)
    real_time_travellers = count_total_assigned_requests(vehicles_schedule, dynamic= True)

    list_real_time_travellers = list_assigned_travellers(vehicles_schedule, dynamic=True)

    # PLOT
    if 'dyn' in filename:
        x = [abs(tup[0][1]-tup[0][2]) for tup in list_real_time_travellers]
        y = [calc_request_group_invehicle_time(network, vehicles_schedule, group) +
             calc_request_group_waiting_time(vehicles_schedule, group) for group in list_real_time_travellers]
        z = [tup[0][1] for tup in list_real_time_travellers]
        plt.scatter(x, y, c=z)
        plt.xlabel("Difference between pick up time - issue time (min.)")
        plt.ylabel("Travel time (min.)")
        plt.colorbar()
        plt.show()

    in_advance_travel_time = get_objective_function_val(network, vehicles_schedule, relative=False, direction='all', dynamic_filter=False) - \
                             get_objective_function_val(network, vehicles_schedule, relative=False, direction='all', dynamic_filter=True)
    real_time_travel_time = get_objective_function_val(network, vehicles_schedule, relative=False, direction='all', dynamic_filter=True)

    export[filename] = [total_passenger_count, summed_waiting_time, summed_in_veh_time,
                        total_travel_time, passenger_travel_time, total_vehicle_kms,
                        count_city_travellers, count_terminal_travellers,
                        city_travellers_tt, terminal_travellers_tt,
                        city_travellers_wt, city_travellers_ivt,
                        terminal_travellers_wt, terminal_travellers_ivt,
                        in_advance_travellers, real_time_travellers,
                        in_advance_travel_time, real_time_travel_time]


df = pd.DataFrame.from_dict(export, orient='index')
headers = ['total pass. count', 'total waiting time', 'total in-veh. time',
           'total travel time', 'travel time per pass.', 'total veh. kms',
           'total city travelers', 'total terminal travelers',
           'avg. travel time to city', 'avg. travel time to terminal',
           'wt city travel', 'ivt city travel',
           'wt terminal travel', 'ivt terminal travel',
           'in-advance pass. count', 'real-time pass. count',
           'in-advance tt', 'real-time tt']
output_path = directory + '_' + output_name + '.csv'
pd.DataFrame.to_csv(df, path_or_buf=output_path, header=headers)
