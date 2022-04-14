import os
import utils.GlobalVar as gl
import re
import pandas as pd

def execCmd(cmd):
  r = os.popen(cmd)
  text = r.read()
  r.close()
  return text

def DesigniteJava(SrcPath,DesPath):
    print(SrcPath)
    print(DesPath)


    cmd = 'java -jar DesigniteJava.jar -i ' + SrcPath + ' -o ' + DesPath
    result = execCmd(cmd)
    print(result)
    AmountRe='(?<=: )[0-9]*'

    strAmount=re.findall(AmountRe, result)
    Amount=[int(i) for i in strAmount]
    return Amount
























def WholeDJ(ClusterNums):
    DataRootPath=os.getcwd()



    SrcPath = os.path.abspath(gl.DTPath)+ '\cluster'

    DesPath=os.path.abspath(gl.DesigniteDetailPath)

    AllAmount=[]

    os.chdir(gl.DesignitePath)
    for i in range(ClusterNums):
        print('Scan Cluster:', i, 'of', ClusterNums-1)
        if i==ClusterNums-1:
            print(i,'cluster-designite')


            Amount=DesigniteJava(SrcPath,DesPath+ '\cluster')
            Amount.insert(0,'Cluster')
        else:

            Amount=DesigniteJava(SrcPath+'\\'+str(i),DesPath+'\\'+str(i))
            Amount.insert(0, i)
        Amount.insert(0, gl.versionCommon)
        AllAmount.append(Amount)

    os.chdir(DataRootPath)
















