import pandas as pd
from numpy import *
import utils.GlobalVar as gl
def divZero(x,y):
    if y:
        return x/y
    else:
        return 0

def RateResult(HCLabelPath):
    HC_cur=pd.read_csv(HCLabelPath+'\HCLabel.csv',names=['path','label'])
    CoChangeMatrix=pd.read_csv(gl.DataPath+"-coMatrix.csv",header=None)
    CCMatrix_index=pd.read_csv(gl.DataPath+'-filename.csv',names=['path'])

    CCMatrix_index['index']=CoChangeMatrix.index
    HC_merge=pd.merge(CCMatrix_index,HC_cur,on=['path'])


    HC_merge.sort_values(by=['label'],inplace=True)

    cluster_group=HC_merge.groupby('label')
    CCR_list=[]
    change_data=[]
    for cluster in cluster_group:
        in_cluster_change=0
        all_cluster_change=0
        for index_x in cluster[1]['index']:
            for index_y in cluster[1]['index']:
                if(index_x!=index_y):
                    in_cluster_change+=CoChangeMatrix[index_x][index_y]
            all_cluster_change+=CoChangeMatrix[index_x].sum()

        PartA_CC=divZero(in_cluster_change/2,cluster[1].shape[0])
        PartB_CC=divZero(all_cluster_change-in_cluster_change,CCMatrix_index.shape[0]-cluster[1].shape[0])
        CCR_cluster=divZero(PartA_CC,PartB_CC)

        CCR_list.append(CCR_cluster)
        change_data.append([in_cluster_change/2,all_cluster_change-in_cluster_change,PartA_CC,PartB_CC,CCR_cluster])



    HC_merge.to_csv(HCLabelPath+'\HCLabel_merge.csv')
    CD=pd.DataFrame(change_data)
    CD.to_csv(HCLabelPath+'\ChangeRateData.csv',header=['in_cluster_change','out_cluster_change','in_cluster_rate','out_cluster_rate','in/out_rate'],index=False)
    return mean(CCR_list)
