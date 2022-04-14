import os
import pandas as pd
import numpy as np
import utils.GlobalVar as gl
from utils.DesigniteCMD import WholeDJ
from utils.GlobalVarUpdate import GlobalVarUpdate

def JC(save_path,smell_type):
    cols = np.arange(5)
    combined_csv = pd.read_csv(save_path + '\\combined.csv')
    combined_csv.drop_duplicates(inplace=True, subset=['Cause of the Smell', 'Type Name', 'Package Name', 'Design Smell'])
    cluster = pd.read_csv(save_path + '\\cluster\\' + smell_type + '.csv', usecols=cols)

    cluster.drop_duplicates(inplace=True, subset=['Cause of the Smell', 'Type Name', 'Package Name', 'Design Smell'])

    union_DS = pd.merge(cluster, combined_csv, on=['Cause of the Smell', 'Type Name', 'Package Name', 'Design Smell'],
                         how='outer')
    union_DS.to_csv(save_path + '\\union_DS.csv', index=False)
    intersection_DS=pd.read_csv(save_path+'\\merge-cause-inner.csv')
    return cluster.shape[0],combined_csv.shape[0],intersection_DS.shape[0],union_DS.shape[0],intersection_DS.shape[0]/union_DS.shape[0]

def MergeCSVFile(cluster_nums,save_path,smell_type):
    all_filenames = []
    for i in range(0, cluster_nums):
        path = save_path + '\\'+ str(i) + '\\'+smell_type+'.csv'
        print(path)
        all_filenames.append(path)
    print(all_filenames)
    cols = np.arange(5)
    combined_csv = pd.concat([pd.read_csv(os.path.abspath(f), usecols=cols) for f in all_filenames])

    combined_csv.to_csv(save_path +'\\combined.csv', index=False)
    combined_csv.drop_duplicates(inplace=True,subset=['Cause of the Smell', 'Type Name', 'Package Name', 'Design Smell'])
    cluster = pd.read_csv(save_path +'\\cluster\\'+smell_type+'.csv', usecols=cols)
    cluster.drop_duplicates(inplace=True,subset=['Cause of the Smell', 'Type Name', 'Package Name', 'Design Smell'])
    merge_csv = pd.merge(cluster, combined_csv, on=['Cause of the Smell', 'Type Name', 'Package Name', 'Design Smell'],
                         how='inner')
    merge_csv.to_csv(save_path +'\\merge-cause-inner.csv', index=False)

    return cluster.shape[0],merge_csv.shape[0]

def JudgeDS(save_path,smell_type):
    cols = np.arange(5)
    cluster_DS=pd.read_csv(save_path +'\\cluster\\'+smell_type+'.csv', usecols=cols)

    combined_DS=pd.read_csv(save_path +'\\combined.csv')

    merge_DS=pd.read_csv(save_path +'\\merge-cause-inner.csv')

    FP_DS=combined_DS.merge(merge_DS,how = 'outer', on=['Cause of the Smell', 'Type Name', 'Package Name', 'Design Smell'], indicator=True).loc[lambda x : x['_merge']=='left_only']
    FN_DS=cluster_DS.merge(merge_DS,how = 'outer', on=['Cause of the Smell', 'Type Name', 'Package Name', 'Design Smell'], indicator=True).loc[lambda x : x['_merge']=='left_only']


    TP=merge_DS.shape[0]
    FP=FP_DS.shape[0]
    FN=FN_DS.shape[0]

    precision=TP/(TP+FP)
    recall=TP/(TP+FN)
    F1=2*precision*recall/(precision+recall)

    print(TP,FP,FN,precision,recall,F1)
    return TP,FP,FN,precision,recall,F1

if __name__ == '__main__':

    count=0
    BFN = pd.read_csv(gl.AbsolutePath + '/result/' + 'CLUF_result.csv')
    for A, B, C in zip(BFN['Project'], BFN['Version'], BFN['n_clusters']):
        print(B)
        GlobalVarUpdate(A, B)
        if A!="flume":
            continue
        # WholeDJ(C + 1)
        MergeCSVFile(C, gl.DesigniteDetailPath, 'DesignSmells')

        DSproj,DSclus,DSunion,DSintersection,jc=JC(gl.DesigniteDetailPath,'DesignSmells')
        JudgeResult=[A,DSproj,DSclus,DSunion,DSintersection,jc]

        RQ2 = pd.read_csv(gl.AbsolutePath +'/result/' + 'JCofDesignSmell.csv')
        RQ2.loc[RQ2.shape[0]] = JudgeResult
        RQ2.to_csv(gl.AbsolutePath +'/result/' + 'JCofDesignSmell.csv',index=False)
