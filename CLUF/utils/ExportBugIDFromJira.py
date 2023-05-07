import os
import urllib
import urllib.request
import urllib.request
import pandas as pd



def download_csv(jira_key,project, part, jira_save_path):
    csv_url_head = 'https://issues.apache.org/jira/sr/jira.issueviews:searchrequest-csv-current-fields/temp/SearchRequest.csv?jqlQuery=project+%3D+'
    csv_url_tail = '+AND+issuetype+%3D+Bug+ORDER+BY+priority+DESC%2C+updated+DESC&tempMax=1000'
    pager_start = '&pager/start='
    csv_url = csv_url_head + jira_key + csv_url_tail + pager_start + str(part * 1000)

    dest_part_path = jira_save_path + '\part' + '\\' + project + str(part) + '.csv'

    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36 Edg/99.0.1150.30'}  # 设置http header
    request = urllib.request.Request(csv_url, headers=header)
    try:
        response = urllib.request.urlopen(request)
        if (response.getcode() == 200):
            with open(dest_part_path, "wb") as f:
                f.write(response.read())  # 将内容写入图片
            return dest_part_path
    except:
        return "failed"


def merge_part(project, jira_save_path):
    inputdir = jira_save_path + '\\part'
    if not os.path.exists(inputdir):
        os.makedirs(inputdir)
    df_empty = pd.DataFrame(
        columns=['Issue Type', 'Issue key', 'Issue id', 'Summary', 'Assignee', 'Reporter', 'Priority', 'Status',
                 'Resolution', 'Created', 'Updated', 'Due Date'])
    for parents, dirnames, filenames in os.walk(inputdir):
        # print(parents, dirnames, filenames)
        for filename in filenames:
            # print(filename)
            file_path = os.path.join(parents, filename)
            print(file_path)
            df = pd.read_csv(file_path)
            df_empty = df_empty.append(df, ignore_index=True)
            os.remove(file_path)

    print(df_empty.shape)
    df_empty.to_csv(jira_save_path + '\\' + project + '.csv', index=False)