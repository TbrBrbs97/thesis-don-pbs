import math
import pandas as pd


def import_network(size, interstop_distance):
    if size == 'small':
        size_name = 'small'
    elif size == 'medium':
        size_name = 'medium'
    elif size == 'large':
        size_name = 'real'
    else:
        size_name = 'real'

    if interstop_distance == 'half':
        distance_name = 'half'
    else:
        distance_name = 'more'

    path_name = 'Data/Benchmark Lines/' + size_name + 'euc' + distance_name + '.xlsx'
    excel = pd.read_excel(path_name, engine='openpyxl', sheet_name=0, header=0, index_col=0, dtype=float)
    df = excel.to_dict('index')

    return df


def calculate_euclidean_dist(x1, y1, x2, y2):
    result = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
    return result


def generate_cost_matrix(network, v_mean):
    
    cost_matrix = {}

    for i in network.keys():
        x_a, y_a = network[i]['x-coord'], network[i]['y-coord']
        for j in network.keys():
            x_b, y_b = network[j]['x-coord'], network[j]['y-coord']
            distance = calculate_euclidean_dist(x_a, y_a, x_b, y_b)
            travel_time = (distance / v_mean)*60  # to get the travel time in minutes
            
            cost_matrix[(i, j)] = round(travel_time, 2)
            
    return cost_matrix


def generate_distance_matrix(network):

    distance_matrix = {}

    for i in network.keys():
        x_a, y_a = network[i]['x-coord'], network[i]['y-coord']
        for j in network.keys():
            x_b, y_b = network[j]['x-coord'], network[j]['y-coord']
            distance = calculate_euclidean_dist(x_a, y_a, x_b, y_b)
            distance_matrix[(i, j)] = round(distance, 2)

    return distance_matrix


def calc_average_interstop_distance(network):
    distance_matrix = generate_distance_matrix(network)
    distance_list = []
    for i, j in distance_matrix:
        if i != j:
            distance_list.append(distance_matrix[i, j])
    return round(sum(distance_list)/len(distance_list), 2)


def get_network_boundaries(network):
    all_stops = set(network.keys())

    terminal = min(all_stops)
    terminal_end = max(all_stops)
    city = round(terminal_end/2) + 1

    return terminal, city, terminal_end


def cv(node):
    """
    Converts a node of the form 'node, occ' to 'node', which can be understood by the distance/cost matrix
    """
    sep = node.index(',')
    return int(node[:sep])
