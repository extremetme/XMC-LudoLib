#
# Lock functions (based on Markus Nikulski's shareData() function)
# lock.py v7
#
import os
import time
import uuid
import glob
import json
import random
PauseSleep = 0.1
LockRootDir = "/dev/shm/"
LockContextDir = None
#/dev/shm/<context>/			# Context directory
#/dev/shm/<context>/lock/		# Lock directory
#/dev/shm/<context>/lockTime		# File containing lock time
#/dev/shm/<context>/queueing.<uuid4>	# Queue file

def exitLockError(errorOutput, sleep=ExitErrorSleep): # v1 - Same as exitError() but releases active lock
    global LockContextDir
    if LockContextDir:
        yieldLock()
    exitError(errorOutput, sleep)

def returnContextDir(workflow, activity, script, execid, username, custom): # v1 - returns the context directory to use
    context = ''
    if username:
        context += '.' + emc_vars["userName"].replace('.', '_').replace('@', '_')
    if workflow: # Will only work with workflows
        context += '.' + emc_vars['workflowPath'].replace('/','_')
    if execid: # Will only work with workflows
        context += '.' + emc_vars['workflowExecutionId']
    if script: # Will only work with scripts
        context += '.' + emc_vars['javax.script.filename']
    if activity: # Will only work with scripts
        context += '.' + emc_vars['activityName'].replace("\n", '')
    if custom: # Custom name
        context += '.' + custom
    if context:
        context = context.replace(' ','_')
    else:
        context = 'global'
    return LockRootDir + context

def acquireLock(workflow=False, activity=False, script=False, execid=False, username=False, custom=None, lockTime=60, timeout=120): # v7 - Acquire lock on custom context
    global LockContextDir
    if LockContextDir:
        exitLockError("acquireLock() called but a lock is already acquired")
    if timeout < lockTime: # Timeout is absolute; it does not re-arm itself when lock ownership changes and this task is still waiting
        exitError("acquireLock() timeout = {} must be larger than lockTime = {}".format(timeout, lockTime))
    print "\nLOCK requested at {}\n".format(time.ctime())
    contextDir = returnContextDir(workflow, activity, script, execid, username, custom)
    debug("acquireLock() contextDir = {}".format(contextDir))
    lockDir = contextDir + "/lock"
    debug("acquireLock() lockDir = {}".format(lockDir))
    lockTimeFile = contextDir + "/lockTime"
    debug("acquireLock() lockTimeFile = {}".format(lockTimeFile))

    try: # Create the context directory
        os.mkdir(contextDir)
        debug("acquireLock() created contextDir {}".format(contextDir))
    except: # it already exists
        debug("acquireLock() contextDir {} already exists".format(contextDir))

    # Loop until we get the lock or timeout
    lockStamp = queueFile = None
    lockObtained = timedOut = sleepMsg = False
    while not (lockObtained or timedOut):
        try: # and acquire lock (smaphore)
            time.sleep(random.randint(0,100)/10000.0) # Random millisec sleep, so if many tasks queuing, they don't all try at exact same time..
            os.mkdir(lockDir)
            # The time between creating the lock directory and creating the lock time file is the yield time
            with open(lockTimeFile, 'w') as f: # Stake a claim to the duration of our lock reservation
                f.write(str(lockTime))
            debug("acquireLock() lock obtained & reserved for {} secs".format(lockTime))
            print "\nLOCK acquired at {}\n".format(time.ctime())
            LockContextDir = contextDir
            lockObtained = True
        except: # lock is already taken...
            try:
                timestamp = os.path.getmtime(lockDir) # Get time of existing lock
            except:
                timestamp = startTime = None # Can happen if lockDir just got deleted; need to fall through to sleep and loop again
            if not queueFile: # Create queuing file
                queueFile = contextDir + "/queueing." + str(uuid.uuid4())
                try:
                    with open(queueFile, 'a'):
                        os.utime(queueFile, None)
                        debug("acquireLock() set queuing file {}".format(queueFile))
                except:
                    debug("acquireLock() unable to set queuing file {}".format(queueFile))
                    queueFile = None
            if timestamp and timestamp != lockStamp:
                startTime = time.time() # This will restart the timeout upon every new lock reservation
                lockStamp = timestamp
                sleepMsg = True
                debug("acquireLock() timestamp of existing lock = {}".format(lockStamp))
                try: # Read reserved lock time
                    with open(lockTimeFile, 'r') as f:
                        reservedLockTime = int(f.readline())
                        debug("acquireLock() reserved lock duration = {}".format(reservedLockTime))
                except: # Or if can't be read go fo 0
                    reservedLockTime = 0
                    debug("acquireLock() unable to read reserved lock duration")
            if lockStamp and time.time() > lockStamp + reservedLockTime: # Lock time expired reservation
                os.rmdir(lockDir) # We bump it
                debug("acquireLock() deleting existing expired lock")
                continue # and try again
            else: # Lock time has not yet expired reservation; honour it and keep trying until success or timeout
                if startTime and time.time() - startTime + PauseSleep > timeout:
                    debug("acquireLock() timed out, aborting")
                    print "\nLOCK timed-out at {}\n".format(time.ctime())
                    timedOut = True
                else:
                    if sleepMsg:
                        debug("acquireLock() sleeping to wait for lock release or timeout")
                        sleepMsg = False
                    time.sleep(PauseSleep + random.randint(0,100)/10000.0) # Randomaized sleep timer

    if queueFile: # Delete queuing file
        os.remove(queueFile)
    return True if lockObtained else False

def yieldLock(): # v4 - Yield existing lock
    global LockContextDir
    if not LockContextDir:
        exitError("yieldLock() cannot be called before acquireLock()")
    contextDir = LockContextDir
    debug("yieldLock() contextDir = {}".format(contextDir))
    lockDir = contextDir + "/lock"
    debug("yieldLock() lockDir = {}".format(lockDir))
    lockTimeFile = contextDir + "/lockTime"
    debug("yieldLock() lockTimeFile = {}".format(lockTimeFile))

    try:
        os.rmdir(lockDir)
        debug("yieldLock() deleted lockDir {}".format(lockDir))
        print "\nLOCK released at {}\n".format(time.ctime())
    except:
        debug("yieldLock() could not delete lockDir {}".format(lockDir))
        print "\nTried & failed to release LOCK... at {}\n".format(time.ctime())
    try:
        os.remove(lockTimeFile)
        debug("yieldLock() deleted lockTimeFile {}".format(lockTimeFile))
    except:
        debug("yieldLock() could not delete lockTimeFile {}".format(lockTimeFile))

    LockContextDir = None

def lockQueue(): # v3 - Check if there is a queue for the lock
    if not LockContextDir:
        exitError("lockQueue() cannot be called without holding the lock")
    contextDir = LockContextDir
    debug("lockQueue() contextDir = {}".format(contextDir))
    queueFileGlob = contextDir + "/queueing.*"
    debug("lockQueue() queueFileGlob = {}".format(queueFileGlob))

    # Returns length of queue waiting to acquire samew lock; 0 = no queue
    lockQueueLength = len(glob.glob(queueFileGlob))
    print "\nLOCK queue length = {} at {}\n".format(lockQueueLength, time.ctime())
    return lockQueueLength

def shareData(context, newData=None, purge=False): # v1 - Allows to read, store or flush data into provided context file in lock directory
    # Examples:
    # data = shareData(context)                                   # Shared data is returned
    # None = shareData(context, purge=True)                       # Shared data is flushed, returs None
    # mergedData = shareData(context, newData=data)               # New data is merged with existing data, which is written and returned
    # sameData = shareData(context, newData=sameData, purge=True) # Existing data is flushed, new data is written and returned

    if not LockContextDir:
        exitError("shareData() cannot be called without holding the lock")
    contextDir = LockContextDir
    shareFile = contextDir + "/{}.json".format(context)
    debug("shareData() shareFile = {}".format(shareFile))

    # Read existing data, or flush existing data
    shareData = None # Assume we have nothing to start with
    if os.path.exists(shareFile):
        if purge: # Delete it & and hence don't read it
            os.remove(shareFile)
        else: # Read data from it
            try:
                with open(shareFile, 'r') as f:
                    shareData = json.load(f)
                print "\nLOCK shareData read for context {}\n".format(context)
            except:
                exitLockError("Unable to read lock shareData() file {}; JSON expected".format(shareFile))

    # Write new data
    if newData:
        if shareData: # We have to merge the new data with the existing one
            if isinstance(shareData, dict) and isinstance(newData, dict):
                # Merge two Dicts
                shareData = {key: value for d in (shareData, newData) for key, value in d.items()}
            elif isinstance(shareData, list) and isinstance(newData, list):
                # Append newData to shareData list
                shareData.extend(newData)
            else:
                exitLockError("Cannot merge existing shared data '' with new data '' as different types".format(type(shareData), type(newData)))
        else: # No merge, just write fresh data
            shareData = newData
        # Now write to shared file
        try:
            with open(shareFile, 'w') as f:
                json.dump(shareData, f)
        except:
            exitLockError("Unable to write lock shareData() file {}".format(shareFile))
        print "\nLOCK shareData written for context {}\n".format(context)

    return shareData

def readDataNoLock(context, workflow=False, activity=False, script=False, execid=False, username=False, custom=None): # v1 - Allows to read data without a lock
    # Holding a lock when reading data is only necessary to avoid reading while someone else is writing the data
    # But if there is no chance of a write happening, then no need for tasks to grab a lock to read
    contextDir = returnContextDir(workflow, activity, script, execid, username, custom)
    shareFile = contextDir + "/{}.json".format(context)
    debug("readDataNoLock() shareFile = {}".format(shareFile))

    # Read existing data
    shareData = None # Assume we have nothing to start with
    if os.path.exists(shareFile):
        try:
            with open(shareFile, 'r') as f:
                shareData = json.load(f)
            print "\nNo LOCK shareData read for context {}\n".format(context)
        except:
            exitLockError("Unable to read lock shareData() file {}; JSON expected".format(shareFile))
    return shareData
