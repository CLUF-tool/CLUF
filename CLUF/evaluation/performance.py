import pandas as pd

from utils.GetHighRiskCluster import buggy_cluster_in_next_version
from utils.GlobalVarUpdate import *

if __name__ == '__main__':
    v_type = ['c2v_tfidf']
    c_type = ['AHC']
    log_type = ['tag']

    project_type=''
    cluster_result_data_prefix = r'result_'+project_type
    top_cluster_prefix = r'bug_'+project_type
    result_data_prefix = r'next_bug_'+project_type

    for vectorize_type in v_type:
        for cluster_type in c_type:
            for log in log_type:

                cluster_arch = cluster_type + '_' + vectorize_type + '_' + log
                cluster_arch_specify = gl.data_result_path + '\\' + cluster_arch

                bug_result_path = cluster_arch_specify + '\\' + top_cluster_prefix + cluster_arch + '.csv'
                bug_result = pd.read_csv(bug_result_path)

                save_path = cluster_arch_specify + '\\' + result_data_prefix + cluster_arch + '_only.csv'
                input_data = pd.read_csv(
                    cluster_arch_specify + '\\' + cluster_result_data_prefix + cluster_arch + '.csv')
                for project, version, cluster_sum in zip(input_data['Project'], input_data['Version'], input_data['f_optimal']):

                    print(version, cluster_sum)
                    GlobalVarUpdate(project, version)

                    top_buggy_cluster = bug_result[bug_result['Project'] == project]['top_buggy_cluster'].values
                    top_buggy_cluster = eval(top_buggy_cluster[0])

                    middle_data_path = gl.version_middle_path
                    root_path = gl.version_cluster_path + '\\' + cluster_arch + '\\' + str(cluster_sum)

                    cluster_label_path = root_path + '\\' + "Label.csv"
                    next_log_prefix = gl.project_middle_path + "\\next"
                    current_log_path = next_log_prefix + '_bug_fix_' + log + '_only.json'

                    buggy_cluster_in_next_version(project, cluster_label_path,
                                                  current_log_path,
                                                  top_buggy_cluster, save_path)
