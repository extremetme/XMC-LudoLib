#
# Save Config functions (requires cli.py v26)
# cliVossSave.py v6
#
import re                           # Used by vossSaveConfigRetry
import time                         # Used by vossSaveConfigRetry & vossWaitNoUsersConnected

def vossSaveConfigRetry(waitTime=10, retries=3, returnCliError=False, aggressive=False): # v5 - On VOSS a save config can fail, if another CLI session is doing "show run", so we need to be able to backoff and retry
    # Only supported for family = 'VSP Series'
    global LastError
    cmd = 'save config'
    if Sanity:
        printLog("SANITY> {}".format(cmd))
        ConfigHistory.append(cmd)
        LastError = None
        return True

    retryCount = 0
    while retryCount <= retries:
        resultObj = emc_cli.send(cmd, True)
        if resultObj.isSuccess():
            outputStr = cleanOutput(resultObj.getOutput())
            if outputStr and re.search(r'Save config to file \S+ successful', outputStr): # Check for message indicating successful save
                ConfigHistory.append(cmd)
                LastError = None
                return True
            # If we get here, then the save did not happen, possibly because: "Another show or save in progress.  Please try the command later."
            retryCount += 1
            if retries > 0:
                if aggressive and retryCount == retries:
                    # We become aggressive, we kill all other SSH/Telnet sessions
                    printLog("==> Save config did not happen. Getting aggressive... killing all other CLI sessions...")
                    cliSessionsList = sendCLI_showRegex('list://show users||^(Telnet|SSH)(\d+) +\S+ +\S+ +[\d\.\:]+ *$', 'cliSessionsList')
                    for sessionTuple in cliSessionsList:
                        sendCLI_configCommand('clear {} {}'.format(sessionTuple[0], sessionTuple[1]), returnCliError=True, historyAppend=False)
                else: # Wait and try again
                    if retryCount > retries:
                        printLog("==> Save config did not happen. Exausted retries...")
                    else:
                        printLog("==> Save config did not happen. Waiting {} seconds before retry...".format(waitTime))
                        time.sleep(waitTime)
                        printLog("==> Retry {}\n".format(retryCount))
        else:
            exitError(resultObj.getError())

    if returnCliError: # If we asked to return upon CLI error, then the error message will be held in LastError
        LastError = outputStr
        return False
    exitError(outputStr)

def vossWaitNoUsersConnected(waitTime=10, retries=3, aggressive=False): # v4 - Waits until no other Telnet/SSH connections to VSP switch
    # Only supported for family = 'VSP Series'
    retryCount = 0
    while retryCount <= retries:
        if sendCLI_showRegex('bool://show users||^(?:Telnet|SSH).+\d *$'):
            retryCount += 1
            if retries > 0:
                if aggressive and retryCount == retries:
                    # We become aggressive, we kill all other SSH/Telnet sessions
                    printLog("==> Some users are still connected. Getting aggressive... killing all other CLI sessions...")
                    cliSessionsList = sendCLI_showRegex('list://show users||^(Telnet|SSH)(\d+) +\S+ +\S+ +[\d\.\:]+ *$', 'cliSessionsList')
                    for sessionTuple in cliSessionsList:
                        sendCLI_configCommand('clear {} {}'.format(sessionTuple[0], sessionTuple[1]), returnCliError=True, historyAppend=False)
                else: # Wait and try again
                    if retryCount > retries:
                        printLog("==> Some users are still connected. Exausted retries...")
                        return False
                    else:
                        printLog("==> Some users are still connected. Waiting {} seconds before retry...".format(waitTime))
                        time.sleep(waitTime)
                        printLog("==> Retry {}\n".format(retryCount))
        else:
            return True
