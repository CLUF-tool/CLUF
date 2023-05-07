import pandas as pd

from utils.ExtractJson import get_repo_log_bug_log, json_filter
from utils.GlobalVarUpdate import *
from utils.SaveResult import save_result

if __name__ == '__main__':

    save_path = gl.data_result_path + '\\historical_data.csv'
    save_header = ['Project', 'Version', 'New Version',
                   'V2 Commits', 'V1 Commits', 'inc Commits',
                   'V2 Bug Commits', 'V1 Bug Commits', 'inc Bug Commits']

    input_data = pd.read_csv(gl.input_data_path + r'\input_project.csv')
    for project, version, branch, next_version, next_branch, jira_key, jira_bugs_amount in zip(
            input_data['project'],
            input_data['exp_version'],
            input_data['exp_branch'],
            input_data['new_version'],
            input_data['new_branch'],
            input_data['jira_key'],
            input_data['jira_bugs_amount']):

        print(project)
        GlobalVarUpdate(project, version)

        # Export history data of current release V1
        bugs, commits, bug_commits = get_repo_log_bug_log(gl.data_project_path, project, version, branch,
                                                          gl.project_middle_path,
                                                          gl.jira_save_path)

        # Export history data of next release V2
        next_repo_path = gl.root_path + '\\git_main'
        new_version = 'next'
        get_repo_log_bug_log(next_repo_path, project, new_version, next_branch, gl.project_middle_path, gl.jira_save_path)

        v2_log_path = gl.project_middle_path + '\\' + new_version + '_tag.json'
        v2_only_log_path = gl.project_middle_path + '\\' + new_version + '_tag_only.json'
        v2_bug_log_path = gl.project_middle_path + '\\' + new_version + '_bug_fix_tag.json'
        v2_only_bug_log_path = gl.project_middle_path + '\\' + new_version + '_bug_fix_tag_only.json'

        # Export log of V1-V2
        v2_commits, v1_commits, increment_commits = json_filter(gl.version_middle_path + '_tag.json', v2_log_path,
                                                                v2_only_log_path)

        # Export bug log of V1-V2
        v2_bug_commits, v1_bug_commits, increment_bug_commits = json_filter(
            gl.version_middle_path + '_bug_fix_tag.json', v2_bug_log_path,
            v2_only_bug_log_path)

        project_historical_data = [project, version, project + '-' + next_version, v2_commits, v1_commits,
                                   increment_commits, v2_bug_commits, v1_bug_commits, increment_bug_commits]
        print(project_historical_data)

        # Save result
        save_result(save_path, project_historical_data, save_header)
