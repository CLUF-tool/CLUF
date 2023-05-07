import os
import numpy as np
import pandas as pd

def MergeCSVFile(cluster_nums, save_path, smell_type):
    all_filenames = []
    for i in range(0, cluster_nums):
        path = save_path + '\\' + str(i) + '\\' + smell_type + '.csv'
        all_filenames.append(path)
    cols = np.arange(5)
    combined_csv = pd.concat([pd.read_csv(os.path.abspath(f), usecols=cols) for f in all_filenames])
    combined_csv.to_csv(save_path + '\\combined.csv', index=False)

def ds_jc(cluster_list, save_path, smell_type):
    cols = np.arange(5)

    combined_csv = pd.read_csv(save_path + '\\combined.csv')
    combined_csv.drop_duplicates(inplace=True, subset=['Cause of the Smell', 'Type Name', 'Package Name', 'Design Smell'])

    combined_list = combined_csv[combined_csv['Project Name'].isin(cluster_list)]
    # print(combined_top)

    cluster = pd.read_csv(save_path + '\\cluster\\' + smell_type + '.csv', usecols=cols)
    cluster.drop_duplicates(inplace=True, subset=['Cause of the Smell', 'Type Name', 'Package Name', 'Design Smell'])

    union_ds = pd.merge(cluster, combined_list, how='outer', on=['Cause of the Smell', 'Type Name', 'Package Name', 'Design Smell'])
    # union_ds.to_csv(save_path + '\\union_ds_top.csv', index=False)

    intersection_ds = pd.merge(cluster, combined_list, how='inner', on=['Cause of the Smell', 'Type Name', 'Package Name', 'Design Smell'])
    # intersection_ds.to_csv(save_path + '\\intersection_ds_top.csv')

    ds_in_cluster = cluster.shape[0]
    ds_in_list = combined_list.shape[0]
    ds_intersection = intersection_ds.shape[0]
    ds_union = union_ds.shape[0]
    jc_top = ds_intersection / ds_union

    return jc_top
