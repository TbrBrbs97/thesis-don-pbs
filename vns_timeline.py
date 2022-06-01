import os
import matplotlib.pyplot as plt
from pandas import read_pickle


directory = 'Results/SE_0'

for filename in os.listdir(directory):
    file = os.path.join(directory, filename)
    vns_evolution = read_pickle(file)

print(vns_evolution)
plt.plot(vns_evolution)
plt.xlabel("Iterations")
plt.ylabel("Total travel time (min.)")
plt.show()
