import os
import utils.GlobalVar as gl
import understand
import pandas as pd
import numpy as np

def execCmd(cmd):
    r = os.popen(cmd)
    text = r.read()
    r.close()
    return text

def CreateUnderstandProject(CouplingType):
    UDPath = gl.DTPath + '\\' + CouplingType + '\\'
    os.chdir(UDPath)
    cmd = 'und create -db ' + CouplingType + ' -languages java add ' + UDPath + ' analyze -all'
    result = execCmd(cmd)



def ReportClusterArchs(CouplingType):
    UDPath = gl.DTPath + '\\' + CouplingType + '\\'
    db = understand.open(UDPath + CouplingType + '.udb')

    cluster_nums = 0
    for i in db.root_archs():
        for arch_i in i.children():
            cluster_nums += 1

    CD = []
    count=0

    for file in db.ents('File'):


        java_file = str(file.longname(True))

        if not java_file.endswith('.java'):
            continue
        [a] = db.archs(file)


        a_dict = file.depends()
        for key, value in a_dict.items():
            ClusterDependecy = []
            ClusterDependecy.append(str(a))
            [b] = db.archs(key)
            ClusterDependecy.append(str(b))
            ClusterDependecy.append(len(value))
            CD.append(ClusterDependecy)

    CD = pd.DataFrame(CD)
    CD.to_csv(UDPath + 'ClusterDependecy.csv', index=False, header=False)
    return CD, cluster_nums

def InterRefRelation(CouplingType,CD,Size):

    DependMatrix = np.zeros((Size, Size), dtype=int)
    DependencyData = CD

    for A, B, C in zip(DependencyData[0], DependencyData[1], DependencyData[2]):
        a = int(A) - 1
        b = int(B) - 1
        DependMatrix[a][b] += C

    DM = pd.DataFrame(DependMatrix)
    DM.to_csv(gl.DTPath + '\\' + CouplingType + '\\'+'DM.csv',index=False,header=False)
    return DM