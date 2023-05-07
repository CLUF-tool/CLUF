
project=''
version=''

root_path=r'D:\program\SC_Related'

# path of analyzed project

input_data_path=root_path + r'\input'
jira_save_path = input_data_path + r'\jira'

data_project_path=root_path+r"\git_tag"

project_path = data_project_path+'\\'+project
version_path = project_path + "\\" + version

UDPath = version_path + ".udb"

# path of project middle data
data_middle_path=root_path+r"\data_middle"
project_middle_path = data_middle_path+'\\'+project
version_middle_path = project_middle_path + "\\" + version
LogPath = version_middle_path+".json"

# path of cluster data
data_cluster_path=root_path+r"\data_cluster"
project_cluster_path = data_cluster_path+'\\'+project
version_cluster_path = project_cluster_path + "\\" + version
sub_version_cluster_path = version_cluster_path + "\\" + version

# path of result data
data_result_path=root_path+r"\data_result"
# OutputRootPath = CLUFResultPath+r"\\output\\"
result_path= data_result_path +'\\'+ project + '\\' + version
