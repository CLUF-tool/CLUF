import pandas as pd

from utils.EntropyRelated import standardize, cal_weight
from utils.GetHighRiskCluster import LOCPerFile, generate_buggy_space, get_bug_decision_matrix, bug_liner_weighted, \
    buggy_cluster_order_by_file_in_bug_space, get_top_cluster
from utils.GlobalVarUpdate import *

if __name__ == '__main__':

    v_type = ['c2v_tfidf']
    c_type = ['AHC']
    log_type = ['tag']

    cluster_result_data_prefix = r'result_'
    result_data_prefix = r'bug_'

    for vectorize_type in v_type:
        for cluster_type in c_type:
            for log in log_type:

                cluster_arch = cluster_type + '_' + vectorize_type + '_' + log
                cluster_arch_specify = gl.data_result_path + '\\' + cluster_arch
                if not os.path.exists(cluster_arch_specify):
                    os.makedirs(cluster_arch_specify)
                input_data = pd.read_csv(
                    cluster_arch_specify + '\\' + cluster_result_data_prefix + cluster_arch + '.csv')
                save_path = cluster_arch_specify + '\\' + result_data_prefix + cluster_arch + '.csv'
                count = 0
                for project, version, cluster_nums in zip(input_data['Project'], input_data['Version'], input_data['f_optimal']):

                    GlobalVarUpdate(project, version)
                    print(version, cluster_nums)

                    root_path = gl.version_cluster_path + '\\' + cluster_arch + '\\' + str(cluster_nums)
                    cluster_label_path = root_path + '\\' + "Label.csv"

                    middle_data_path = gl.version_middle_path
                    loc_path = middle_data_path + '_LOC.csv'
                    current_log_path = middle_data_path + '_bug_fix_' + log + '.json'

                    loc_label_path = middle_data_path + '_LableLOC.csv'
                    LOCPerFile(loc_path, cluster_label_path, loc_label_path)

                    bug_space_path = middle_data_path + '_bug_space.csv'
                    generate_buggy_space(cluster_label_path, current_log_path, bug_space_path)

                    cluster_data_path = root_path + '\\cluster_data_double.csv'
                    decision_matrix_path = root_path + '\\decision_matrix_bug.csv'
                    weight_path = root_path + '\\weight_bug.csv'
                    decision_matrix = get_bug_decision_matrix(cluster_label_path, bug_space_path, cluster_data_path)

                    # 标准化
                    decision_matrix_std = pd.DataFrame()
                    decision_matrix_std['label'] = decision_matrix['label']
                    decision_matrix_std['bug_weight'] = standardize('pos', 0.002, 0.996,
                                                                    decision_matrix['bug_weight'].values)
                    decision_matrix_std['bug_density_file'] = standardize('pos', 0.002, 0.996,
                                                                          decision_matrix['bug_density_file'].values)
                    decision_matrix_std['bug_density_loc'] = standardize('pos', 0.002, 0.996,
                                                                         decision_matrix['bug_density_loc'].values)

                    weight = cal_weight(decision_matrix_std[['bug_weight', 'bug_density_file', 'bug_density_loc']])
                    ranged_cluster = bug_liner_weighted(decision_matrix_std, weight, decision_matrix_path, weight_path)
                    top_buggy_cluster, bug_space_file_sum, buggy_file_threshold, current_accumulate_file = get_top_cluster(
                        cluster_label_path, bug_space_path, ranged_cluster)

                    print(top_buggy_cluster)

                    buggy_cluster_order_by_file_in_bug_space(project, bug_space_file_sum, cluster_label_path,
                                                             current_log_path,
                                                             loc_label_path, save_path, top_buggy_cluster,
                                                             buggy_file_threshold, current_accumulate_file,
                                                             decision_matrix)
