import os
import shutil
import understand
import pandas as pd
import utils.GlobalVar as gl
from utils.CreateUdbExportDM import execCmd
import re





















def CreateUDP(UDPRootPath,UDPName):
    UDPath = UDPRootPath + '/'
    os.chdir(UDPath)
    cmd = 'und create -db ' + UDPName + ' -languages java add ' + UDPath + ' analyze -all'
    result = execCmd(cmd)
    cmd='und analyze '+UDPath + UDPName + '.udb'
    execCmd(cmd)


def ExportFilePathForLexer(UDPRootPath,UDPName):
    UDPath = UDPRootPath + '/'

    db = understand.open(UDPath + UDPName + '.udb')

    absolute_filename=[]
    for file in db.ents('File'):


        java_file=str(file.longname(True))

        if not java_file.endswith('.java'):
            continue
        absolute_filename.append(file.longname(True))

    absolute_filename=pd.DataFrame(absolute_filename)
    absolute_filename.to_csv(gl.DataPath+'-filename.csv',index=False,header=False)


def ExportLog(SavePath, version):
    UDPath = SavePath + '/'
    os.chdir(UDPath)
    execCmd(
        'git log --numstat --pretty="commit-block:commit-hash:%h||message:%s||commiter:%cn||">' + version + '.txt')


def ExportJson(SavePath, version):
    regex = r"(?<=(commit-block:))[\s\S]*?(?=(commit-block:))"

    ExportLog(SavePath,version)
    file_content = ''
    with open(SavePath + '/' + version + '.txt', encoding='utf-8') as f:
        file_context = f.read()
    file_context += 'commit-block:'
    matches = re.finditer(regex, file_context, re.MULTILINE)
    count = 0
    log_json = []
    for matchNum, match in enumerate(matches, start=1):
        single_log = {}




        match_group = match.group().replace('/', '\\')
        cmt_regex = '(?<=commit-hash:).*(?=\|\|message)'
        msg_regex = '(?<=message:).*(?=\|\|commiter)'

        try:
            [commit] = re.findall(cmt_regex, match_group)
            [message] = re.findall(msg_regex, match_group)
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

        mod_status = pd.DataFrame(modified_status, columns=['insertions', 'deletions', 'path'])




        single_log = [commit, commiter, message, mod_status]
        log_json.append(single_log)



    log_json = pd.DataFrame(log_json, columns=['commit', 'commiter', 'message', 'paths'])
    log_json.to_json(SavePath + '\\' + version + '.json', orient='records')