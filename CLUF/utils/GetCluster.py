import os
import time
from collections import Counter
import warnings
import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
import utils.GlobalVar as gl
from utils.EntropyRelated import standardize, cal_weight
from utils.SaveResult import save_result

warnings.filterwarnings('error')


def divZero(x, y):
    if y:
        return x / y
    else:
        return x


def ClusterEsembled(cluster_type, n_cluster, dendrogram_matrix, index, label_path):
    if cluster_type is 'KMeans':
        try:
            cluster = KMeans(n_cluster, random_state=100).fit(dendrogram_matrix)
        except Warning:
            return 50
    elif cluster_type == 'KMeans_5':
        try:
            cluster = KMeans(n_cluster, random_state=100, n_init=5).fit(dendrogram_matrix)
        except Warning:
            return 50
    elif cluster_type == 'AHC':
        cluster = AgglomerativeClustering(n_cluster, affinity='precomputed', linkage='average').fit(dendrogram_matrix)
    cluster_labels = {'index': index, 'labels': cluster.labels_}
    cluster_labels = pd.DataFrame(cluster_labels)
    cluster_labels.to_csv(label_path + "\\" + "Label.csv", index=False, header=False)

    return 60


def cluster_entrance(start_index, iteration, dendrogram_matrix, cluster_type, index, label_path_):
    for n_cluster in range(start_index, iteration + 1):
        label_path = label_path_ + '\\' + str(n_cluster)
        if not os.path.exists(label_path):
            os.makedirs(label_path)
        clustercode = ClusterEsembled(cluster_type, n_cluster, dendrogram_matrix, index, label_path)
        if clustercode == 50:
            return n_cluster - 1
    return iteration


def get_cluster_data(cut_off_matrix, label_path, loc_path):
    if os.path.exists(label_path + r'\cluster_data_double.csv'):
        # print('Double existed: ',label_path)
        cluster_data = pd.read_csv(label_path + r'\cluster_data_double.csv')
    elif os.path.exists(label_path + r'\cluster_data.csv'):
        # print('Data existed: ', label_path)
        cluster_data = pd.read_csv(label_path + r'\cluster_data.csv')
        # print(cluster_data['out_change_file_r'])
        cluster_data['in_change_file_r'] = cluster_data['in_change'] / (
                cluster_data['in_file'] * cluster_data['in_file'])
        cluster_data['out_change_file_r'] = cluster_data['out_change'] / (
                cluster_data['in_file'] * cluster_data['out_file'])
        cluster_data['in_change_loc_r'] = cluster_data['in_change'] / (cluster_data['in_loc'] * cluster_data['in_loc'])
        cluster_data['out_change_loc_r'] = cluster_data['out_change'] / (
                cluster_data['in_loc'] * cluster_data['out_loc'])
        # print(cluster_data['out_change_file_r'])
        cluster_data.to_csv(label_path + r'\cluster_data_double.csv')
    else:
        # print('Not Data existed: ', label_path)
        cluster_labels = pd.read_csv(label_path + r'\Label.csv', names=['path', 'label'])
        file_loc = pd.read_csv(loc_path)

        all_file = file_loc.shape[0]
        all_loc = file_loc['CountLineCode'].sum()

        cluster_loc = pd.merge(cluster_labels, file_loc, left_on='path', right_on='Name')
        cluster_loc = cluster_loc[['path', 'label', 'CountLineCode']]
        cluster_group = cluster_loc.groupby('label')

        change_data = []

        for cluster in cluster_group:
            in_cluster_change = 0
            all_cluster_change = 0

            for index_x in cluster[1].index:
                for index_y in cluster[1].index:
                    if index_x != index_y:
                        in_cluster_change += cut_off_matrix[index_x][index_y]
                all_cluster_change += cut_off_matrix[index_x].sum()

            cluster_label = cluster[0]

            out_cluster_change = all_cluster_change - in_cluster_change
            in_cluster_change = in_cluster_change / 2

            in_cluster_file = cluster[1].shape[0]
            out_cluster_file = all_file - in_cluster_file

            in_cluster_loc = cluster[1]['CountLineCode'].sum()
            out_cluster_loc = all_loc - in_cluster_loc

            in_change_file_rate = in_cluster_change / (in_cluster_file * in_cluster_file)
            in_change_loc_rate = divZero(in_cluster_change, (in_cluster_loc * in_cluster_loc))

            out_change_file_rate = out_cluster_change / (in_cluster_file * out_cluster_file)
            out_change_loc_rate = divZero(out_cluster_change, (in_cluster_loc * out_cluster_loc))

            change_data.append([
                cluster_label,
                in_cluster_change, out_cluster_change,
                in_cluster_file, out_cluster_file,
                in_cluster_loc, out_cluster_loc,
                in_change_file_rate, out_change_file_rate,
                in_change_loc_rate, out_change_loc_rate
            ])

        cluster_data = pd.DataFrame(change_data)
        cluster_data.columns = [
            'label',
            'in_change', 'out_change',
            'in_file', 'out_file',
            'in_loc', 'out_loc',
            'in_change_file_r', 'out_change_file_r',
            'in_change_loc_r', 'out_change_loc_r'
        ]
        cluster_data.to_csv(label_path + r'\cluster_data_double.csv', index=False)

    return cluster_data['in_change_file_r'].mean(), cluster_data['out_change_file_r'].mean(), cluster_data[
        'in_change_loc_r'].mean(), cluster_data['out_change_loc_r'].mean()


def get_ned(label_path):
    cluster_labels = pd.read_csv(label_path + r'\Label.csv', names=['path', 'label'])
    cluster_label_data = cluster_labels['label'].values
    cluster_label_amount = Counter(cluster_label_data)
    non_extreme_distribution = 0
    for k, v in cluster_label_amount.items():
        if 5 <= v <= 20:
            non_extreme_distribution += v
    ned = non_extreme_distribution / cluster_labels.shape[0]
    return ned


def liner_weighted(decision_matrix, weight, decision_matrix_path, weight_path):
    decision_matrix.iloc[:, [2, 4]] = -decision_matrix.iloc[:, [2, 4]]
    select_cols = decision_matrix.columns[1:]
    decision_matrix['linear_weighted_sum'] = np.dot(decision_matrix[select_cols], weight['weight'])

    decision_matrix.to_csv(decision_matrix_path, index=False)
    weight.to_csv(weight_path)

    f_optimal = decision_matrix[decision_matrix['linear_weighted_sum'] == decision_matrix['linear_weighted_sum'].max()]
    f_optimal = f_optimal['label'].values

    return f_optimal[0]


def cluster_drive(start_index, project, version, vectorize_type, cluster_type, comatrix_type):
    start = time.time()

    FilenameData = pd.read_csv(gl.version_middle_path + '-filename.csv', names=['path'])

    cc_matrix = pd.read_csv(gl.version_middle_path + '_coMatrix_' + comatrix_type + '.csv', header=None)
    file_sum = FilenameData.shape[0]

    sem_sim_matrix = pd.read_csv(gl.version_middle_path + '-seMatrix-' + vectorize_type + '.csv', header=None)
    sem_sim_matrix = 1 - sem_sim_matrix
    label_path = gl.version_cluster_path + '\\' + cluster_type + '_' + vectorize_type + '_' + comatrix_type

    # SEM_CC
    iteration = cluster_entrance(start_index, file_sum, sem_sim_matrix, cluster_type, FilenameData['path'], label_path)
    cluster_arch = cluster_type + '_' + vectorize_type + '_' + comatrix_type
    cluster_arch_specify = gl.data_result_path + '\\' + cluster_arch
    if not os.path.exists(cluster_arch_specify):
        os.makedirs(cluster_arch_specify)
    cluster_result_path = cluster_arch_specify + '\\result_' + cluster_arch + '.csv'

    # iteration=1707
    decision_matrix = []
    for label in range(2, iteration + 1):
        loc_path = gl.version_middle_path + '_LOC.csv'
        icfr, ocfr, iclr, oclr = get_cluster_data(cc_matrix, label_path + '\\' + str(label), loc_path)

        ned = get_ned(label_path + '\\' + str(label))
        if icfr != 0 and iclr != 0 and ocfr != 0 and oclr != 0 and ned != 0:
            decision_matrix.append([label, icfr, ocfr, iclr, oclr, icfr / ocfr, iclr / oclr, ned])
    decision_matrix = pd.DataFrame(decision_matrix)
    decision_matrix.columns = [
        'label',
        'in_change_file_r', 'out_change_file_r',
        'in_change_loc_r', 'out_change_loc_r',
        'change_file_rate', 'change_loc_rate',
        'NED'
    ]


    decision_matrix_std = pd.DataFrame()
    decision_matrix_std['label'] = decision_matrix['label']
    decision_matrix_std['in_change_file_r'] = standardize('pos', 0.002, 0.996,
                                                          decision_matrix['in_change_file_r'].values)
    decision_matrix_std['out_change_file_r'] = standardize('neg', 0.002, 0.996,
                                                           decision_matrix['out_change_file_r'].values)
    decision_matrix_std['in_change_loc_r'] = standardize('pos', 0.002, 0.996,
                                                         decision_matrix['in_change_loc_r'].values)
    decision_matrix_std['out_change_loc_r'] = standardize('neg', 0.002, 0.996,
                                                          decision_matrix['out_change_loc_r'].values)

    decision_matrix_std['NED'] = standardize('pos', 0.002, 0.996,
                                             decision_matrix['NED'].values)
    weight = cal_weight(decision_matrix_std[
                            ['in_change_file_r', 'out_change_file_r', 'in_change_loc_r', 'out_change_loc_r',
                             'NED']])

    decision_matrix_path = label_path + '\\decision_matrix_ned_std.csv'
    weight_path = label_path + '\\weight_ned_std.csv'
    f_optimal = liner_weighted(decision_matrix_std, weight, decision_matrix_path, weight_path)

    end = time.time()
    cluster_data = [project, version, file_sum, iteration, f_optimal, end - start]
    print(cluster_data)
    cluster_header = ['Project', 'Version', 'file_sum', 'iteration', 'f_optimal', 'run_time']
    save_result(cluster_result_path, cluster_data, cluster_header)
