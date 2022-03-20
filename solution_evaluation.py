
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


def get_req_ivt(request, vehicle, solution):
    pickup = request[0][0]
    dropoff = request[0][1]

    ivt = solution[vehicle][dropoff][0] - solution[vehicle][pickup][0]

    return ivt


def calc_in_vehicle_time(solution):
    ivt_dict = {}

    for v in solution.keys():
        ivt_dict[v] = {}
        for s in solution[v]:
            ivt_dict[v][s] = []
            for rg in range(1, len(solution[v][s])):
                for req in range(len(solution[v][s][rg])):
                    if solution[v][s][rg][req][0][0] == s:
                        ivt = get_req_ivt(solution[v][s][rg][req], v, solution)
                        ivt_dict[v][s].append(ivt)

    return ivt_dict


def calculate_ttt(ivt_dict, wt_dict):
    ttt_dict = {}

    for v in ivt_dict.keys():
        ttt_dict[v] = {}
        for s in ivt_dict[v]:
            ttt_dict[v][s] = list(range(len(ivt_dict[v][s])))
            for t in range(len(ivt_dict[v][s])):
                if len(ivt_dict[v][s]) != 0 and len(wt_dict[v][s]) != 0:
                    ttt_dict[v][s][t] = ivt_dict[v][s][t] + wt_dict[v][s][t]

    return ttt_dict


# maybe also provide the ability to sum per request group? for later swappings
def sum_total_tt(ttt_dict, level='vehicle'):

    if level == 'stop':
        result = {v: {s: sum([r for r in ttt_dict[v][s]]) for s in ttt_dict[v]} for v in ttt_dict}
    elif level == 'vehicle':
        result = {v: sum([sum([r for r in ttt_dict[v][s]]) for s in ttt_dict[v]]) for v in ttt_dict}
    else:
        result = sum([sum([sum([r for r in ttt_dict[v][s]]) for s in ttt_dict[v]]) for v in ttt_dict])

    return result


def get_objective_function_val(solution):
    wt = calc_waiting_time(solution)
    ivt = calc_waiting_time(solution)
    total_travel_time = calculate_ttt(ivt, wt)

    return round(sum_total_tt(total_travel_time, 'total'), 2)


def calc_occupancy_rate(solution, capacity):
    # [1:] slice: because the departure time should not be counted!
    return {v: {s: len([j for i in solution[v][s][1:] for j in i])/capacity for s in solution[v]} for v in solution}


### TEST FUNCTIONS:

# fucntion that asserts that no vehicle goes over its capacity at no stop
# function that asserts that departure time goes up!

