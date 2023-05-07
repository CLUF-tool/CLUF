import numpy as np
import pandas as pd


def InterRefRelation(save_path,CD,Size):

    DependMatrix = np.zeros((Size, Size), dtype=int)
    DependencyData = CD
    # print(DependencyData)
    # UDPath = cluster_path + '\\'+cluster_type
    for A, B, C in zip(DependencyData[0], DependencyData[1], DependencyData[2]):
        # print(A,B,C)
        if isinstance(A,str) or isinstance(B,str):
            # print(A,B)
            continue
        a = int(A) - 1
        b = int(B) - 1
        DependMatrix[a][b] += C

    DM = pd.DataFrame(DependMatrix)
    DM.to_csv(save_path,index=False,header=False)
    return DM

def report_cluster_dependency(file_deps_path, cluster_label_path, save_path):
    file_deps = pd.read_csv(file_deps_path)
    file_deps.columns = range(file_deps.shape[1])
    cluster_label = pd.read_csv(cluster_label_path, names=["Path", "clusterLabels"])
    cluster_quantity = cluster_label.clusterLabels.max() + 1
    for A, B in zip(cluster_label['Path'], cluster_label['clusterLabels']):
        file_deps.replace(A, B, inplace=True)
    file_deps.to_csv(save_path, header=False, index=False)
    return file_deps, cluster_quantity

def MQ_Metrics(DependMatrix, size):
    mq = 0
    RowSum = DependMatrix.sum(axis=1)
    ColumnSum = DependMatrix.sum(axis=0)
    for i in range(size):
        A = DependMatrix[i][i]
        B = RowSum[i] + ColumnSum[i] - 2 * A
        if A == 0:
            mq += 0
            continue
        else:
            MFi = (A / (A + 0.5 * B))
            # print(MFi)
            mq += MFi
    # print(mq)
    return mq