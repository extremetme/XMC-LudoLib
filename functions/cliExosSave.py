#
# Save Config functions (requires cli.py)
# cliExosSave.py v1
#
import re                           # Used by vossSaveConfigRetry
import time                         # Used by vossSaveConfigRetry & vossWaitNoUsersConnected

def exosSaveConfigRetry(waitTime=10, retries=3, returnCliError=False): # v1 - On EXOS a save config can fail: Error: This command cannot be executed during configuration save.
    # Only supported for family = 'Summit Series'
    cmd = 'save configuration'
    retryCount = 0

    while retryCount < retries:
        sendCLI_configCommand(cmd, returnCliError=True)
        if not LastError:
            return True

        # If we get here, then the save errored, possibly because: "Error: This command cannot be executed during configuration save."
        retryCount += 1
        printLog("==> Save config did not happen. Waiting {} seconds before retry...".format(waitTime))
        time.sleep(waitTime)
        printLog("==> Retry {}\n".format(retryCount))

    # Last try, succeed or bust
    sendCLI_configCommand(cmd, returnCliError=returnCliError)
    if LastError:
        printLog("==> Save config did not happen. Exausted retries...")
        return False
    else:
        return True
