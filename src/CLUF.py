import numpy as np

from utils.ClusterFolder import GenerateFolder
from utils.ExportLogCreateUDB import *
from utils.GetMaxHCRate import *
from utils.SimOutput import LatentSemanticAnalysis
from utils.ParseLog import LogParser


DataItem=[]
DataItem.append(gl.projectCommon)
DataItem.append(gl.versionCommon)

ExportJson(gl.RootPathGithub, gl.versionCommon)

ExportFilePathForLexer(gl.RootPathGithub, gl.versionCommon)

print('1.Semantic Similarity Matrix Generation')
if os.path.exists(gl.DataPath + "-seMatrix.csv"):
    cos_sim = pd.read_csv(gl.DataPath + "-seMatrix.csv", header=None)
else:
    UDPParseFlag = True
    cos_sim = LatentSemanticAnalysis(gl.DataPath, gl.UDPath, UDPParseFlag)
cos_sim=np.around(cos_sim,2)
DataItem.append(cos_sim.shape[0])
euc_dist = (2 - 2 * cos_sim) ** (1 / 2)
euc_dist=np.around(euc_dist,2)
euc_dist = pd.DataFrame(euc_dist)
euc_dist.fillna(0, inplace=True)
euc_dist.to_csv(gl.DataPath+'-euc.csv')

print('2.Co-Change Matrix Generation')
if os.path.exists(gl.DataPath + "-coMatrix.csv"):
    pass
else:
    LogParser(gl.LogPath)

print('3.Hierarchy Cluster Process')
FileSum=euc_dist.shape[0]
midMax, midMaxIndex = Sklearn_AHC_Max(euc_dist,FileSum)

DataItem.append(midMaxIndex)
DataItem.append(midMax)

GenerateFolder(gl.DTPath + '\\Cluster\\', midMaxIndex, 'HCLabel')

DIA=pd.read_csv(gl.AbsolutePath +'/result/' + 'CLUF_result.csv')
DIA.loc[DIA.shape[0]]=DataItem
DIA.to_csv(gl.AbsolutePath +'/result/' + 'CLUF_result.csv', index=False)

print("Done!")