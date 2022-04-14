import os
import utils.GlobalVar as gl

def GlobalVarUpdate(Project,Version):
    gl.projectCommon = Project
    gl.versionCommon = Version

    gl.RootPathGithub = gl.AbsolutePath + '/input/Github/' + gl.projectCommon
    gl.FirstPathGithub = gl.RootPathGithub + "/" + gl.versionCommon
    
    gl.OutputRootPath = gl.AbsolutePath + "/output/"
    gl.DTPath = gl.OutputRootPath + gl.projectCommon + '/' + gl.versionCommon
    
    gl.DataPath = gl.DTPath + "/" + gl.versionCommon
    if not os.path.exists(gl.DataPath):
        os.makedirs(gl.DataPath)

    gl.LogPath = gl.FirstPathGithub + ".json"
    gl.UDPath = gl.FirstPathGithub + ".udb"
    
    gl.DesignitePath = r"D:\program\DesigniteJava" + '/'
    gl.DesigniteDetailPath = gl.DTPath + '/DesigniteJava'
