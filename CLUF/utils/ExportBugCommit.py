import pandas as pd


def FilterIssues(jira_path, log_path, bug_fix_path):
    jira_all_issue = pd.read_csv(jira_path)
    # jira_all_issue=pd.read_csv(gl.AbsolutePath+r'\jira'+'\\'+project+'.csv')
    # print(log_path)
    log_json = pd.read_json(log_path)
    commit_message = log_json.message

    count_bugID = 0
    fix_bug_commit = pd.DataFrame(columns=['commit', 'commiter', 'message', 'paths'])
    for bug_ID in jira_all_issue['Issue key']:
        bug_list = bug_ID.split('-')
        new_bug_ID = bug_list[0] + '.' + bug_list[1]
        bool_match = commit_message.str.contains(new_bug_ID, case=False)

        if commit_message[bool_match].empty:
            pass
        else:
            fix_bug_commit = fix_bug_commit.append(log_json[bool_match])
            count_bugID += 1
            b_m_v_c = bool_match.value_counts()
            if b_m_v_c[True] >= 1:
                matched = commit_message.loc[bool_match]

    fix_bug_commit.drop_duplicates(subset=['commit'], inplace=True)
    fix_bug_commit.to_json(bug_fix_path, orient='records')
    return count_bugID,fix_bug_commit.shape[0]
