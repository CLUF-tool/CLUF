import pandas as pd
import utils.GlobalVar as gl

from utils.ExecuteCMD import execCmd


def Export_Directory_RSF(ground_truth_rsf_path):
    '''
    用于外部指标，导出目录依赖
    contain 目录 文件名
    '''
    filename_path = gl.version_middle_path + "-filename.csv"
    Directory_label = pd.read_csv(filename_path, names=['path'])
    # print(Directory_label)
    # print(gl.RootPathGithub+'\\')
    Directory_label['path'] = Directory_label['path'].str.replace(gl.project_path + '\\', '', regex=False)
    Directory_label['path'] = Directory_label['path'].str.replace('\\', '.', regex=False)
    Directory_label['Arch'] = Directory_label['path'].str.extract(r'([^\s]*(?=\.src|org\.))', expand=False)
    Directory_label['Arch'] = Directory_label['Arch'].fillna('root')
    # print(Directory_label)

    RSF_Data = Directory_label[['Arch', 'path']]
    RSF_Data.insert(0, 'contain', 'contain')

    RSF_Data.to_csv(ground_truth_rsf_path, sep=' ', index=None, header=None)


def Export_Clustering_RSF(cluster_label_path, cluster_rsf_path):
    '''
    用于外部指标，导出聚类依赖
    contain 聚类号 文件名
    '''

    # cluster_label_path=gl.DataPath + "\\" + vectorize_type + "\\" + cluster_type + "\\"

    cluster_label = pd.read_csv(cluster_label_path, names=['path', 'cluster_label'])

    cluster_label['path'] = cluster_label['path'].str.replace(gl.project_path + '\\', '', regex=False)
    cluster_label['path'] = cluster_label['path'].str.replace('\\', '.', regex=False)
    # cluster_label['path']=cluster_label['path'].str.replace('.*(?=(org.apache.))','',regex=True)
    # cluster_label['path']=cluster_label['path'].str.replace('(.java)$','',regex=True)

    RSF_Data = cluster_label[['cluster_label', 'path']]
    RSF_Data.insert(0, 'contain', 'contain')

    RSF_Data.to_csv(cluster_rsf_path, sep=' ', index=None, header=None)


def ExternalMetrics(cluster_rsf, ground_truth_rsf):
    MoJoFM = execCmd(
        "java -jar " + gl.metrics_jar_path + r"\MoJo\mojo.jar " + ground_truth_rsf + " " + cluster_rsf + ' -fm')
    A2A = execCmd("java -jar " + gl.metrics_jar_path + r"\A2A\A2A.jar " + ground_truth_rsf + " " + cluster_rsf)

    MoJoFM = round(float(MoJoFM), 1)
    A2A = round(float(A2A), 1)

    return MoJoFM, A2A
