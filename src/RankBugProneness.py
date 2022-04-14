import os
import pandas as pd
import utils.GlobalVar as gl
from utils.ExportBugCommit import FilterIssues
from utils.FixingChurn import FCRate
from utils.GlobalVarUpdate import GlobalVarUpdate

BatchData = pd.read_csv(gl.AbsolutePath + '/result/' + 'CLUF_result.csv')
count=0
for A, B, C in zip(BatchData['Project'], BatchData['Version'], BatchData['n_clusters']):
    print(B)
    GlobalVarUpdate(A, B)
    if os.path.exists(gl.FirstPathGithub+'_bug_fix.json'):
        pass
    else:
        FilterIssues(A,B)
    top_10, top10_BC, fileSum_10_rate, top_20, top20_BC, fileSum_20_rate = FCRate(C)
    BCResult = [A,top_10, top10_BC, fileSum_10_rate, top_20, top20_BC, fileSum_20_rate]

    RQ3 = pd.read_csv(gl.AbsolutePath + '/result/' + 'StatusOfBugProneness.csv')
    RQ3.loc[RQ3.shape[0]] = BCResult
    RQ3.to_csv(gl.AbsolutePath + '/result/' + 'StatusOfBugProneness.csv', index=None)

