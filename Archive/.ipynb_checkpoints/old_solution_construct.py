def steepest_descent_2(vehicles_schedule, request_group):
    """
    Function that removes a request group from the vehicle schedule and reinserts it in the best possible spot.
    This is the spot that yields the best improving opportunity cost.
    """

    original_score = round(calc_request_group_opportunity_cost(vehicles_schedule, request_group), 2)
    temp_schedule = deepcopy(vehicles_schedule)
    remove_request_group(temp_schedule, request_group)
    temp_request_dict = dict()

    positions = []
    assigned_so_far = []
    while len(assigned_so_far) != len(request_group):

        portion_to_add = [r for r in request_group if r not in assigned_so_far]
        candidate_vehicle, candidate_node, score, added_portion = find_best_improvement_for_request_group(
            temp_schedule, portion_to_add, original_score)
        insert_request_group(temp_schedule, temp_request_dict, portion_to_add,
                             candidate_vehicle, candidate_node, ignore_request_dict=True)

        positions.append((added_portion, candidate_vehicle, candidate_node, score))
        assigned_so_far += added_portion
        if candidate_node != 'current pos':
            original_score -= calc_request_group_opportunity_cost(temp_schedule, added_portion)

    if all([candidate[2] != 'current pos' for candidate in positions]):
        vehicles_schedule = temp_schedule

    return vehicles_schedule


def large_shuffle(vehicles_schedule, temp_request_dict=None, shuffle_rate=shuffle_ratio):
    """
    Function which shakes a solution schedule by a large amount. The shaking process goes as follows:
    """

    if not temp_request_dict:
        temp_request_dict = dict()

    request_groups_to_select = int(round(shuffle_rate * count_assigned_request_groups(vehicles_schedule)))
    random_request_groups = select_random_request_groups(vehicles_schedule, request_groups_to_select)

    for request_group in random_request_groups:
        # original_obj_func_value = get_objective_function_val(vehicles_schedule)
        original_score = calc_request_group_opportunity_cost(vehicles_schedule, request_group)

        temp_schedule = copy.deepcopy(vehicles_schedule)
        # print(count_total_assigned_requests(vehicles_schedule))

        remove_request_group(temp_schedule, request_group)
        temp_request_dict = add_request_group_to_dict(request_group, temp_request_dict)
        # candidate_vehicle, candidate_node, score = find_first_best_improvement_for_request_group(temp_schedule,
        #                                                                                          request_group, original_score=M/4)
        candidate_vehicle, candidate_node, score = find_first_best_improvement_for_request_group_2(temp_schedule,
                                                                                                 request_group, original_score=original_score)

        # TODO check if you have to constrain position by 'if obj_func of temp < original schedule AFTER insertion in temp above!
        # if get_objective_function_val(temp_schedule) < original_obj_func_value:
        # if the result is satisfactory, perform it on the original vehicles schedule

        if candidate_node != 'current pos':
            remove_request_group(vehicles_schedule, request_group)
            insert_request_group(vehicles_schedule, temp_request_dict, request_group, candidate_vehicle, candidate_node)

    return vehicles_schedule


def large_shuffle_2(vehicles_schedule, temp_request_dict=None, shuffle_rate=shuffle_ratio):
    """
    Function which shakes a solution schedule by a large amount. The shaking process goes as follows:
    """

    if not temp_request_dict:
        temp_request_dict = dict()

    request_groups_to_select = int(round(shuffle_rate * count_assigned_request_groups(vehicles_schedule)))
    random_request_groups = select_random_request_groups(vehicles_schedule, request_groups_to_select)

    for request_group in random_request_groups:
        original_obj_func_value = get_objective_function_val(vehicles_schedule)
        temp_schedule = copy.deepcopy(vehicles_schedule)

        remove_request_group(temp_schedule, request_group)
        temp_request_dict = add_request_group_to_dict(request_group, temp_request_dict)
        candidate_vehicle, candidate_node, score = find_best_position_for_request_group(temp_schedule, request_group)

        if get_objective_function_val(temp_schedule) < original_obj_func_value:
            remove_request_group(vehicles_schedule, request_group)
            insert_request_group(vehicles_schedule, temp_request_dict, request_group, candidate_vehicle, candidate_node)

    return vehicles_schedule


def disturb_solution(vehicles_schedule, temp_request_dict=None, disturbance=disturbance_ratio):
    """
    Function which shakes a solution schedule. The intensity parameter
    indicates how many requests are lifted and moved elsewhere. The shaking process goes as follows:
    - 'intensity' amount of requests are removed from the schedule and put in a random
    """

    if not temp_request_dict:
        temp_request_dict = dict()

    request_groups_to_select = int(round(disturbance * count_assigned_request_groups(vehicles_schedule)))
    random_request_groups = select_random_request_groups(vehicles_schedule, request_groups_to_select)

    for request_group in random_request_groups:
        remove_request_group(vehicles_schedule, request_group)
        temp_request_dict = add_request_group_to_dict(request_group, temp_request_dict)

    while count_requests(temp_request_dict) != 0:
        request_group = pop_request_group(temp_request_dict, set_seed=False)
        candidate_vehicle, candidate_node, score = find_best_position_for_request_group(vehicles_schedule,
                                                                                        request_group)
        insert_request_group(vehicles_schedule, temp_request_dict, request_group, candidate_vehicle, candidate_node)

    return vehicles_schedule


def disturb_solution_2(vehicles_schedule, temp_request_dict=None, disturbance=disturbance_ratio):
    """
    Function which shakes a solution schedule. The intensity parameter
    indicates how many requests are lifted and moved elsewhere. The shaking process goes as follows:
    - 'intensity' amount of requests are removed from the schedule and put in a random
    """

    if not temp_request_dict:
        temp_request_dict = dict()

    request_groups_to_select = int(round(disturbance * count_assigned_request_groups(vehicles_schedule)))
    random_request_groups = select_random_request_groups(vehicles_schedule, request_groups_to_select)

    for request_group in random_request_groups:
        original_score = calc_request_group_waiting_time(vehicles_schedule, request_group) + \
                         calc_request_group_invehicle_time(vehicles_schedule, request_group)

        temp_schedule = copy.deepcopy(vehicles_schedule)

        remove_request_group(temp_schedule, request_group)
        temp_request_dict = add_request_group_to_dict(request_group, temp_request_dict)

        # candidate_vehicle, candidate_node, score = \
        #     find_first_best_improvement_for_request_group(vehicles_schedule, request_group, original_score)

        candidate_vehicle, candidate_node, score = find_best_position_for_request_group(temp_schedule,
                                                                                        request_group)
        insert_request_group(temp_schedule, temp_request_dict, request_group, candidate_vehicle, candidate_node)
        new_opportunity_cost = calc_request_group_opportunity_cost(temp_schedule, request_group)

        if new_opportunity_cost < original_score:
            vehicles_schedule = temp_schedule

    return vehicles_schedule