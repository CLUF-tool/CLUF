import pandas as pd
import understand


def export_file_loc(udp_path, save_path):
    db = understand.open(udp_path)
    file_list = []
    file_loc = []
    for file in db.ents('File'):
        metric = file.metric(("CountLineCode",))

        if metric["CountLineCode"] is not None:
            java_file = str(file.longname(True))
            file_list.append(java_file)
            loc = metric["CountLineCode"]
            file_loc.append(loc)

    save_result = pd.DataFrame()
    save_result['Name'] = file_list
    save_result['CountLineCode'] = file_loc
    save_result.to_csv(save_path, index=False)