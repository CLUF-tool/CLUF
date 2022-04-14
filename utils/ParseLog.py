import pandas as pd
import numpy as np
import utils.GlobalVar as gl

def GenerateCCMatrix(FileList,FileName,cluster_matrix):
    mod_set = set()
    for i,d,f in zip(FileList['insertions'],FileList['deletions'],FileList['path']):  
        f = f.replace("/", "\\")
        t = FileName.Path.str.contains(f, regex=False)
        if FileName[t].empty:  
            pass
        else:
            idx = int(FileName[t].index.values[0])

            mod_set.add(idx)
    
    if len(mod_set)>1:
        for i in mod_set:
            for j in mod_set:
                if i!=j:
                    cluster_matrix[i][j]+=1

def LogParser(JSONLogPath):
    JSONLog=pd.read_json(JSONLogPath,orient="records")
    FileNameList=pd.read_csv(gl.DataPath+'-filename.csv', names=["Path"])
    m=FileNameList.shape[0]
    cluster_matrix=np.zeros((m,m),dtype=int)
    for FileList in JSONLog.paths:
        if len(FileList)==0:
            continue
        File=pd.DataFrame(FileList)
        javaFile=File[File['path'].str.contains("\.java")]
        if len(javaFile)==0:
            continue
        GenerateCCMatrix(javaFile,FileNameList,cluster_matrix)
    temp = pd.DataFrame(cluster_matrix)
    temp.to_csv(gl.DataPath+"-coMatrix.csv",index=False,header=None)
