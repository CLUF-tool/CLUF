import pandas as pd
from cliffs_delta import cliffs_delta
from utils.GlobalVarUpdate import *

if __name__ == '__main__':

    file_list = {
        'bug': ['fr', 'loc', 'bc', 'density_bf_file', 'density_bf_loc'],
        'next_bug': ['bfr_top', 'bfr_all'],
        'authority': ['MoJoFM', 'A2A'],
        'DS': ['JC_top', 'JC_all']}

    csec_result_path = gl.data_result_path


    cluster_a = ['C2V-KMeans']

    # project_size='small'
    # cluster_b = ['ACDC', 'ARC', 'CLUFFP']

    project_size = 'large'
    cluster_b = ['ACDC']

    cliff_result = pd.DataFrame(index=cluster_b)

    # for size in project_size:
    for file, metric_list in file_list.items():
        for metric in metric_list:
            path = csec_result_path + '\\' + project_size + '\\' + metric + '_' + project_size + '.csv'
            metric_data = pd.read_csv(path)
            cliff = []
            for other in cluster_b:
                for sem_cc in cluster_a:
                    # d,res=cliffs_delta(file_small[other], file_small[sem_cc])
                    d, res = cliffs_delta(metric_data[sem_cc], metric_data[other])
                    cliff.append(str(round(d, 2)) + '(' + res[0] + ')')
                    # conclusion.append(res)
                    print(other, d, res)
            cliff_result[metric] = cliff
    print(cliff_result)
    cliff_result.to_csv(csec_result_path + '\\cliff_' + cluster_a[0] + '_'+cluster_b[0] + '_' + project_size + '.csv')
