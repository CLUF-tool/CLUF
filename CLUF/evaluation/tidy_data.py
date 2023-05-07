import pandas as pd
from utils.GlobalVarUpdate import *

def get_project_list(data):
    project_large_list = []
    project_small_list = []
    count = 0
    for project in data['Project']:
        count += 1
        if count < 11:
            project_small_list.append(project)
        else:
            project_large_list.append(project)
    print(project_small_list)
    print(project_large_list)


def extract_gather_data(data, project_list, metric):
    project_large = data[data['Project'].isin(project_list)]
    print(project_large.shape[0])
    project_large = project_large.sort_values(by='Project', ascending=True)
    return project_large[metric].values


def get_df_mean(df):
    df_mean = ['Average']
    for col in df.columns:
        # print(col)
        if col == 'Project':
            continue
        df_mean.append(df[col].mean())
    df.loc[len(df)] = df_mean
    df = df.round(2)
    return df


if __name__ == '__main__':

    project_small_list = ['atlas', 'curator', 'flume', 'groovy', 'hudi', 'iotdb', 'kylin', 'pdfbox', 'storm', 'struts']
    project_large_list = ['beam', 'calcite', 'camel', 'gobblin', 'hbase', 'hive', 'logging-log4j2',
                          'nifi']

    cluster_type = {
        'acdc': 'ACDC',
        'arc': 'ARC',
        'cluffp': 'CLUFFP',
        'AHC_tfidf_tag': 'LSA-AHC',
        'KMeans_tfidf_tag': 'LSA-KMeans',
        'AHC_c2v_tfidf': 'C2V-AHC',
        'KMeans_c2v_tfidf': 'C2V-KMeans'
    }

    # bug=['fr','loc','bc','density_bf_file','density_bf_loc']
    # next_bug=['bfr_top','bfr_all']
    # authority=['MoJoFM','A2A']
    # DS=['JC_top','JC_all']

    file_list = {
        'bug': ['fr', 'loc', 'bc', 'density_bf_file', 'density_bf_loc'],
        'next_bug': ['bfr_top', 'bfr_all'],
        'authority': ['MoJoFM', 'A2A'],
        'DS': ['JC_top', 'JC_all']}

    csec_result_path = gl.data_result_path
    other_result_path = gl.root_path+r'\Compare_Cluster'

    for file, metric_list in file_list.items():
        for metric in metric_list:
            metric_df_small = pd.DataFrame()
            metric_df_small['Project'] = project_small_list
            metric_df_large = pd.DataFrame()
            metric_df_large['Project'] = project_large_list
            for cluster_physical, cluster_real in cluster_type.items():
                print(cluster_real)
                if cluster_physical in ['AHC_tfidf_tag', 'KMeans_tfidf_tag','AHC_c2v_tfidf','KMeans_c2v_tfidf']:
                    data_path_ = csec_result_path + '\\' + cluster_physical + '\\' + file + '_' + cluster_physical + '.csv'
                    data_ = pd.read_csv(data_path_)
                    metric_small = extract_gather_data(data_, project_small_list, metric)
                    if metric == 'density_bf_loc':
                        metric_small *= 1000
                    metric_df_small[cluster_real] = metric_small
                    metric_large = extract_gather_data(data_, project_large_list, metric)
                    if metric == 'density_bf_loc':
                        metric_large *= 1000
                    metric_df_large[cluster_real] = metric_large
                else:
                    data_path_ = other_result_path + '\\' + cluster_physical + '\\result\\' + file + '_' + cluster_physical + '.csv'
                    data_ = pd.read_csv(data_path_)
                    metric_small = extract_gather_data(data_, project_small_list, metric)
                    if metric == 'density_bf_loc':
                        metric_small *= 1000
                    try:
                        metric_df_small[cluster_real] = metric_small
                    except:
                        print(cluster_physical,metric)

                    if cluster_physical in ['acdc']:
                        metric_large = extract_gather_data(data_, project_large_list, metric)
                        if metric == 'density_bf_loc':
                            metric_large *= 1000
                        metric_df_large[cluster_real] = metric_large
            metric_df_small = get_df_mean(metric_df_small)
            metric_df_small.to_csv(csec_result_path + '\\small\\' + metric + '_small.csv', index=False)
            metric_df_large = get_df_mean(metric_df_large)
            metric_df_large.to_csv(csec_result_path + '\\large\\' + metric + '_large.csv', index=False)
