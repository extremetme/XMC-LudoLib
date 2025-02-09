#
# Read Path Variables %rootDir%, %sitepath% and %sitename% (requires apiXmc.py and apiXmcDict.py call getSitePath)
# varsPath.py v2
#
import os

def readPathVariables(deviceIp, rootDir='/'): # v2 - Obtains a dict of path variables starting from Site of deviceIp
    if not os.path.exists(rootDir):
        exitError("readPathVariables: input root path '{}' does not exist".format(rootDir))
    sitePath = nbiQuery(NBI_Query['getSitePath'], debugKey='sitePath', returnKeyError=True, IP=deviceIp)
    debug("readPathVariables sitePath = {}".format(sitePath))
    # Sample of what we should get back:
    # "/World/CTC-Reading/VSP Sandbox"
    pathList = sitePath.split("/")
    if not len(pathList[0]):
        pathList = pathList[1:]
    if rootDir[-1] == "/":
        rootDir = rootDir[:-1]
    pathVarDict = {
        'rootDir' : rootDir,
        'sitePath': pathList[-1],
        'siteName': "/".join(pathList[:-1]),
    }
    debug("readPathVariables pathVarDict = {}".format(pathVarDict))
    return pathVarDict

def pathVarLookup(inputStr, pathVarDict): # v1 - Replaces path variables %rootDir%, %sitepath% and %sitename% in the input string
    pathVarsUsed = {x.group(1):1 for x in re.finditer(r'%([\w -]+)%', inputStr)}
    outputStr = inputStr
    if pathVarsUsed:
        debug("pathVarLookup pathVarsUsed = {}".format(pathVarsUsed))
        missingVarList = [x for x in pathVarsUsed if x not in pathVarDict]
        if missingVarList:
            exitError("pathVarLookup: the following variables were not found: {}".format(missingVarList))
        for pathVar in pathVarsUsed:
            outputStr = re.sub(r'%' + pathVar + '%', pathVarDict[pathVar], outputStr)
        debug("pathVarLookup {} {} =  {} {}".format(type(inputStr), inputStr, type(outputStr), outputStr))
    return outputStr
