import os
import utils.GlobalVar as gl


def GlobalVarUpdate(project, version):
    gl.project = project
    gl.version = version

    # path of analyzed project
    gl.project_path = gl.data_project_path + '\\' + project
    gl.version_path = gl.project_path + "\\" + version
    gl.UDPath = gl.version_path + ".udb"

    # path of project middle data
    gl.project_middle_path = gl.data_middle_path + '\\' + project
    if not os.path.exists(gl.project_middle_path):
        os.makedirs(gl.project_middle_path)
    gl.version_middle_path = gl.project_middle_path + "\\" + version
    gl.LogPath = gl.version_middle_path + ".json"

    # path of cluster data
    gl.project_cluster_path = gl.data_cluster_path + '\\' + project
    gl.version_cluster_path = gl.project_cluster_path + "\\" + version
    gl.sub_version_cluster_path = gl.version_cluster_path + "\\" + version
    if not os.path.exists(gl.sub_version_cluster_path):
        os.makedirs(gl.sub_version_cluster_path)

    if not os.path.exists(gl.data_result_path):
        os.makedirs(gl.data_result_path)
    gl.result_path = gl.data_result_path + project + '\\' + version
