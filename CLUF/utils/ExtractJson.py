import os
import re
import pandas as pd

from utils.ExecuteCMD import execCmd
from utils.ExportBugCommit import FilterIssues


def get_repo_log_bug_log(repo_root_path, project, version, branch, log_save_path, jira_save_path):
    print(project, version)
    if not os.path.exists(repo_root_path):
        os.makedirs(repo_root_path)
    project_path = repo_root_path + '\\' + project
    if not os.path.exists(project_path):
        os.chdir(repo_root_path)
        git_cmd = 'git clone -b ' + branch + ' git@github.com:apache/' + project + '.git'
        os.system(git_cmd)

    middle_data_path = log_save_path + '\\' + version
    os.chdir(project_path)
    os.system('git checkout ' + branch)
    execCmd(
        'git log --numstat --date=iso-strict-local --pretty="commit-block:commit-hash:%h||message:%s||__unique-date-mark:%cd||commiter:%cn||">' + middle_data_path + '_tag.txt')
    commit_nums = export_log(middle_data_path + '_tag')

    jira_path = jira_save_path + '\\' + project + '.csv'
    log_path = middle_data_path + '_tag.json'
    bug_log_path = middle_data_path + '_bug_fix_tag.json'
    bug_nums, bug_commit_nums = FilterIssues(jira_path, log_path, bug_log_path)

    return bug_nums, commit_nums, bug_commit_nums


def json_filter(old_log_path, new_log_path, filtered_log_path):
    old_log = pd.read_json(old_log_path)
    print(new_log_path)
    new_log = pd.read_json(new_log_path)

    filtered_log = pd.concat([new_log['commit'], old_log['commit'], old_log['commit']]).drop_duplicates(keep=False)
    filtered_log = new_log[new_log['commit'].isin(filtered_log)]
    print(new_log.shape[0], old_log.shape[0], filtered_log.shape[0])
    filtered_log.to_json(filtered_log_path, orient='records')

    return new_log.shape[0], old_log.shape[0], filtered_log.shape[0]


def export_log(source_path):
    regex = r"(?<=(commit-block:))[\s\S]*?(?=(commit-block:))"
    with open(source_path + '.txt', encoding='utf-8') as f:
        # with open(r'D:\program\SC_Related\git-log' + '/' + project+ '/' + project + '.txt', encoding='utf-8') as f:
        file_context = f.read()
    file_context += 'commit-block:'
    matches = re.finditer(regex, file_context, re.MULTILINE)
    count = 0
    log_json = []

    for matchNum, match in enumerate(matches, start=1):
        match_group = match.group().replace('/', '\\')
        cmt_regex = '(?<=commit-hash:).*(?=\|\|message)'
        msg_regex = '(?<=message:).*(?=\|\|__unique-date-mark)'
        date_regex = '(?<=__unique-date-mark:).*(?=\|\|commiter)'

        try:
            [commit] = re.findall(cmt_regex, match_group)
            [message] = re.findall(msg_regex, match_group)
            [date] = re.findall(date_regex, match_group)
        except ValueError:
            break
        cmter_regex = '(?<=commiter:).*(?=\|\|)'
        [commiter] = re.findall(cmter_regex, match_group)
        count = 0
        modified_status = []

        for line in match_group.splitlines():
            count += 1
            if (count < 3):
                continue
            sep_line = line.split('\t')
            modified_status.append(sep_line)
        date = date[:-6].replace('T', ' ')
        mod_status = pd.DataFrame(modified_status, columns=['insertions', 'deletions', 'path'])
        single_log = [commit, commiter, date, message, mod_status]
        log_json.append(single_log)

    log_json = pd.DataFrame(log_json, columns=['commit', 'commiter', 'date', 'message', 'paths'])
    # log_json.to_json(r'D:\program\SC_Related\git-exp'+'\\'+project + '\\' + version + '.json', orient='records')
    log_json.to_json(source_path + '.json', orient='records')
    return log_json.shape[0]
