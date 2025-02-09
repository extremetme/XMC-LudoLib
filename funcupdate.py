# Written by Ludovico Stevens, TME Extreme Networks
# Checks latest versions of library functions then compares and applies them to selected script(s)

__version__ = 1.00;

Description = '''
Script Version {}. Checks latest versions of library functions
 then compares and applies them to selected script(s).
'''.format(__version__)

#
# Imports:
#
import os
import sys
import glob
import re
import time
import argparse

#
# Variables:
#
Debug = False    # Enables debug messages
Sanity = False   # If enabled, config commands are not sent to host (show commands are operational)
FuncPath = "C:/Users/lstevens/Scripts/X-Python/XMC/functions" # Path of latest library files
RegexLibFile = re.compile('# (\w+\.py)(?: +v(\d+))?')
RegexFunction = re.compile('def (\w+)\(.+?\): +# +v(\d+)')
RegexBanner = re.compile('# \w+')
RegexMain = re.compile('def main():')


#
# Functions
#

def debug(debugOutput): # v2 - Use function to include debugging in script; set above Debug variable to True or False to turn on or off debugging
    if Debug:
        print "[{}] {}".format(time.ctime(), debugOutput)


def exitError(errmsg): # v1 - Exit script with error message and setting status appropriately
    print "ERROR: " + errmsg
    sys.exit(1)


def getUserParams(): # Set up argparse
    parser = argparse.ArgumentParser(description=Description + '='*78)
    parser.add_argument('-d', '--debug', action='store_true', help="Debug") # action='store_true' so that no value expected for option
    parser.add_argument('-s', '--sanity', action='store_true', help="Sanity") # shitty argparse...
    parser.add_argument('filename', nargs='?')
    return parser.parse_args()


def getLatestFuncVersions(funcPath): # Read latest library function versions
    funcDict = {
#       <libfile.py>: {
#           version: <version>,
#           functions: {
#               <func1>: <version>,
#               <func2>: <version>,
#           }
#       }
    }
    if not re.search(r'[\/]$', funcPath):
        funcPath += "/"
    funcPath += "*.py"
    debug("funcPath: {}".format(funcPath))
    for pyFile in glob.glob(funcPath):
        #debug("File: {}".format(pyFile))
        fileKey = None
        with open(pyFile, 'r') as f:
            for line in f:
                libFile = RegexLibFile.match(line)
                if libFile:
                    if libFile.group(1) != os.path.basename(pyFile):
                        exitError("File {} reportes itself as {}".format(os.path.basename(pyFile), libFile.group(1)))
                    fileKey = libFile.group(1)
                    funcDict[fileKey] = {'version': libFile.group(2), 'functions': {}}
                    continue
                function = RegexFunction.match(line)
                if function:
                    if not fileKey:
                        exitError("File {} hit function '{}()' and missed initial banner".format(os.path.basename(pyFile), function.group(1)))
                    if function.group(1) in funcDict[fileKey]['functions']:
                        exitError("File {} has duplicate function '{}()'".format(os.path.basename(pyFile), function.group(1)))
                    funcDict[fileKey]['functions'][function.group(1)] = function.group(2)

    print "\nLatest libfiles and functions"
    print "=" * 90
    for fileKey in sorted(funcDict.keys()):
        print "{:34} version {:>4}".format(fileKey, funcDict[fileKey]['version'])
        for function in sorted(funcDict[fileKey]['functions'].keys()):
            print "    {:30} version {:>4}".format(function + "()", funcDict[fileKey]['functions'][function])
        print
    return funcDict


def getScriptVersions(filePath): # Read input script function versions
    scriptDict = {
#       <libfile.py>: {
#           version: <version>,
#           functions: {
#               <func1>: <version>,
#               <func2>: <version>,
#           }
#       }
    }
    with open(filePath, 'r') as f:
        fileKey = 'orphan'
        for line in f:
            libFile = RegexLibFile.match(line)
            if libFile:
                #debug("LIBR: {}".format(line))
                fileKey = libFile.group(1)
                scriptDict[fileKey] = {'version': libFile.group(2), 'functions': {}}
                continue
            if RegexBanner.match(line):
                #debug("BANN: {}".format(line))
                fileKey = 'orphan'
                continue
            if RegexMain.match(line):
                #debug("MAIN: {}".format(line))
                break
            function = RegexFunction.match(line)
            if function:
                if fileKey == 'orphan' and fileKey not in scriptDict:
                    scriptDict[fileKey] = {'version': None, 'functions': {}}
                scriptDict[fileKey]['functions'][function.group(1)] = function.group(2)

    print "\nLibfiles and function versions used by script '{}'".format(os.path.basename(filePath))
    print "=" * 90
    for fileKey in sorted(scriptDict.keys()):
        print "{:34} version {:>4}".format(fileKey, scriptDict[fileKey]['version'])
        for function in sorted(scriptDict[fileKey]['functions'].keys()):
            print "    {:30} version {:>4}".format(function + "()", scriptDict[fileKey]['functions'][function])
        print
    return scriptDict


def checkVersionMatrix(funcDict, filename, scriptDict): # Print matrix comparison of function versions
    newerVersionsExist = False
    canUpdateFlag = True
    print "\nMatrix of libfiles and function versions used by script '{}'".format(os.path.basename(filename))
    print "=" * 90
    for fileKey in sorted(scriptDict.keys()):
        line = "{:34} version {:>4}".format(fileKey, scriptDict[fileKey]['version'])
        if scriptDict[fileKey]['version']:
            line += " - "
            if fileKey in funcDict:
                if scriptDict[fileKey]['version'] == funcDict[fileKey]['version']:
                    line += "is latest"
                elif scriptDict[fileKey]['version'] < funcDict[fileKey]['version']:
                    line += "latest is v{:4}".format(funcDict[fileKey]['version'])
                    newerVersionsExist = True
                else:
                    line += "newer than master!! v{:4}".format(funcDict[fileKey]['version'])
                    canUpdateFlag = False
            else:
                line += "libfile not found"
                canUpdateFlag = False
        print line
        for function in sorted(scriptDict[fileKey]['functions'].keys()):
            line = "    {:30} version {:>4} - ".format(function + "()", scriptDict[fileKey]['functions'][function])
            if fileKey in funcDict and function in funcDict[fileKey]['functions']:
                funcKey = fileKey
                searchFlag = False
            else: # We try and find the function..
                funcKey = None
                for searchKey in funcDict:
                    if function in funcDict[searchKey]['functions']:
                        funcKey = searchKey
                        searchFlag = True
                        break
            if funcKey and function in funcDict[funcKey]['functions']:
                if scriptDict[fileKey]['functions'][function] == funcDict[funcKey]['functions'][function]:
                    line += "is latest      "
                elif scriptDict[fileKey]['functions'][function] < funcDict[funcKey]['functions'][function]:
                    line += "latest is v{:4}".format(funcDict[funcKey]['functions'][function])
                    newerVersionsExist = True
                else:
                    line += "NEWER!!!! v{:4}".format(funcDict[funcKey]['functions'][function])
                    canUpdateFlag = False
                if searchFlag:
                    line += " found in {}".format(funcKey)
                    canUpdateFlag = False
            else:
                line += "function not found"
                canUpdateFlag = False
            print line
        print
    if newerVersionsExist:
        print "--> Newer versions of functions exist"
        if canUpdateFlag:
            print "--> Updates can be performed"
        else:
            print "--> Updates are NOT possible due to issues!!"
        print
    else:
        if not canUpdateFlag:
            print "--> Updates would NOT be possible due to issues!!"
            print
    return newerVersionsExist, canUpdateFlag


def updateScript(funcPath, funcDict, filePath): # Perform update of script file
    if not re.search(r'[\/]$', funcPath):
        funcPath += "/"
    if Sanity:
        originalFile = filePath                                     # inputscript.py
        writeFile    = re.sub(r'\.py', r'.sanity', filePath)        # sanity.py
    else:
        backupFile = re.sub(r'\.py', r'.bak', filePath)             # inputscript.bak
        try:
            os.rename(filePath, backupFile) # Make backup of script # inputscript.py --> inputscript.bak
        except Exception as e:
            exitError("Could not rename script file '{}' to '{}'\n{}".format(filePath, backupFile, e))
        print "Original script file '{}' backed up as '{}'".format(filePath, backupFile)
        originalFile = backupFile                                   # inputscript.bak
        writeFile    = filePath                                     # inputscript.py
    debug("originalFile = {}".format(originalFile))
    debug("writeFile = {}".format(writeFile))

    # Overwrite original file now
    libFilesUpdatedList = []
    commentLinesList = []
    emptyLines = 0
    libFileReplaceFlag = libFileJustSetFlag = False
    with open(originalFile, 'r') as f, open(writeFile, 'w') as n:
        for line in f:
            libFile = RegexLibFile.match(line)
            if libFile:
                #debug("LIBR: {}".format(line))
                fileKey = libFile.group(1)
                if libFile.group(2) < funcDict[fileKey]['version']:
                    debug("Replacing: {}".format(fileKey))
                    libFilesUpdatedList.append(fileKey)
                    libFileReplaceFlag = libFileJustSetFlag = True
                    commentLinesList = []
                    libPath = funcPath + fileKey
                    with open(libPath, 'r') as l:
                        lib = l.read()
                    n.write(lib)
                else:
                    commentLinesList.append(line)
                continue
            if re.match(r'#', line):
                #debug("BANN: {}".format(line))
                if libFileJustSetFlag: # Banner lines immediately following the RegexLibFile match
                    libFileJustSetFlag = False
                else:
                    libFileReplaceFlag = False
                    while emptyLines > 0:
                        debug("Write empty line")
                        n.write("\n")
                        emptyLines -= 1
                    commentLinesList.append(line)
                continue
            if RegexMain.match(line):
                #debug("MAIN: {}".format(line))
                break
            if libFileReplaceFlag:
                if re.match(r'^\s*$', line):
                    emptyLines += 1
                else:
                    emptyLines = 0
            else:
                while commentLinesList:
                    n.write(commentLinesList.pop(0))
                n.write(line)
        while commentLinesList:
            n.write(commentLinesList.pop(0))

    print "Updated script file '{}' with latest library functions: {}".format(writeFile, libFilesUpdatedList)


#
# Main:
#
def main():

    global Debug, Sanity

    # Get arguments if any
    args = getUserParams()
    if args.debug:
        Debug = True
        print "Debug flag true"
    if args.sanity:
        Sanity = True
        print "Sanity flag true"
    if not args.filename: # We glob *.py
        fileList = glob.glob("*.py")
        if not fileList:
            exitError("No files matchnig glow '{}'".format(args.filename))
    else:
        fileList = [args.filename]

    # Read latest library function versions
    funcDict = getLatestFuncVersions(FuncPath)

    # Read input script(s) function versions
    scriptDict = {}
    for scriptFile in fileList:
        filename = os.path.basename(scriptFile)
        scriptDict[os.path.basename(scriptFile)] = getScriptVersions(scriptFile)

    print "\n\n===\n\n"

    # Print matrix comparison of function versions
    canUpdateFileList = []
    cannotUpdateFileList = []
    uptoDateFileList = []
    for scriptFile in fileList:
        filename = os.path.basename(scriptFile)
        newerVersionsExist, canUpdateFlag = checkVersionMatrix(funcDict, filename, scriptDict[filename])
        if newerVersionsExist and canUpdateFlag:
            canUpdateFileList.append(scriptFile)
        elif not canUpdateFlag:
            cannotUpdateFileList.append(scriptFile)
        elif not newerVersionsExist:
            uptoDateFileList.append(scriptFile)

    if uptoDateFileList or canUpdateFileList or cannotUpdateFileList:
        print "===\n"
    if uptoDateFileList:
        print "Script files up to date: {}".format(uptoDateFileList)
    if canUpdateFileList:
        print "Script files which can be updated now: {}".format(canUpdateFileList)
    if cannotUpdateFileList:
        print "Script files with issues which cannot be updated: {}".format(cannotUpdateFileList)
    if not canUpdateFileList:
        sys.exit(0)

    # Ask to update
    print
    answer = raw_input("Update scripts files which can be updated ? (y/n): ")
    if not answer.lower() == "y": 
        sys.exit(0)
    print

    # Update script(s)
    for scriptFile in canUpdateFileList:
        updateScript(FuncPath, funcDict, scriptFile)

main()
