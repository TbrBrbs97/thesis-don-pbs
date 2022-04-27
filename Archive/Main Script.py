#!/usr/bin/env python
# coding: utf-8

# Main script elements:
# 
# STATIC VERSION
# - Given a fixed DoD
# - Main function
# - Auxillary functions:
#     - (greedy) insertion heuristic: in stead of looking for all possible insertions, look for a better insertion until you find no better one
#         - initial solution creator > spatio-temporal clustering of requests?
#         - feasibility check
#         - incremental waiting time + travel time calculator
#     - improvement heuristic
#         - neighborhood creators (destroy&repair, swappers, L-opt moves, ...)
#         - evaluate objective functions

# In[6]:


import pickle

from Archive import old_solution_generation

# In[7]:


# parameters

available_vehicles = 5
vehicle_capacity = 20
dod = 0 # static version = 0, dynamic version > 0
WT_penalty = 0 
TT_penalty = 0 


# In[8]:


# NOTE: this is only 1 scenario and 1 direction!!
file = open("Data/requests.pkl", "rb")
Requests = pickle.load(file)

file_2 = open("Data/small_od_matrix.pkl", "rb")
od_matrix = pickle.load(file_2)

vehicles = {}
schedule_so_far = {}


# In[9]:


od_pairs = set([i[0] for i in Requests])
od_pairs


# In[10]:


# Class: requests
# methods: select on destination, cluster/group on pickup time, assign issue time, ...

Requests
len(Requests)


# In[11]:


# make this later a method of the class 'requests / request list'



# In[12]:


# create equalsize clusters per od-pair = grouping together or request in time




# In[38]:


# create clusters per dep_t threshold, i.e. group requests from the first departure time until x minutes further.


        


# In[40]:


Requests_grouped = group_requests_dt(Requests, 5)
Requests_grouped


# In[9]:


# how many groups of at most 20 requests are there?
for k in Requests_grouped:
   print(k, len(Requests_grouped[k]))


# In[10]:


od_matrix


# Insertion strategy: momentarily focussed on the capacity constraint (i.e. trying to fill vehicles), not so much on the time constraint
# 
# 1. Divide requests into chunks: 
#  * (a) of at most equal size (e.g. 10) 
#  * (b) of optimal size (according to jenk's borders)
# 2. Select a first chunk of travellers, who want to travel from the origin to the farthest point, and fill a bus with them (almost) 
#     * If this bus is ride is full, then this schedule is complete.
#     * If there is room left, then add passengers in between at each visited stop.
# 

# In[11]:


tocity_keys = [(1,2),(2,3),(1,3)]
toterminal_keys = [(3,4),(3,5),(4,5)]

filterByKey = lambda keys: {x: Requests_grouped[x] for x in keys}
tocity_requests = filterByKey(tocity_keys)
toterminal_requests = filterByKey(toterminal_keys)

tocity_requests


# In[12]:


s = old_solution_generation.create_initial_solution(tocity_requests, 1, 3, 1, 20)


# In[14]:


s


# In[13]:


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

