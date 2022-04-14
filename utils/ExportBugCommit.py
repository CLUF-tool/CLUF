import pandas as pd
import utils.GlobalVar as gl
def FilterIssues(project,version):
    jira_all_issue=pd.read_csv(gl.AbsolutePath+r'\input\jira'+'\\'+project+'.csv')

    log_json=pd.read_json(gl.FirstPathGithub+'.json')

    commit_message = log_json.message

    count_bugID=0

    fix_bug_commit=pd.DataFrame(columns=['commit','commiter','message','paths'])
    for bug_ID in jira_all_issue['Issue key']:
        bug_list = bug_ID.split('-')
        new_bug_ID = bug_list[0] + '.' + bug_list[1]
        bool_match = commit_message.str.contains(new_bug_ID, case=False)


        if commit_message[bool_match].empty:
            pass
        else:


            fix_bug_commit=fix_bug_commit.append(log_json[bool_match])
            count_bugID+=1
            b_m_v_c = bool_match.value_counts()
            if b_m_v_c[True] >= 1:
                matched = commit_message.loc[bool_match]


    fix_bug_commit.drop_duplicates(subset=['commit'],inplace=True)

    fix_bug_commit.to_json(gl.FirstPathGithub+'_bug_fix.json',orient='records')

def FromBugzilla():
    log_json=pd.read_json(gl.FirstPathGithub+'.json')
    bug_commit=log_json[log_json.message.str.contains("bugzilla")]
    print(bug_commit)
    bug_commit.to_json(gl.FirstPathGithub+'_bug_fix.json',orient='records')





