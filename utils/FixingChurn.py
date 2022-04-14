import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np
import utils.GlobalVar as gl
from collections import Counter
from matplotlib.ticker import FuncFormatter
from utils.ChangeAVGRate import divZero
def to_percent(temp, position):
    return '%1.0f'%(100*temp) + '%'


def ARPlot(cluster_statics, AccumulateRate, top_10,top10_BC,top_20, top20_BC):
    fig, ax = plt.subplots(figsize=(10, 5), dpi=100)

    plt.ylabel(u'Fixing Churn', fontsize=14)
    plt.xlabel(u'Cluster Numbers', fontsize=14)
    x = np.arange(0, len(cluster_statics) ,1)

    plt.tick_params(labelsize=12)
    plt.locator_params('both',nbins=10)
    plt.gca().yaxis.set_major_formatter(FuncFormatter(to_percent))

    plt.scatter(x, AccumulateRate,s=10, color="dodgerblue", label='one')
    plt.scatter(top_10-1, top10_BC,s=50, color="r", linewidth=4, marker='.')
    plt.scatter(top_20-1, top20_BC,s=50, color="r", linewidth=4, marker='.')

    bbox = dict(boxstyle="round", fc="1")
    arrowprops = dict(
        arrowstyle="->",
        connectionstyle = 'Angle3')

    ax.annotate('Top_10%% (%d, %.1f%%)' % (top_10, top10_BC*100),
                (top_10-1, top10_BC), xytext= (+30,-30), textcoords='offset points',
                bbox=bbox, arrowprops=arrowprops,fontsize=16)
    ax.annotate('Top_20%% (%d, %.1f%%)' % (top_20, top20_BC*100),
                (top_20-1, top20_BC), xytext= (+30,-30), textcoords='offset points',
                bbox=bbox, arrowprops=arrowprops,fontsize=16)

    plt.savefig(gl.DataPath+'-FC.pdf',bbox_inches='tight')

    plt.close()


def FCRate(n_clusters):
    JSON_log = pd.read_json(gl.FirstPathGithub+'_bug_fix.json')
    FileCluster = pd.read_csv(gl.DataPath + "\\" + 'euc_dist' + "\\" + str(n_clusters) + '\\HCLabel.csv',
                              names=["Path", "clusterLabels"])
    SumFilesPerCluster = Counter(FileCluster["clusterLabels"])

    l = FileCluster.clusterLabels.max()
    cluster_statics = [0] * (l + 1)
    for mod_file_list in JSON_log.paths:





        for mod_file in mod_file_list:

            java_mod_file = mod_file['path']
            if java_mod_file.endswith(".java"):

                FC = FileCluster.Path.str.contains(java_mod_file, regex=False)
                if FileCluster[FC].empty:
                    pass
                else:
                    modified = int(mod_file['insertions']) + int(mod_file['deletions'])
                    idx = int(FileCluster[FC].index.values[0])

                    C_nums = FileCluster.loc[idx, "clusterLabels"]

                    cluster_statics[C_nums] += modified


    ModifiedSum = sum(cluster_statics)
    top_20 = round(n_clusters*0.2)
    top_10=round(n_clusters*0.1)







    FileSum_10_rate,FileSum_20_rate=TopFileSum_10_20(top_10,top_20,cluster_statics,SumFilesPerCluster)


    cluster_statics.sort(reverse=True)



    AccumulateRate = [divZero(cluster_statics[0] ,ModifiedSum)]
    for i in range(1, n_clusters):
        t = divZero(cluster_statics[i] , ModifiedSum)
        AccumulateRate.append(AccumulateRate[i - 1] + t)

    top10_BC=AccumulateRate[top_10-1]
    top20_BC = AccumulateRate[top_20 - 1]
    ARPlot(cluster_statics,AccumulateRate,top_10,top10_BC,top_20, top20_BC)


    return top_10,top10_BC,FileSum_10_rate,top_20, top20_BC,FileSum_20_rate


def TopFileSum_10_20(top_10,top_20, cluster_statics, SumFilesPerCluster):
    CSDict = dict(enumerate(cluster_statics, start=1))

    CSOrder = sorted(CSDict.items(), key=lambda x: x[1], reverse=True)


    i=0
    FileSum_10=0
    FileSum_20=0
    for (x,y) in CSOrder:


        i+=1
        FileSum_20+=SumFilesPerCluster[x]
        if i<=top_10:
            FileSum_10+=SumFilesPerCluster[x]
        if i>=top_20:
            break

    projectFileSum=sum(SumFilesPerCluster.values())

    return FileSum_10/projectFileSum,FileSum_20/projectFileSum












