#
# Lock functions (based on Markus Nikulski's shareData() function)
# lock.py v1
#
import os
import time
PauseSleep = 0.1
LockRootDir = "/dev/shm/"
LockContextDir = None
#/dev/shm/<context>/		# Context directory
#/dev/shm/<context>/lock/	# Lock directory
#/dev/shm/<context>/lockTime	# File containing lock time

def exitLockError(errorOutput, sleep=ExitErrorSleep): # v1 - Same as exitError() but releases active lock
    global LockContextDir
    if LockContextDir:
        yieldLock()
    exitError(errorOutput, sleep)

def acquireLock(workflow=False, activity=False, script=False, execid=False, username=False, lockTime=60, timeout=120): # v1 - Acquire lock on custom context
    print "\nLOCK requested at {}\n".format(time.ctime())
    global LockContextDir
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
    if not context:
        context = 'global'

    contextDir = LockRootDir + context
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
    lockStamp = None
    lockObtained = timedOut = sleepMsg = False
    while not lockObtained or timedOut:
        try: # and acquire lock (smaphore)
            os.mkdir(lockDir)
            # The time between creating the lock directory and creating the lock time file is the yield time
            with open(lockTimeFile, 'w') as f: # Stake a claim to the duration of our lock reservation
                f.write(str(lockTime))
            lockObtained = True
            debug("acquireLock() lock obtained & reserved for {} secs".format(lockTime))
            print "\nLOCK acquired at {}\n".format(time.ctime())
            LockContextDir = contextDir
        except: # lock is already taken...
            timestamp = os.path.getmtime(lockDir) # Get time of existing lock
            if timestamp != lockStamp:
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
            if time.time() > lockStamp + reservedLockTime: # Lock time expired reservation
                os.rmdir(lockDir) # We bump it
                debug("acquireLock() deleting existing expired lock")
                continue # and try again
            else: # Lock time has not yet expired reservation; honour it and keep trying until success or timeout
                if time.time() - startTime + PauseSleep > timeout:
                    debug("acquireLock() timed out, aborting")
                    timedOut = True
                else:
                    if sleepMsg:
                        debug("acquireLock() sleeping to wait for lock release or timeout")
                        sleepMsg = False
                    time.sleep(PauseSleep)

    return True if lockObtained else False

def yieldLock(): # v1 - Yield existing lock
    print "\nLOCK released at {}\n".format(time.ctime())
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
    except:
        debug("yieldLock() could not delete lockDir {}".format(lockDir))
    try:
        os.remove(lockTimeFile)
        debug("yieldLock() deleted lockTimeFile {}".format(lockTimeFile))
    except:
        debug("yieldLock() could not delete lockTimeFile {}".format(lockTimeFile))

    LockContextDir = None
