# Rough idea for an insertion heuristic >> add in a python script, not notebook
def insert_passenger(requests, vehicles, schedule_so_far):
    
    if len(requests) == 0:
        return schedule_so_far
    
    else:
        for r in requests:
            greedy_insert()
            requests.pop(r)
            
            insert_passenger(requests, vehicles, schedule_so_far)
    
    return None