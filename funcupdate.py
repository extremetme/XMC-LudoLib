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
import shutil
import argparse

#
# Variables:
#
Debug = False    # Enables debug messages
Sanity = False   # If enabled, config commands are not sent to host (show commands are operational)
FuncPath = "C:/Users/lstevens/Scripts/X-Python/XMC/functions" # Path of latest library files
ScriptVersionsFolder = "./versions"
RegexScriptVersion = re.compile("__version__ *= *'(\d+\.\d+)'")
RegexLibFile = re.compile('# (\w+\.py)(?: +v(\d+))?')
RegexFunction = re.compile('def (\w+)\(.*?\): +# +v(\d+)')
RegexBanner = re.compile('# \w+')
RegexMain = re.compile('(?:def main\(\):|# Main:|# INIT:|# Variables:)')
BannerLength = 100


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
    print "=" * BannerLength
    for fileKey in sorted(funcDict.keys()):
        print "{:34} version {:>4}".format(fileKey, funcDict[fileKey]['version'])
        for function in sorted(funcDict[fileKey]['functions'].keys()):
            print "    {:30} version {:>4}".format(function + "()", funcDict[fileKey]['functions'][function])
        print
    return funcDict


def getScriptVersions(filePath): # Read input script function versions
    scriptDict = {
        'version': None,
        'libfiles': {
#           <libfile.py>: {
#               version: <version>,
#               functions: {
#                   <func1>: <version>,
#                   <func2>: <version>,
#               }
#           }
        }
    }
    with open(filePath, 'r') as f:
        fileKey = 'orphan'
        libFileFlag = False
        for line in f:
            scriptVersion = RegexScriptVersion.match(line)
            if scriptVersion:
                scriptDict['version'] = scriptVersion.group(1)
                continue
            libFile = RegexLibFile.match(line)
            if libFile:
                #debug("LIBR: {}".format(line))
                fileKey = libFile.group(1)
                scriptDict['libfiles'][fileKey] = {'version': libFile.group(2), 'functions': {}}
                libFileFlag = True
                continue
            if not libFileFlag and RegexBanner.match(line):
                #debug("BANN: {}".format(line))
                fileKey = 'orphan'
                continue
            if RegexMain.match(line):
                #debug("MAIN: {}".format(line))
                break
            function = RegexFunction.match(line)
            if function:
                if fileKey == 'orphan' and fileKey not in scriptDict['libfiles']:
                    scriptDict['libfiles'][fileKey] = {'version': None, 'functions': {}}
                scriptDict['libfiles'][fileKey]['functions'][function.group(1)] = function.group(2)
                libFileFlag = False

    print "\nLibfiles and function versions used by script '{}' version {}".format(os.path.basename(filePath), scriptDict['version'])
    print "=" * BannerLength
    for fileKey in sorted(scriptDict['libfiles'].keys()):
        print "{:34} version {:>4}".format(fileKey, scriptDict['libfiles'][fileKey]['version'])
        for function in sorted(scriptDict['libfiles'][fileKey]['functions'].keys()):
            print "    {:30} version {:>4}".format(function + "()", scriptDict['libfiles'][fileKey]['functions'][function])
        print
    return scriptDict


def checkVersionMatrix(funcDict, filename, scriptDict): # Print matrix comparison of function versions
    newerVersionsExist = False
    canUpdateFlag = True
    print "\nMatrix of libfiles and function versions used by script '{}' version {}".format(os.path.basename(filename), scriptDict['version'])
    print "=" * BannerLength
    for fileKey in sorted(scriptDict['libfiles'].keys()):
        line = "{:34} version {:>4}".format(fileKey, scriptDict['libfiles'][fileKey]['version'])
        if scriptDict['libfiles'][fileKey]['version']:
            line += " - "
            if fileKey in funcDict:
                if scriptDict['libfiles'][fileKey]['version'] == funcDict[fileKey]['version']:
                    line += "is latest"
                elif int(scriptDict['libfiles'][fileKey]['version']) < int(funcDict[fileKey]['version']):
                    line += "latest is v{:4}".format(funcDict[fileKey]['version'])
                    newerVersionsExist = True
                else:
                    line += "newer than master!! v{:4}".format(funcDict[fileKey]['version'])
                    canUpdateFlag = False
            else:
                line += "libfile not found"
                canUpdateFlag = False
        print line
        for function in sorted(scriptDict['libfiles'][fileKey]['functions'].keys()):
            line = "    {:30} version {:>4} - ".format(function + "()", scriptDict['libfiles'][fileKey]['functions'][function])
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
                if scriptDict['libfiles'][fileKey]['functions'][function] == funcDict[funcKey]['functions'][function]:
                    line += "is latest      "
                elif int(scriptDict['libfiles'][fileKey]['functions'][function]) < int(funcDict[funcKey]['functions'][function]):
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


def incrementVersion(version): # Increments script version by 0.01; assumes versions in formay y.xx
    major, minor = [int(v) for v in version.split('.', 1)]
    minor += 1
    if minor > 99: # Roll over major..
        major += 1
        minor = 0
    return "{}.{:02}".format(major, minor)


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
    miscPyFuncUpdatedList = []
    cachedLinesList = []
    cachedLinesFlag = False
    originalScriptVersion = newScriptVersion = None
    emptyLines = 0
    replaceFlag = libFileJustSetFlag = miscLibFileProcessFlag = False
    with open(originalFile, 'r') as f, open(writeFile, 'w') as n:
        for line in f:
            if not originalScriptVersion:
                scriptVersion = RegexScriptVersion.match(line)
                if scriptVersion:
                    originalScriptVersion = scriptVersion.group(1)
                    newScriptVersion = incrementVersion(originalScriptVersion)
                    line = re.sub(r'(\d+\.\d+)', newScriptVersion, line)
                    debug("Script version increased from {} to {}".format(originalScriptVersion, newScriptVersion))
            libFile = RegexLibFile.match(line)
            if miscLibFileProcessFlag:
                function = RegexFunction.match(line)
            if libFile:
                replaceFlag = False
                fileKey = libFile.group(1)
                debug("LIBFILE {} : {}".format(fileKey, line.rstrip()))
                if fileKey == "misc.py":
                    miscLibFileProcessFlag = True
                elif libFile.group(2) and int(libFile.group(2)) < int(funcDict[fileKey]['version']):
                    # If we have a libFile version and the version is old, then we replace libFile
                    # Misc.pl will always be skipped as it has no version
                    debug("*** Replacing: {}".format(fileKey))
                    libFilesUpdatedList.append(fileKey)
                    replaceFlag = libFileJustSetFlag = True
                    miscLibFileProcessFlag = False

                    # Restore empty lines only
                    if cachedLinesList:
                        debug("lib printing empty cachedLinesList lines: {}".format(",".join([x.rstrip() for x in cachedLinesList if not re.match(r'\s*$', x)])))
                    while cachedLinesList:
                        cachedLine = cachedLinesList.pop(0)
                        if not re.match(r'\s*$', cachedLine):
                            break
                        n.write(cachedLine)
                    cachedLinesList = []
                    cachedLinesFlag = False

                    # Open libFile, fully read it, and fully write it
                    libPath = funcPath + fileKey
                    with open(libPath, 'r') as l:
                        lib = l.read()
                    n.write(lib)
                    continue
                else: # If we don't need to replace the libFile, we store these initial comment lines
                    miscLibFileProcessFlag = False

            elif miscLibFileProcessFlag and function: # Parsing of misc.py individual functions
                funcName = function.group(1)
                debug("MISC.PY FUNCTION : {}".format(funcName))
                if int(function.group(2)) < int(funcDict[fileKey]['functions'][funcName]):
                    # If we have a function which is old, then we replace the function
                    debug("*** Replacing misc.py function: {}".format(funcName))
                    miscPyFuncUpdatedList.append(funcName)
                    replaceFlag = True

                    # Restore empty lines only
                    if cachedLinesList:
                        debug("misc printing empty cachedLinesList lines: {}".format(",".join([x.rstrip() for x in cachedLinesList if not re.match(r'\s*$', x)])))
                    while cachedLinesList:
                        cachedLine = cachedLinesList.pop(0)
                        if not re.match(r'\s*$', cachedLine):
                            break
                        n.write(cachedLine)
                    cachedLinesList = []
                    cachedLinesFlag = False

                    # Open misc.py libFile, fully read it, and fully write it
                    libPath = funcPath + "misc.py"
                    writeFuncFlag = False
                    emptyLineList = []
                    with open(libPath, 'r') as l:
                        for mLine in l:
                            mFunction = RegexFunction.match(mLine)
                            if mFunction:
                                if mFunction.group(1) == funcName: # We got to the function we need to replace
                                    n.write(mLine)
                                    writeFuncFlag = True
                                else: # A different function, we skip and stop replacing if we were
                                    writeFuncFlag = False
                            elif re.match(r'import ', mLine): # Some functions are preceded by import statements..
                                writeFuncFlag = False
                            elif writeFuncFlag:
                                if re.match(r'\s*$', mLine):
                                    emptyLineList.append(mLine)
                                else:
                                    while emptyLineList:
                                        n.write(emptyLineList.pop(0))
                                    n.write(mLine)
                    continue
                else: # If we don't need to replace the misc.py function
                    replaceFlag = False

            elif RegexMain.match(line):
                # Restore any commented line we pushed on stack
                if cachedLinesList:
                    debug("main printing cachedLinesList: {}".format(",".join([x.rstrip() for x in cachedLinesList])))
                while cachedLinesList:
                    n.write(cachedLinesList.pop(0))
                cachedLinesFlag = False
                debug("MAIN: {}".format(line))
                replaceFlag = False

            elif re.match(r'#\s*$', line) and libFileJustSetFlag: # Empty banner line immediately following the RegexLibFile match
                debug("BANN Skip: {}".format(line.rstrip()))
                libFileJustSetFlag = False # and we skip it..
                continue

            elif re.match(r'#', line) or (replaceFlag and re.match(r'\s*$', line)): # Comment line (always) or empty line (only when replacing)
                # Could be end of lib section, maybe not.. so we cache these lines
                if line.rstrip():
                    if emptyLines:
                        debug("Cache {} empty lines".format(emptyLines))
                        emptyLines = 0
                    debug("BANN cache line: {}".format(line.rstrip()))
                    cachedLinesFlag = True
                else:
                    emptyLines += 1
                cachedLinesList.append(line)
                continue

            if replaceFlag:
                if cachedLinesFlag:
                    debug("Flushing BANN/Empty cached lines")
                cachedLinesList = [] # Flush any cached lines
                cachedLinesFlag = False

            else: # Preserve lines, only if not replacing them
                # Restore any commented line we pushed on stack
                if cachedLinesList:
                    debug("no replace, printing cachedLinesList: {}".format(",".join([x.rstrip() for x in cachedLinesList])))
                while cachedLinesList:
                    n.write(cachedLinesList.pop(0))
                cachedLinesFlag = False
                # And write over the line at hand
                n.write(line)

        # Restore any commented line we pushed on stack
        if cachedLinesList:
            debug("exit printing cachedLinesList: {}".format(",".join([x.rstrip() for x in cachedLinesList])))
        while cachedLinesList:
            n.write(cachedLinesList.pop(0))

    if replaceFlag:
        print "\nERROR: Reached end of file and replaceFlag was still true; '{}' is corrupted!!\n".format(writeFile)
        return

    if not Sanity and originalScriptVersion:
        # Create versions directory if non existent
        if not os.path.exists(ScriptVersionsFolder):
            try:
                os.makedirs(ScriptVersionsFolder)
                print "Created script versions directory '{}'".format(ScriptVersionsFolder)
            except Exception as e:
                print "ERROR! Could not create script versions directory '{}'\n{}".format(ScriptVersionsFolder, e)

        # Copy .bak file to version storage folder
        backupOldVersionFile = re.sub(r'\.bak', '_{}.bak'.format(originalScriptVersion), originalFile) # inputscript_<oldVer>.py
        verBackupFile = "{}/{}".format(ScriptVersionsFolder,backupOldVersionFile)
        if os.path.exists(verBackupFile):
            print "ERROR! There is already a version '{}' backup file: '{}'".format(originalScriptVersion, verBackupFile)
        else:
            try:
                shutil.copyfile(originalFile, verBackupFile)
                print "Made version {} backup of original script: '{}'".format(originalScriptVersion, verBackupFile)
            except Exception as e:
                print "ERROR! Could make version {} backup of original scrip\n{}".format(originalScriptVersion, e)

    print "Updated script file '{}' with latest library functions: {}".format(writeFile, libFilesUpdatedList)
    if miscPyFuncUpdatedList:
        print "Updated script file '{}' with latest misc.py functions: {}".format(writeFile, miscPyFuncUpdatedList)
    if newScriptVersion:
        print "Updated script file '{}' now has version {}".format(writeFile, newScriptVersion)


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
