import solution_evaluation as se
import solution_generation as sg
import vehicle_generation as vg
import requests_generation as rg

# TODO: Do we do the check for available capacity in the outer or inner function?
# If we do it in the outer functions, we can control which portion is 'sent' in as request group better
# so, then within this next function, we assume that the insertion is feasible!

def static_opt(solution):
    return None


