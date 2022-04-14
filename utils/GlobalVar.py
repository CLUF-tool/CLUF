import os


projectCommon="kylin"
versionCommon="kylin-1.5.1"
DesignitePath=r"D:\program\DesigniteJava"+'/'



DataInAllPath="../"
AbsolutePath=os.path.abspath(DataInAllPath)

RootPathGithub = AbsolutePath+'/input/Github/'+projectCommon
FirstPathGithub = RootPathGithub + "/" + versionCommon

OutputRootPath = AbsolutePath+"/output/"
DTPath= OutputRootPath + projectCommon + '/' + versionCommon

DataPath = DTPath+ "/" + versionCommon
if not os.path.exists(DataPath):
    os.makedirs(DataPath)

LogPath = FirstPathGithub+".json"
UDPath = FirstPathGithub + ".udb"

DesigniteDetailPath=DTPath+'/DesigniteJava'