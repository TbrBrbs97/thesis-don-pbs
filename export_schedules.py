import os
from network_generation import import_network, generate_cost_matrix, cv
from pandas import read_pickle, DataFrame, ExcelWriter
from vehicle import requests_per_node, boarding_pass_at_node, \
    get_nodes_in_range, get_prev_node, get_departure_time_at_node


def hours_minutes(minutes):
    time = 8*60 + minutes
    h = int(time / 60)
    m = int(time %  60)

    if m < 10:
        return str(h) + ':0' + str(m)
    else:
        return str(h) + ':' + str(m)

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

# print(files)

instances = [7]

for inst in instances:
    sched = files[inst]
    net = networks[inst]
    cost_matrix = generate_cost_matrix(net, v_mean=50)

    filename = files[inst][13:-7]
    output_name = output_dir + 'schedule_' + filename + '.xlsx'
    writer = ExcelWriter(output_name, engine='openpyxl') # or 'xlsxwriter'

    print('Returning results for: ', sched)
    vehicles_schedule = read_pickle(sched)
    pass_per_node = requests_per_node(vehicles_schedule)

    for veh in pass_per_node:
        export_dict = dict()
        export_dict['Stop'] = []
        export_dict['Arr'] = []
        export_dict['Dep'] = []
        export_dict['Pass. aboard'] = []

        all_stops = get_nodes_in_range(vehicles_schedule, veh)

        for stop in pass_per_node[veh]:
            export_dict['Stop'].append(cv(stop))

            if all_stops.index(stop) > 0:
                prev_stop = get_prev_node(vehicles_schedule, veh, node=stop)
                previous_departure = get_departure_time_at_node(vehicles_schedule, veh, prev_stop)

                to_convert = previous_departure + cost_matrix[cv(prev_stop), cv(stop)]
                export_dict['Arr'].append(hours_minutes(to_convert))
            else:
                previous_departure = 0
                export_dict['Arr'].append(hours_minutes(get_departure_time_at_node(vehicles_schedule, veh, stop)))

            export_dict['Dep'].append(hours_minutes(get_departure_time_at_node(vehicles_schedule, veh, stop)))

            if boarding_pass_at_node(pass_per_node, veh, stop):
                export_dict['Pass. aboard'].append(sum(pass_per_node[veh][stop][1:]))
            else:
                export_dict['Pass. aboard'].append(0)

        sheetname = 'Veh ' + str(veh)
        df = DataFrame(export_dict)
        df.to_excel(writer, sheet_name=sheetname)

    writer.save()



