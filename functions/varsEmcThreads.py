#
# XMC Emc threads vars
# varsEmcThreads.py v4
#

#
# IMPORTS:
#
import os
import sys
import time
import glob
import json

#
# VARIABLES:
#
StartTime = time.time()
TimeDeviation = 5.0 # When XMC runs many instances of same script, not all instances will start at exactly the same time; set this to worst case deviation in secs
DelayStaleDelete = 1.0 # If stale files exists, all threads will be made to wait this minimum delay, before the ThreadMaster is allowed to delete the stale files 
Timeout = 10   # Seconds we are ready to wait for reading emc_vars from other threads
SleepTimer = 1 # While waiting for other threads to make their emc_vars avail, this is the sleep timer in the timeout loop
SeqNumber = 0
ThreadMaster = None
ThreadIPs = []
ThreadVarsDict = {}
ReturnOnError = False # When reading data from other threads, determines whether we want to bomb out if some threads don't respond or continue with threads which do
Emc_vars_copy = emc_vars.copy() # Modifying emc_vars is discouraged, so we take a copy of it; shallow copy is enough, emc_vars is single level dict 
if 'activityCustomId' in emc_vars: # Workflow
    ThisScript = emc_vars['activityCustomId'].split(os.path.sep)[-1].split('.')[0]  # Name of workflow activity
else: # Script
    ThisScript = __file__.split(os.path.sep)[-1].split('.')[0]  # Name of our script
try:
    WorkDir = '/dev/shm'
    os.chdir(WorkDir)
except: # If not running on XMC Jython...I develop on my Windows laptop...
    WorkDir = os.getcwd()
UserName = emc_vars["userName"].replace('.', '_').replace('@', '_')
MyIP = emc_vars["deviceIP"]
RegexFileIP = re.compile('^\.[^\.]+\.[^\.]+\.([\d_]+)\.')
GlobStamps = '.' + UserName + '.' + ThisScript + '.*.stamp'
GlobSeqnce = '.' + UserName + '.' + ThisScript + '.' + MyIP.replace('.', '_') + '.[0-9]*'
GlobSqJson = '.' + UserName + '.' + ThisScript + '.*.<SEQ>.json'
# The following files are written to the XMC filesystem (default path: /usr/local/Extreme_Networks/NetSight/wildfly/bin)
# - Stamp file:    .<UserName>.<ThisScript>.<IP>.stamp        : modify time of this empty file used to track other threads
# - Sequence file: .<UserName>.<ThisScript>.<IP>.<seqNb>      : empty file who's sequence number determines which json file to load
# - JSON file:     .<UserName>.<ThisScript>.<IP>.<seqNb>.json : json file containing IP's Emc_vars_copy


#
# FUNCTIONS:
#
def threadFile(ip, seqnum=None, suffix=None): # v1 - Given IP and suffix, returns the script instance specific filenames
    fileName = '.' + UserName + '.' + ThisScript + '.' + ip.replace('.', '_')
    if seqnum != None:
        fileName += '.' + str(seqnum)
    if suffix:
        fileName += '.' + suffix
    return fileName

def threadIP(filename): # v1 - Given a thread filename, returns the thread IP
    ipMatch = RegexFileIP.match(filename)
    if not ipMatch:
        exitError("Unable to extract IP from thread filename '{}'".format(filename))
    ip = ipMatch.group(1)
    return ip.replace('_', '.')

def deleteFiles(globStr): # v1 - Deletes all existing sequence files for this thread
    fileList = glob.glob(globStr)
    if fileList:
        debug("Threads - deleteFiles() deleting files : {}".format(fileList))
        for f in fileList:
            os.remove(f)

def touch(path): # v2 - Touches a file (and sets its modify time)
    try:
        with open(path, 'a'):
            os.utime(path, None)
            debug("Threads - touch() file : {}".format(path))
    except Exception as e: # Expect IOError
        printLog("{}: {}".format(type(e).__name__, str(e)))
        exitError("Unable to touch file '{}'".format(path))

def writeJson(dataDict, path): # v2 - Writes a dict to json file
    try: # Python file locking https://yakking.branchable.com/posts/flocking/
        with open(path, 'w') as f:
            json.dump(dataDict, fp=f, indent=4)
            debug("Threads - writeJson() file : {}".format(path))
    except Exception as e: # Expect IOError
        printLog("{}: {}".format(type(e).__name__, str(e)))
        exitError("Unable to write to json file '{}'".format(path))

def emc_threads(returnOnError=None): # v1 - Returns list of IPs for other instances simultaneously running this same script
    global ThreadIPs
    global ReturnOnError

    if ThreadIPs: # We only need to call this function once; if it has already run, simply come out
        return ThreadIPs

    def electMaster(iplist, myip): # Given a list of IPs, returns true if myip is the numerically lowest in the list
        myipInt = ipToNumber(myip)
        for ip in iplist:
            if ipToNumber(ip) < myipInt:
                return False
        return True

    if returnOnError != None: # If returnOnError was set to True/False, then we change the global ReturnOnError
        ReturnOnError = returnOnError

    waitTime = StartTime - time.time() + TimeDeviation
    if waitTime > 0:
        debug("Threads - emc_threads() allowing for deviation of start time between threads / sleep = {}".format(waitTime))
        time.sleep(waitTime)

    # Get a list of all Stamp files for this script
    stampFileList = glob.glob(GlobStamps)
    # - there is a chance that ThreadMaster instance actually deletes some of files in stampFileList, while this instance is on the line below
    # - and we would error on doing os.path.getmtime(x) on a since non-existent file...
    # - the solution is the code added in the ThreadMaster if section below, where a delay is added to compensate between time of this thread and slowest thread
    activeStampFiles = [x for x in stampFileList if os.path.getmtime(x) >= (StartTime - TimeDeviation)]
    staleStampFiles  = [x for x in stampFileList if x not in activeStampFiles]
    if staleStampFiles:
        debug("Threads - staleStampFiles:\n{}".format(staleStampFiles))

    # Only retain IPs for Stamp files newer than StartTime
    ThreadIPs = [threadIP(x) for x in activeStampFiles]
    debug("Threads - active device IPs = {}".format(ThreadIPs))

    # Write JSON and sequence number file
    if SeqNumber == 0: # Only do this if emc_threads_put() has not already been called
        writeJson(Emc_vars_copy, threadFile(MyIP, seqnum=SeqNumber, suffix='json'))
        touch(threadFile(MyIP, seqnum=SeqNumber))

    if staleStampFiles: # The master thread will take charge of cleanup of stale thread files of this same script (these could be stale from previous runs)
        # But we let all threads do the wait below, to keep them in sync as much as possible
        debug("Threads - stale files exist; electing ThreadMaster")
        staleStampStart = time.time()
        # Elect a ThreadMaster; we want only one script instance to perform cleanup of stale files
        ThreadMaster = electMaster(ThreadIPs, MyIP)
        # Before deleting any files we need to make sure that all other active threads have passed this function
        # Identify the active thread with the highest time stamp (= slowest thread)
        slowestStamp = 0
        for stampFile in activeStampFiles:
            stamp = os.path.getmtime(stampFile)
            if stamp > slowestStamp:
                slowestStamp = stamp
        debug("Threads - slowest thread timestamp = {}".format(slowestStamp))
        # Take the delta of that highest time and our initial timestamp (and adjust for processing to get here)
        waitTime = slowestStamp - int(StartTime) - (time.time() - staleStampStart) + DelayStaleDelete
        if waitTime > 0:
            debug("Threads - emc_threads() allowing for delta between this thread and slowest thread / sleep = {}".format(waitTime))
            time.sleep(waitTime)

        if ThreadMaster: # The master thread will take charge of cleanup of stale thread files of this same script (these could be stale from previous runs)
            debug("Threads - acting as ThreadMaster and deleting stale files;")
            # By now, all other threads will have come out of emc_threads(), so is safe to perform clean up of stale files
            for fnam in staleStampFiles:
                fglob = re.sub(r'[^\.]+$', '*', fnam) # This glob will catch all 3 file types
                debug("** Deleting all files for glob = {}".format(fglob))
                for fdel in glob.glob(fglob):
                    debug("-> deleting file = {}".format(fdel))
                    os.remove(fdel)
    return ThreadIPs

def emc_threads_vars(ip=None, var=None, returnOnError=None): # v2 - Returns variable dict from other instances simultaneously running this same script
    # If both ip and var is set, returns value of variable
    # If only ip is set, returns dict of ip's Emc_vars_copy
    # If neither ip nor var is set, returns full dict where 1st key is thread ip and 2nd key are Emc_vars_copy keys
    # This method will also work if the local thread ip is provided, in which case the local ip Emc_vars_copy is returned
    # If returnOnError=False or returnOnError not set and global ReturnOnError is False:
    #     This method expects to obtain Emc_vars_copy from all running instances for which Stamp files were recorded
    #     Failure to read the JSON file of one or more other instances will result in an exception being raised
    #     This can happen if some script instances fail after starting; the outcome is that all instances will then fail
    # If returnOnError=True or returnOnError not set and global ReturnOnError is True:
    #     In this case, failure to read the JSON file of one or more other instances will not result in an exception
    #     The method will instead return, but the variables requested may or may not be available.
    #     If the ip provided is for an instance for which the Emc_vars_copy could not be read, then the method will return
    #     None if a var was requested and an empty dict otherwise.
    #     If the method is called without any ip or var set, then a dict is returned, but this dict will have some IP keys
    #     holding an empty dict
    global ThreadIPs
    global ThreadVarsDict

    if returnOnError == None: # Unless override provided in method call, use global setting
        returnOnError = ReturnOnError

    if not ThreadIPs: # emc_threads() has not been called
        emc_threads() # global ThreadIPs gets set

    if not ThreadVarsDict: # dict is not populated
        # Set our own Emc_vars_copy
        ThreadVarsDict[MyIP] = Emc_vars_copy

        timeoutTime = time.time() + Timeout # Prime the timeout time, in case we have to timeout
        failedFirstRead = {}                # Init dict to track failed file read

        while set(ThreadIPs) != set(ThreadVarsDict.keys()): # Until we have variables for all IPs
            # Check for available json files
            jsonFileList = glob.glob(GlobSqJson.replace('<SEQ>', str(SeqNumber)))
            jsonIPList = [threadIP(x) for x in jsonFileList]
            debug("Threads - available JSON files on SeqN {} = {}".format(SeqNumber, jsonIPList))
            newIPList = [x for x in jsonIPList if x in ThreadIPs and x not in ThreadVarsDict]

            if newIPList: # Read in available JSON files
                debug("Threads - new JSON files to read in for these IPs = {}".format(newIPList))
                for newip in newIPList:
                    try:
                        path = threadFile(newip, seqnum=SeqNumber, suffix='json')
                        with open(path, 'r') as f:
                            debug("-> reading file = {}".format(path))
                            ThreadVarsDict[newip] = json.load(fp=f)
                    except Exception as e: # Expect IOError or ValueError
                        printLog("{}: {}".format(type(e).__name__, str(e)))
                        if newip not in failedFirstRead: # We allow 1 retry
                            failedFirstRead[newip] = 1
                            printLog("Threads - WARNING: Unable to read Emc_vars_copy for IP instance {} on first try".format(newip))
                            time.sleep(1) # Delay 1 sec before retry
                            continue
                        if returnOnError:
                            printLog("Threads - WARNING: Unable to read Emc_vars_copy for IP instance {}".format(newip))
                            ThreadVarsDict[newip] = {}
                        else:
                            exitError("Unable to read to json file '{}'".format(path))
                # Reset timeout time (we only tick timeout time when we have no JSON to read)
                timeoutTime = time.time() + Timeout

            else: # No JSON files available; implement timeout
                if time.time() > timeoutTime: # We timeout
                    missingIPList = [x for x in ThreadIPs if x not in ThreadVarsDict]
                    if returnOnError:
                        printLog("Threads - WARNING: Unable to read Emc_vars_copy from these thread IPs: {}".format(missingIPList))
                        for failip in missingIPList:
                            ThreadVarsDict[failip] = {}
                    else:
                        exitError("Timing out due to inability to read Emc_vars_copy from these thread IPs: {}".format(missingIPList))
                time.sleep(SleepTimer)

    if ip and var: # Both are set
        if var in ThreadVarsDict[ip]:
            return ThreadVarsDict[ip][var]
        else: # Case where returnOnError is set and we are missing the Emc_vars_copy for this IP
            return None
    elif ip:
        return ThreadVarsDict[ip]
    else:
        return ThreadVarsDict

def emc_threads_put(**dict): # v1 - Set a local Emc_vars_copy variable and ensure this becomes available to other instances simultaneously running this same script
    global ThreadVarsDict
    global SeqNumber

    # As we are writing a new variable, every other instance of this script will too, so..
    ThreadVarsDict = {}         # Clear out the stored thread Emc_vars_copy
    SeqNumber += 1              # We increase the sequence number

    # Delete any existing sequence number files for this thread IP
    deleteFiles(GlobSeqnce)

    # Update the value in our local Emc_vars_copy
    for key, value in dict.items():
        Emc_vars_copy[key] = value

    # Re-write our thread json file
    writeJson(Emc_vars_copy, threadFile(MyIP, seqnum=SeqNumber, suffix='json'))

    # Re-post sequence number file
    touch(threadFile(MyIP, seqnum=SeqNumber))

#
# INIT: Init code for Threads; signal self thread existence and store Emc_vars_copy as json; we do this as early as possible
#
printLog("Threads - StartTime = {}".format(StartTime))
debug("Threads - ThisScript = {}".format(ThisScript))
debug("Threads - WorkDir = {}".format(WorkDir))
deleteFiles(GlobSeqnce)
touch(threadFile(MyIP, suffix='stamp'))

