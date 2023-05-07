import math

import numpy as np
import pandas as pd
from numpy import array


def standardize(direction, range_min, range_max, source):
    source_min = min(source)
    source_max = max(source)
    target = []
    if direction == 'pos':
        for data in source:
            t = (data - source_min) / (source_max - source_min)
            target.append((range_max - range_min) * t + range_min)
    elif direction == 'neg':
        for data in source:
            t = (source_max - data) / (source_max - source_min)
            target.append((range_max - range_min) * t + range_min)
    return target

def cal_weight(df):
    rows = df.index.size
    cols = df.columns.size
    k = 1.0 / math.log(rows)

    x = array(df)
    lnf = [[None] * cols for i in range(rows)]
    lnf = array(lnf)
    for i in range(0, rows):
        for j in range(0, cols):
            if x[i][j] == 0:
                lnfij = 0.0
            else:
                p = x[i][j] / np.sum(x, axis=0)[j]
                lnfij = math.log(p) * p * (-k)
            lnf[i][j] = lnfij
    lnf = pd.DataFrame(lnf)
    E = lnf

    d = 1 - E.sum(axis=0)

    w = [[None] * 1 for i in range(cols)]
    for j in range(0, cols):
        wj = d[j] / sum(d)
        w[j] = wj

    w = pd.DataFrame(w)
    w.index = df.columns
    w.columns = ['weight']
    return w