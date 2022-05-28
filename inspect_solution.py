import pickle
import os
from pandas import read_pickle
from solution_evaluation import calc_total_vehicle_kilometers, sum_total_travel_time, generate_total_travel_time_dict
from network_generation import import_network
from vehicle import get_nodes_in_range

directory = 'Results/SE_3'
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

file = files[1]
net = networks[1]

vehicles_schedule = read_pickle(file)
for i in vehicles_schedule:
    print('veh ', i, ': ', vehicles_schedule[i], len(get_nodes_in_range(vehicles_schedule, i)))

print(sum([len(get_nodes_in_range(vehicles_schedule, i)) for i in vehicles_schedule])/len(vehicles_schedule))
print(calc_total_vehicle_kilometers(net, vehicles_schedule, list_per_vehicle=True))

dict_total_tt = generate_total_travel_time_dict(vehicles_schedule)
summed_per_veh = sum_total_travel_time(dict_total_tt, 'vehicle')
print(summed_per_veh)