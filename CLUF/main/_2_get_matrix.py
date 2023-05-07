import pandas as pd

from utils.ExportLOC import export_file_loc
from utils.ExportLogCreateUDB import ExportFilePathForLexer
from utils.GlobalVarUpdate import *
from utils.ParseLog import LogParser
from utils.SimOutput import UDPFileParse, GetSematicEntrance

if __name__ == '__main__':

    v_type = ['c2v_tfidf']
    input_data = pd.read_csv(gl.root_path+r'\input\input_project.csv')
    for project, version in zip(input_data['project'], input_data['exp_version']):

        print(project)
        GlobalVarUpdate(project, version)

        # Analyze source code by Understand
        ExportFilePathForLexer(gl.UDPath, gl.version_middle_path + '-filename.csv')
        UDPFileParse(gl.version_middle_path, gl.UDPath)

        # Generate seMatrix
        for vectorized_type in v_type:
            if os.path.exists(gl.version_middle_path + "-seMatrix-" + vectorized_type + ".csv"):
                pd.read_csv(gl.version_middle_path + "-seMatrix-" + vectorized_type + ".csv", header=None)
            else:
                GetSematicEntrance(gl.version_middle_path, vectorized_type)

        # Generate coMatrix
        if os.path.exists(gl.version_middle_path + "_coMatrix_tag.csv"):
            pass
        else:
            log_path = gl.version_middle_path + '_tag.json'
            coMatrix_path = gl.version_middle_path + '_coMatrix_tag.csv'
            LogParser(gl.version_middle_path, log_path, coMatrix_path)

        # Export LOC data of each files
        loc_path = gl.version_middle_path + '_LOC.csv'
        export_file_loc(gl.UDPath, loc_path)
