import understand
import pandas as pd


def ExportFilePathForLexer(UDPath, file_data_path):
    # UDPath = UDPRootPath + '/'
    # print(UDPath)
    db = understand.open(UDPath)
    absolute_filename = []

    for file in db.ents('File'):
        java_file = str(file.longname(True))
        if not java_file.endswith('.java'):
            continue
        absolute_filename.append(file.longname(True))

    absolute_filename = pd.DataFrame(absolute_filename)
    absolute_filename.to_csv(file_data_path, index=False, header=False)
