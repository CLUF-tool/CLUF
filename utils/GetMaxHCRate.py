import os
import pandas as pd
import utils.GlobalVar as gl
from sklearn.cluster import AgglomerativeClustering
from utils.ChangeAVGRate import RateResult


def Sklearn_AHC(data,n_clusters,DataPath):
    SubPath=DataPath+"\\euc_dist\\"+str(n_clusters)
    FilePath = DataPath + "-filename.csv"

    if not os.path.exists(SubPath):
        os.makedirs(SubPath)

    AFC_result=AgglomerativeClustering(n_clusters,affinity='precomputed',linkage='average').fit(data)
    HC_labels=AFC_result.labels_
    fn=pd.read_csv(FilePath,header=None)
    fn.insert(1,"clusterLabels",HC_labels)
    fn.sort_values(by=["clusterLabels"],inplace=True)
    fn.to_csv(SubPath+"\\"+"HCLabel.csv",index=0,header=0)


def Sklearn_AHC_Max(dist,FileSum):

    midMax = 0
    midMaxIndex = 0
    for i in range(2,FileSum):
        if os.path.exists(gl.DataPath + "\\euc_dist\\" + str(i)+'\ChangeRateData.csv'):
            RM = pd.read_csv(gl.DataPath + "\\euc_dist\\" + str(i)+'\ChangeRateData.csv')
            RateMean = RM['in/out_rate'].mean()
        else:
            Sklearn_AHC(dist, i, gl.DataPath)
            RateMean = RateResult(gl.DataPath + "\\euc_dist\\" + str(i))

        if RateMean > midMax:
            midMax = RateMean
            midMaxIndex = i
        elif midMaxIndex > i and RateMean == midMax:
            midMaxIndex = i

    return midMax,midMaxIndex
