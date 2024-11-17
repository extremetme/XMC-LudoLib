#
# Linux shell functions (requires cli.py)
# shell.py v3
#
import re
import os
import subprocess

def xmcLinuxExecute(cmd): # v1 - Execute a command on XMC for which no output expected
    debug("xmcLinuxExecute about to execute : {}".format(cmd))
    try:
        os.system(cmd)
        return True
    except Exception as e: # Expect OSError
        print "{}: {}".format(type(e).__name__, str(e))
        print "Error executing '{}' on XMC shell".format(cmd)
        return False

def xmcLinuxCommand(cmdRegexStr, debugKey=None): # v2 - Execute a command on XMC and recover the output
    mode, cmdList, regex = parseRegexInput(cmdRegexStr)
    cmd = cmdList[0] # We only support single shell command syntax for now
    cmdList = cmd.split(' ')
    try:
        emc_vars
    except: # If not running on XMC Jython...I develop on my Windows laptop...
        cmdList[0] += '.bat'
    debug("xmcLinuxCommand about to execute : {}".format(cmd))
    try:
        outputStr = subprocess.check_output(cmdList)
    except Exception as e: # Expect OSError
        print "{}: {}".format(type(e).__name__, str(e))
        print "Error executing '{}' on XMC shell".format(cmd)
        return
    data = re.findall(regex, outputStr, re.MULTILINE)
    # Format we return data in depends on what '<type>://' was pre-pended to the cmd & regex
    value = formatOutputData(data, mode)
    if Debug:
        if debugKey: debug("{} = {}".format(debugKey, value))
        else: debug("xmcLinuxCommand OUT = {}".format(value))
    return value
