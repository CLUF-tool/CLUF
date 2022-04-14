import os
import shutil
import pandas as pd
import utils.GlobalVar as gl

def GenerateFolder(ClusterPath,cluster_num,Type):
    HCPath=gl.DataPath+"\\"+'euc_dist'+"\\"+str(cluster_num)+'\\'+Type+'.csv'
    # 这个用于已知Threshold后单独生成文件夹
    # HCPath = gl.DataPath + "\\" + 'distance\\' + threshold + '\\HCLabel.csv'
    HCResult=pd.read_csv(HCPath, names=["Path","cluster_nums"])
    # CN=HCResult.cluster_nums.max()
    # CN=1
    for A,B in zip(HCResult["Path"],HCResult["cluster_nums"]):
        # print(A,B)
        # if CN!=B:
        #     CN=B
        CP=ClusterPath + str(B)
        if not os.path.exists(CP):
            os.makedirs(CP)
        name = os.path.basename(A)
        if not os.path.exists(os.path.join(CP, name)):
            shutil.copy(A, CP)
        else:
            base, extension = os.path.splitext(name)
            i = 1
            while os.path.exists(os.path.join(CP, '{}_{}{}'.format(base, i, extension))):
                i += 1
            shutil.copy(A, os.path.join(CP, '{}_{}{}'.format(base, i, extension)))
