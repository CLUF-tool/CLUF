import os
import pandas as pd

def save_result(save_path, save_data, save_header):
    if os.path.exists(save_path):
        result = pd.read_csv(save_path)
        result.loc[result.shape[0]] = save_data
    else:
        result = [save_data]
        result = pd.DataFrame(result)
        result.columns = save_header
    result.to_csv(save_path, index=False)


def save_result_vertical(save_path, save_data, save_header):
    result = pd.read_csv(save_path)
    for data, header in zip(save_data, save_header):
        result[header] = data
    result.to_csv(save_path, index=False)
