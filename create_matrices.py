from network_generation import generate_cost_matrix, import_network
from settings import v_mean
from pandas import DataFrame

path = 'Cost matrices/'

networks = ['small', 'medium', 'large']
variants = ['half', 'more']

for net in networks:
    for var in variants:

        network = import_network(net, var)
        cost_matrix = generate_cost_matrix(network, v_mean=v_mean)

        temp_x, temp_y = map(max, zip(*cost_matrix))
        res = [[cost_matrix.get((j, i), 0) for i in range(1, temp_y + 1)]
                                          for j in range(1, temp_x + 1)]

        df = DataFrame(res)
        output_path = path + net + '_' + var + '.csv'
        DataFrame.to_csv(df, output_path)
