import pickle
import os
from pandas import read_pickle, DataFrame
from solution_evaluation import calc_total_vehicle_kilometers, sum_total_travel_time, generate_total_travel_time_dict, \
    get_objective_function_val, generate_waiting_time_dict, generate_in_vehicle_time_dict, calc_total_vehicle_duration, \
    calc_total_stopping_time
from network_generation import import_network, generate_cost_matrix
from vehicle import get_nodes_in_range, count_total_assigned_requests, count_assigned_request_groups_2, \
    count_boarding_pax_until_dest, count_inveh_pax_over_node, requests_per_node

directory = 'Results/SE_3'
output_dir = 'Results/Schedules/'
files = []
networks = []

for filename in os.listdir(directory):
    file = os.path.join(directory, filename)
    files.append(file)

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

    networks.append(network)

instances = list(range(len(files)))

for inst in instances:
    sched = files[inst]
    net = networks[inst]

    filename = files[inst][13:-7]

    # print(generate_cost_matrix(net, v_mean=50))

    print('Returning results for: ', sched)
    vehicles_schedule = read_pickle(sched)
    # for i in vehicles_schedule:
    #     print('veh ', i, ': ', vehicles_schedule[i], len(get_nodes_in_range(vehicles_schedule, i)))
    #
    # print('tot. veh km', calc_total_vehicle_kilometers(net, vehicles_schedule))
    # print('obj. func: ', get_objective_function_val(net, vehicles_schedule))
    # print('tot. ind. requests', count_total_assigned_requests(vehicles_schedule))
    # print('tot. request groups', count_assigned_request_groups_2(vehicles_schedule))
    #
    # print('objective func: ', get_objective_function_val(net, vehicles_schedule, relative=False))
    # print('assigned ind. requests', count_total_assigned_requests(vehicles_schedule))
    # print('assigned request groups', count_assigned_request_groups_2(vehicles_schedule))
    #
    # waiting_time = generate_waiting_time_dict(vehicles_schedule)
    # in_veh_time = generate_in_vehicle_time_dict(net, vehicles_schedule)
    #
    # print('avg. waiting time: ', sum_total_travel_time(waiting_time))
    # print('avg. in-vehicle time: ', sum_total_travel_time(in_veh_time))

    # print('tot. veh duration: ', calc_total_vehicle_duration(net, vehicles_schedule))
    # print('tot veh. idle time: ', calc_total_stopping_time(net, vehicles_schedule))
    print('relative idle time:', calc_total_stopping_time(net, vehicles_schedule) / calc_total_vehicle_duration(net, vehicles_schedule))
    # print('waiting time at stops: ', sum_total_travel_time(in_veh_time) - calc_total_vehicle_duration(net, vehicles_schedule))
