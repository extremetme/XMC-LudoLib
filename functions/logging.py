#
# Logging functions (based on Markus Nikulski's setupLogger() function)
# logging.py v4
#
import os
import sys
import logging
import traceback
DebugLoggerRootDir = "/dev/shm/"

def setupDebugFileLogging(): # v4 - Debug logging to /dev/shm
    if not Debug: # Do nothing
        return
    global DebugLogger
    DebugLogger = logging.getLogger() 
    DebugLogger.setLevel(logging.DEBUG)

    # Add StdOut for INFO logging only
    stdout = logging.StreamHandler(stream=sys.stdout)
    stdout.setLevel(logging.INFO)
    stdoutFormatter = logging.Formatter('%(message)s')
    stdout.setFormatter(stdoutFormatter)
    DebugLogger.addHandler(stdout)

    # Add debug file for INFO & DEBUG
    logRDir = ".{}.{}".format(emc_vars['workflowPath'][1:].replace('/','_').replace(' ','-'), emc_vars['workflowExecutionId'])
    logPath = DebugLoggerRootDir + logRDir
    if not os.path.exists(logPath):
        os.makedirs(logPath)
    logPath += "/%s.log" % emc_vars['activityName'].replace(' ','-').replace("\n",'')
    printLog("Debug logging to file: {}".format(logPath))
    debugFile = logging.FileHandler(logPath,mode='a',encoding='utf-8')
    debugFile.setLevel(logging.DEBUG)
    debugFormatter = logging.Formatter('%(asctime)s %(levelname)-5s %(message)s')
    debugFile.setFormatter(debugFormatter)
    DebugLogger.addHandler(debugFile)
