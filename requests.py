import numpy as np
import pandas as pd
from random import choice, randint, seed


def get_scenario_mean_demand(direction, size, scen, peak=1):

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
    # create a list of the to terminal nodes and call it 'm'
    m = list(range(n, 2*n))
    demand_dict = {}
    
    for i in range(1, n+1):
        for j in range(1, n+1):
            if i < j:
                demand_dict[(i, j)] = df_meandemand_city.loc[(scen, i), j]
            else:
                demand_dict[(i, j)] = df_meandemand_terminal.loc[(scen, m[-i]), m[-j]]

    return demand_dict
    

def generate_static_requests(mean_demand, peak_hour_duration=60, set_seed=None):

    static_requests = {}

    for od in mean_demand.keys():
        if mean_demand[od] > 0:
    
            static_requests[od] = []
            static_requests[od].append(np.float64(0))

            t = 0

            while t < peak_hour_duration:
                if set_seed:
                    np.random.seed(set_seed)

                delta_t = np.random.exponential(1/mean_demand[od], 1)[0]  #the time before the next passenger arrives is sampled from an exponential distr.                              
                t += round(delta_t, 2)
            
                if t > peak_hour_duration:
                    break
                else:
                    static_requests[od].append(round(t, 2)) #if no request yet is at that time

    return static_requests


def list_individual_requests(requests_per_od, dod=0, lead_time=1, set_seed=None):

    all_static_requests, all_dynamic_requests = [], []

    for k in requests_per_od.keys():
        for v in requests_per_od[k]:
            all_static_requests.append((k, v, 0))

    amount_dynamic_requests = int(dod*len(all_static_requests))

    if set_seed:
        seed(set_seed)

    for count in range(amount_dynamic_requests):

        random_request = all_static_requests.pop(randint(0, len(all_static_requests)))

        editable_request = list(random_request)
        if random_request[1] < 1:
            editable_request[2] = randint(0, lead_time)
        else:
            editable_request[2] = randint(0, int(random_request[1])-lead_time)
        all_dynamic_requests.append([tuple(editable_request)])

    return all_static_requests, all_dynamic_requests


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
        list_requests_od = select_requests(requests, od)

        if len(list_requests_od) != 0:
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
    # print(request_group)
    o = request_group[0][0][0]
    d = request_group[0][0][1]

    return o, d


def get_max_pick_time(request_group):
    if len(request_group) != 0:
        return max([value[1] for value in request_group])
    else:
        return 0


def get_issue_time(request):
    """
    Returns the issue time of an individual request.
    """
    return request[0][2]


def pop_request_group(request_dictionairy, set_seed=True):
    '''
    Function that returns a random request group from the request dictionairy.
    '''

    if set_seed is True:
        seed(2022)

    random_od_pair = choice(list(request_dictionairy))
    while count_requests(request_dictionairy, random_od_pair) == 0:
        random_od_pair = choice(list(request_dictionairy))

    return choice(request_dictionairy[random_od_pair])


def remove_from_request_dictionairy(request_dictionairy, request_group):
    """
    Function that removes a request from the request dictionairy
    """

    o, d = get_od_from_request_group(request_group)
    request_dictionairy[(o, d)].remove(request_group)


def add_request_group_to_dict(request_group, request_dict=None):
    """
    Adds a request_group to a (temporary) request dictionairy.
    """
    if not request_dict:
        request_dict = dict()

    o, d = get_od_from_request_group(request_group)
    if (o, d) not in request_dict:
        request_dict[(o, d)] = []
    request_dict[(o, d)].append(request_group)

    return request_dict


def collect_request_until_time(dynamic_requests, time, lead_time=5):
    """
    Function that lists the request with an issue time up until 'lead_time' ago.
    Caution, the returned list might be empty!
    """
    return [request for request in dynamic_requests if get_issue_time(request) in range(time-lead_time, time)]