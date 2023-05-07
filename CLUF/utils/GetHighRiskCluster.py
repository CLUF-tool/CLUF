from collections import Counter

import numpy as np
import pandas as pd

from utils.SaveResult import save_result


def LOCPerFile(loc_path, cluster_path, loc_label_path):
    FileCluster = pd.read_csv(cluster_path, names=["Path", "clusterLabels"])

    FileLOC = pd.read_csv(loc_path)

    LableLOC = pd.merge(FileCluster, FileLOC, left_on='Path', right_on='Name')
    LableLOC = LableLOC[['Path', 'clusterLabels', 'CountLineCode']]
    LableLOC.to_csv(loc_label_path, index=False)



def generate_buggy_space(label_path, log_path, save_path):
    bug_fix_commit = pd.read_json(log_path)
    cluster_label = pd.read_csv(label_path, names=["path", "label"])
    file_bugs = [0] * cluster_label.shape[0]

    for commit, mod_file_list in zip(bug_fix_commit.commit, bug_fix_commit.paths):
        mod_file_list = pd.DataFrame(mod_file_list)
        if not mod_file_list.empty:
            mod_java_list = mod_file_list[mod_file_list['path'].str.contains(r'.java', na=True)]
            if not mod_java_list.empty:
                same_cluster = set()
                for insertions, deletions, mod_java in zip(mod_java_list.insertions, mod_java_list.deletions,
                                                           mod_java_list.path):
                    try:
                        exist_label = cluster_label[cluster_label['path'].str.contains(mod_java, regex=False)]
                    except KeyError:
                        print(commit)
                    if not exist_label.empty:
                        cur_index = exist_label.index[0]
                        file_bugs[cur_index] += 1
    bug_space = cluster_label.copy(deep=True)
    bug_space['bugs'] = file_bugs
    bug_space = bug_space[bug_space['bugs'] >= 2]
    bug_space.reset_index(inplace=True)
    bug_space_file_sum = bug_space.shape[0]
    bug_space.to_csv(save_path, index=False)

    return bug_space_file_sum


def get_bug_decision_matrix(cluster_label_path, bug_space_path, cluster_data_path):
    cluster_labels = pd.read_csv(cluster_label_path, names=['path', 'label'])
    cluster_data = pd.read_csv(cluster_data_path)
    bug_space = pd.read_csv(bug_space_path)

    cluster_sum = cluster_labels['label'].max() + 1
    cluster_bugs = bug_space.groupby(by=['label'])['bugs'].sum().reset_index()
    all_bugs = bug_space['bugs'].sum()

    cluster_index = []
    bug_weight = []
    bug_density_file = []
    bug_density_loc = []
    for label, bugs in zip(cluster_bugs['label'], cluster_bugs['bugs']):
        [in_cluster_file] = cluster_data[cluster_data['label'] == label]['in_file'].values
        [in_cluster_loc] = cluster_data[cluster_data['label'] == label]['in_loc'].values
        cluster_index.append(label)
        bug_weight.append(bugs / all_bugs)
        bug_density_file.append(bugs / in_cluster_file)
        bug_density_loc.append(bugs / in_cluster_loc)
    decision_matrix = pd.DataFrame()
    decision_matrix['label'] = cluster_index
    decision_matrix['bug_weight'] = bug_weight
    decision_matrix['bug_density_file'] = bug_density_file
    decision_matrix['bug_density_loc'] = bug_density_loc
    return decision_matrix


def bug_liner_weighted(decision_matrix, weight, decision_matrix_path, weight_path):

    select_cols = decision_matrix.columns[1:]
    decision_matrix['linear_weighted_sum'] = np.dot(decision_matrix[select_cols],weight['weight'])

    decision_matrix = decision_matrix.sort_values(by='linear_weighted_sum', ascending=False)
    decision_matrix.to_csv(decision_matrix_path, index=False)
    weight.to_csv(weight_path)

    return decision_matrix['label'].values


def get_top_cluster(cluster_label_path,bug_space_path, ranged_cluster):
    cluster_label=pd.read_csv(cluster_label_path,names=['path','label'])
    bug_space = pd.read_csv(bug_space_path)
    bug_space_file_sum = bug_space.shape[0]
    buggy_file_threshold = round(bug_space.shape[0] * 0.8)
    buggy_file_per_cluster = dict(Counter(bug_space["label"]))
    top_buggy_cluster = []
    current_accumulate_file = 0
    for label in ranged_cluster:

        current_accumulate_file += buggy_file_per_cluster[label]

        top_buggy_cluster.append(label)
        if current_accumulate_file >= buggy_file_threshold:
            break
    return top_buggy_cluster, bug_space_file_sum, buggy_file_threshold, current_accumulate_file


def buggy_cluster_order_by_file_in_bug_space(project, bug_space_file_sum, label_path, log_path, loc_label_path,
                                             save_path, top_buggy_cluster, buggy_file_threshold,
                                             current_accumulate_file,decision_matrix):
    bug_fix_commit = pd.read_json(log_path)
    cluster_label = pd.read_csv(label_path, names=["path", "label"])
    file_label_loc = pd.read_csv(loc_label_path)

    file_sum = cluster_label.shape[0]
    cluster_sum = cluster_label['label'].max() + 1
    total_loc = sum(file_label_loc['CountLineCode'])
    bc_per_cluster = [0] * cluster_sum
    loc_per_cluster = {}
    bug_in_cluster = 0
    bug_cross_cluster = 0
    file_per_cluster = dict(Counter(cluster_label["label"]))
    bf_per_cluster = [0] * cluster_sum

    for key, val in zip(file_label_loc['clusterLabels'], file_label_loc['CountLineCode']):
        loc_per_cluster[key] = loc_per_cluster.get(key, 0) + val

    for commit, mod_file_list in zip(bug_fix_commit.commit, bug_fix_commit.paths):
        mod_file_list = pd.DataFrame(mod_file_list)
        if not mod_file_list.empty:
            mod_java_list = mod_file_list[mod_file_list['path'].str.contains(r'.java', na=True)]
            if not mod_java_list.empty:
                same_cluster = set()
                for insertions, deletions, mod_java in zip(mod_java_list.insertions, mod_java_list.deletions,
                                                           mod_java_list.path):
                    try:
                        exist_label = cluster_label[cluster_label['path'].str.contains(mod_java, regex=False)]
                    except KeyError:
                        print(commit)
                    if not exist_label.empty:
                        modified = int(insertions) + int(deletions)
                        c_label = int(exist_label['label'].values)
                        bc_per_cluster[c_label] += modified
                        same_cluster.add(c_label)
                if len(same_cluster) == 1:
                    bug_in_cluster += 1
                    list_status = list(same_cluster)
                    bf_per_cluster[list_status[0]] += 1
                elif len(same_cluster) >= 2:
                    bug_cross_cluster += 1

    bug_fix_all = bug_in_cluster + bug_cross_cluster
    total_bc = sum(bc_per_cluster)
    bf_in_top_cluster = 0
    loc_in_top_cluster = 0
    file_in_top_cluster = 0
    bc_in_top_cluster = 0

    bug_density_file = 0
    bug_density_loc = 0

    for cluster in top_buggy_cluster:
        bf_in_top_cluster += bf_per_cluster[cluster]
        loc_in_top_cluster += loc_per_cluster[cluster]
        file_in_top_cluster += file_per_cluster[cluster]
        bc_in_top_cluster += bc_per_cluster[cluster]

        cluster_bug_data = decision_matrix[decision_matrix['label'] == cluster]
        cluster_bug_density_file = cluster_bug_data['bug_density_file'].values
        bug_density_file += cluster_bug_density_file[0]
        cluster_bug_density_loc = cluster_bug_data['bug_density_loc'].values
        bug_density_loc += cluster_bug_density_loc[0]


    bug_density_file = bug_density_file / len(top_buggy_cluster)
    bug_density_loc = bug_density_loc / len(top_buggy_cluster)

    bfr = bf_in_top_cluster / bug_fix_all
    density_bf_file = bf_in_top_cluster / file_in_top_cluster
    density_bf_loc = bf_in_top_cluster / loc_in_top_cluster
    bfin_bfr = bf_in_top_cluster / bug_in_cluster
    loc = loc_in_top_cluster / total_loc
    fr = file_in_top_cluster / file_sum
    bc = bc_in_top_cluster / total_bc


    bug_result = [project, cluster_sum, bug_space_file_sum, file_sum, bug_space_file_sum / file_sum, bug_in_cluster,
                  bug_cross_cluster,fr, loc,  bc, bfr,bug_density_file,bug_density_loc, density_bf_file, density_bf_loc, bfin_bfr, buggy_file_threshold,
                  current_accumulate_file, file_in_top_cluster,
                  top_buggy_cluster]
    bug_header = ['Project', 'cluster_sum', 'File_bs', 'file_sum', 'File_bs%', 'BFin', 'BFout', 'fr', 'loc', 'bc', 'bfr','bug_density_file_average','bug_density_loc_average','density_bf_file', 'density_bf_loc',
                   'bfin_bfr', 'buggy_file_threshold', 'current_accumulate_file', 'file_in_top_cluster',
                  'top_buggy_cluster']
    print(bug_result)
    save_result(save_path, bug_result, bug_header)


def buggy_cluster_in_next_version(project, label_path, log_path, top_buggy_cluster,
                                  save_path):
    bug_fix_commit = pd.read_json(log_path)
    cluster_label = pd.read_csv(label_path, names=["path", "label"])

    file_sum = cluster_label.shape[0]
    cluster_sum = cluster_label['label'].max() + 1
    bc_in_cluster = [0] * cluster_sum
    bug_in_cluster = 0
    bug_cross_cluster = 0
    bf_per_cluster = [0] * cluster_sum
    total_bc = 0

    for commit, mod_file_list in zip(bug_fix_commit.commit, bug_fix_commit.paths):
        mod_file_list = pd.DataFrame(mod_file_list)
        if not mod_file_list.empty:
            mod_java_list = mod_file_list[mod_file_list['path'].str.contains(r'.java', na=True)]
            if not mod_java_list.empty:
                same_cluster = set()
                bc_accumulate = 0
                for insertions, deletions, mod_java in zip(mod_java_list.insertions, mod_java_list.deletions,
                                                           mod_java_list.path):
                    try:
                        exist_label = cluster_label[cluster_label['path'].str.contains(mod_java, regex=False)]
                    except KeyError:
                        print(commit)
                    if not exist_label.empty:
                        modified = int(insertions) + int(deletions)
                        c_label = int(exist_label['label'].values)
                        bc_accumulate += modified
                        same_cluster.add(c_label)
                if len(same_cluster) == 1:
                    bug_in_cluster += 1
                    list_status = list(same_cluster)
                    bf_per_cluster[list_status[0]] += 1
                    bc_in_cluster[list_status[0]] += bc_accumulate
                elif len(same_cluster) >= 2:
                    bug_cross_cluster += 1
                total_bc += bc_accumulate

    bug_fix_all = bug_in_cluster + bug_cross_cluster
    bf_in_top_cluster = 0
    bc_in_top_cluster = 0

    for cluster in top_buggy_cluster:
        bf_in_top_cluster += bf_per_cluster[cluster]
        bc_in_top_cluster += bc_in_cluster[cluster]

    bfr_all = bug_in_cluster / bug_fix_all
    bfr_top = bf_in_top_cluster / bug_fix_all
    bftop_in_bfin = bf_in_top_cluster / bug_in_cluster
    bc_top = bc_in_top_cluster / total_bc
    bc_all = sum(bc_in_cluster) / total_bc


    bug_result = [project, cluster_sum, file_sum, bug_in_cluster,
                  bug_cross_cluster, bc_top, bc_all, bfr_top, bfr_all, bftop_in_bfin]
    bug_header = ['Project', 'cluster_sum', 'file_sum', 'BFin', 'BFout', 'bc_top', 'bc_all', 'bfr_top', 'bfr_all',
                  'bftop_in_bfin']
    print(bug_result)
    save_result(save_path, bug_result, bug_header)
