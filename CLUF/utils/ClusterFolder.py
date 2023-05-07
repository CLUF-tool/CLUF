import os
import shutil

import pandas as pd


def GenerateFolder(cluter_label_path, cluster_path):
    cluter_label = pd.read_csv(cluter_label_path, names=["Path", "cluster_nums"])
    for A, B in zip(cluter_label["Path"], cluter_label["cluster_nums"]):

        CP = cluster_path + '\\' + str(B)
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

