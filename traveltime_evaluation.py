import numpy as np

def calc_waiting_time(solution):
    wt_dict = {}

    for v in solution.keys():
        wt_dict[v] = {}
        for s in solution[v]:
            wt_dict[v][s] = []
            for rg in range(1, len(solution[v][s])):
                for req in range(len(solution[v][s][rg])):
                    # only if the starting station is equal to the stop > this is where the waiting time counts
                    if solution[v][s][rg][req][0][0] == s:
                        wt = abs(solution[v][s][rg][req][1] - solution[v][s][0])
                        wt_dict[v][s].append(wt)

    return wt_dict


def get_served_stops(solution, vehicle):
    # this is only for vehicle v!
    # check for every stop what the origin and destination of stops are
    served_stops = set(())
    for s in solution[vehicle]:
        for rg in range(1, len(solution[vehicle][s])):
            for req in solution[vehicle][s][rg]:
                served_stops.add(req[0][0])  # add the origin and destination
                served_stops.add(req[0][1])

    return served_stops


def get_req_ivt(request, stops_served, od_matrix):
    pickup = request[0][0]
    dropoff = request[0][1]

    ivt = 0

    for i in range(pickup, dropoff):
        if i+1 in stops_served:
            ivt += od_matrix[(i, i+1)]

    return ivt


def calc_in_vehicle_time(solution, od_matrix):
    ivt_dict = {}

    for v in solution.keys():
        ivt_dict[v] = {}
        stops_made = get_served_stops(solution, v)
        for s in solution[v]:
            ivt_dict[v][s] = []
            for rg in range(1, len(solution[v][s])):
                for req in range(len(solution[v][s][rg])):
                    if solution[v][s][rg][req][0][0] == s:
                        ivt = get_req_ivt(solution[v][s][rg][req], stops_made, od_matrix)
                        ivt_dict[v][s].append(ivt)

    return ivt_dict


def calculate_ttt(ivt_dict, wt_dict):
    ttt_dict = {}

    for v in ivt_dict.keys():
        ttt_dict[v] = {}
        for s in ivt_dict[v]:
            ttt_dict[v][s] = list(range(len(ivt_dict[v][s])))
            for t in range(len(ivt_dict[v][s])):
                f = ivt_dict[v][s]
                if len(ivt_dict[v][s]) != 0 and len(wt_dict[v][s]) != 0:
                    ttt_dict[v][s][t] = ivt_dict[v][s][t] + wt_dict[v][s][t]

    return ttt_dict


# maybe also provide the ability to sum per request group?
def sum_total_tt(ttt_dict, level='vehicle'):

    if level == 'stop':
        result = {v: {s: sum([r for r in ttt_dict[v][s]]) for s in ttt_dict[v]} for v in ttt_dict}
    elif level == 'vehicle':
        result = {v: sum([sum([r for r in ttt_dict[v][s]]) for s in ttt_dict[v]]) for v in ttt_dict}
    else:
        result = sum([sum([sum([r for r in ttt_dict[v][s]]) for s in ttt_dict[v]]) for v in ttt_dict])

    return result

