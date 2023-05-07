import os
import utils.GlobalVar as gl
import re
from utils.ExecuteCMD import execCmd


def DesigniteJava(SrcPath, DesPath):
    # print(SrcPath)
    # print(DesPath)

    cmd = 'java -jar DesigniteJava.jar -i ' + SrcPath + ' -o ' + DesPath
    result = execCmd(cmd)
    # print(result)
    AmountRe = '(?<=: )[0-9]+'

    strAmount = re.findall(AmountRe, result)
    # print(len(strAmount),strAmount)
    Amount = [int(i) for i in strAmount]

    return Amount


def WholeDJ(ClusterNums, SrcPath, DesPath):
    DataRootPath = os.getcwd()
    # print(DataRootPath)
    # print(DesPath)
    # DesPath=gl.DesigniteResultPath+'\\'+vectorize_type+'\\'+Cluster_type
    AllAmount = [gl.version]

    os.chdir(gl.designite_path)
    for i in range(ClusterNums - 1, -1, -1):
        if i == ClusterNums - 1:
            Amount = DesigniteJava(SrcPath, DesPath + '\Cluster')
            Amount.insert(0, 'Cluster')
        else:
            Amount = DesigniteJava(SrcPath + '\\' + str(i), DesPath + '\\' + str(i))
            Amount.insert(0, i)
        AllAmount.append(Amount)

    os.chdir(DataRootPath)
