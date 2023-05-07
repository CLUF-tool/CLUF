import pandas as pd

from utils.GetCluster import cluster_drive
from utils.GlobalVarUpdate import *

if __name__ == '__main__':

    v_type = ['c2v_tfidf']
    c_type = ['AHC', 'KMeans']
    log_type = ['tag']
    input_data = pd.read_csv(gl.root_path + r'\input\input_project.csv')

    for vectorize_type in v_type:
        for cluster_type in c_type:
            print(vectorize_type, cluster_type)
            for log in log_type:
                for project, version in zip(input_data['project'], input_data['exp_version']):
                    GlobalVarUpdate(project, version)
                    start_index = 2
                    cluster_drive(start_index, project, version, vectorize_type, cluster_type, log)
