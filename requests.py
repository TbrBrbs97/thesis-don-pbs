import numpy as np
import pandas as pd
import random


def get_scenario_mean_demand(direction, size, scen, peak=1): #add size as a parameter later

    if size == 'small':
        size_name = 'Small3'
    elif size == 'medium':
        size_name = 'Medium3'
    else:
        size_name = 'Real3'

    if peak == 1:
        sheet_lambda = 0
        sheet_mu = 1
    else:
        sheet_lambda = 2
        sheet_mu = 3

    path_name = 'Data/Demand rates/DemandInput' + size_name + '.xlsx'

    df_lambda = pd.read_excel(path_name, engine='openpyxl', sheet_name=sheet_lambda,header=0, index_col=(0,1), dtype=float)
    df_mu = pd.read_excel(path_name, engine='openpyxl', sheet_name=sheet_mu, header=0, index_col=(0,1), dtype=float)

    if direction == 'city':
        df = df_lambda
        n = len(df.iloc[0])
        a = 1

        return df.loc[(scen,a):(scen,n),1:n]

    else: 
        df = df_mu
        n = len(df.iloc[0])
        a = n
    
        return df.loc[(scen, a):(scen, 2*n-1), 1:2*n-1]
    

def convert_md_todict(df_meandemand_city, df_meandemand_terminal, scen):
    n = len(df_meandemand_city.iloc[0])
    demand_dict = {}
    
    for i in range(1, n+1):
        for j in range(1, n+1):
            if i < j:
                demand_dict[(i, j)] = df_meandemand_city.loc[(scen, i), j]
            else:
                demand_dict[(i, j)] = df_meandemand_terminal.loc[(scen, i + 2*(n-i)**i), j + 2*(n-j)**j]

    return demand_dict
    

def generate_requests(mean_demand, peak_hour_duration=60, seed=True):

    requests = {}

    for od in mean_demand.keys():
        if mean_demand[od] > 0:
    
            requests_od = []
            requests[od] = requests_od
            requests[od].append(np.float64(0))

            t = 0

            while t < peak_hour_duration:
                if seed is True:
                    np.random.seed(0)

                delta_t = np.random.exponential(1/mean_demand[od], 1)[0]  #the time before the next passenger arrives is sampled from an exponential distr.                              
                t += round(delta_t, 2)
            
                if t > peak_hour_duration:
                    break
                else:
                    requests[od].append(round(t, 2)) #if no request yet is at that time

    return requests


def list_all_requests(requests_per_od):

    lst_small_requests = []

    for k in requests_per_od.keys():
        for v in requests_per_od[k]:
            lst_small_requests.append((k, v, 0))
        
    return lst_small_requests


def select_requests(requests, od):
    return [x for x in requests if x[0] == od]


def group_requests_es(requests, groupsize, od_pairs):
    requests_dict = {}
    for od in od_pairs:
        requests_dict[od] = [select_requests(requests, od)[x:x + groupsize] for x in
                             range(0, len(select_requests(requests, od)), groupsize)]

    return requests_dict


def group_requests_dt(requests, dep_t_th, od_pairs):

    grouped_requests = {}

    for od in od_pairs:
        grouped_requests[od] = []
        list_requests_od =select_requests(requests, od)

        first_dep = list_requests_od[0]
        group = [first_dep]
        grouped_requests[od].append(group)
        r = 1

        while r < len(list_requests_od):
            if list_requests_od[r][1] > first_dep[1] + dep_t_th:
                first_dep = list_requests_od[r]
                group = [first_dep]
                grouped_requests[od].append(group)
            else:
                group.append(list_requests_od[r])

            r += 1

    return grouped_requests


def count_requests_per_od(grouped_requests):
    result = {}

    for od in grouped_requests.keys():
        result[od] = []
        for r in grouped_requests[od]:
            result[od].append(len(r))
        result[od] = sum(result[od])

    return result


def size_request_groups_per_od(grouped_requests):
    '''
    Function that returns the size of request groups per od
    '''
    result = {}

    for od in grouped_requests.keys():
        result[od] = []
        for r in grouped_requests[od]:
            result[od].append(len(r))

    return result


def count_requests(request_dict, od=None):
    count = 0

    if od is None:
        for k in request_dict.keys():
            count += len([j for i in request_dict[k] for j in i])
    else:
        count += len([j for i in request_dict[od] for j in i])

    return count


def get_od_from_request_group(request_group):
    o = request_group[0][0][0]
    d = request_group[0][0][1]

    return o, d


def get_max_pick_time(request_group):
    # returns the latest pickup time from a group of requests

    if len(request_group) != 0:
        return max([value[1] for value in request_group])
    elif type(request_group[0]) == np.float64:
        return request_group[0]
    else:
        return 0


def pop_request(request_dictionairy):
    '''
    Function that returns a random request group from the request dictionairy.
    '''

    random_od_pair = random.choice(list(request_dictionairy))
    while count_requests(request_dictionairy, random_od_pair) == 0:
        random_od_pair = random.choice(list(request_dictionairy))

    return random.choice(request_dictionairy[random_od_pair])


def remove_from_request_dictionairy(request_dictionairy, request_group):
    """
    Function that removes a request from the request dictionairy
    """

    o, d = get_od_from_request_group(request_group)
    request_dictionairy[(o, d)].remove(request_group)

