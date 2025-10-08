#
# CLI functions2 - (requires cli.py; use of #block directive in sendCLI_configChain2() requires cliWarp.py)
# cli2.py v5
#

def sendCLI_configChain2(chainStr, returnCliError=False, msgOnError=None, waitForPrompt=True, abortOnError=True, initCmdList=[], initRetries=0, initRetryDelay=0): # v4 - Enhanced sendCLI_configChain with embedded directives
    # Syntax: chainStr can be a multi-line string where individual commands are on new lines or separated by the semi-colon ";" character
    # Some embedded directive commands are allowed, these must always begin with the hash "#" character:
    # #error fail       : If a subsequent command generates an error, make the entire script fail
    # #error stop       : If a subsequent command generates an error, do not fail the script but stop processing firther commands
    # #error continue   : If a subsequent command generates an error, ignore it and continue executing remaining commands
    # #block start [n]  : Mark the beginning of a block of commands which will need to be sourced locally on the switch; requires warpBuffer functions
    #                     Used for commands which would otherwise temporarily compromise SSH/Telnet connectivity to the switch
    #                     [n] = Optional number of seconds to sleep after block execution
    # #block execute [wait|reconnect] [n]: Mark the end of block of commands which are to sourced locally on the switch
    #                     If this directive is not seen, and the "#block start" was seen, all commands from the start of
    #                     block section to the last command in the list will be sourced locally on the switch using warpBuffer_execute()
    #                     [n] = Optional number of seconds to sleep after block execution
    #                     [wait|reconnect]: "wait" will simply keep the same CLI session, and just wait [n] secs before resuming;
    #                     "reconnect" will instead tear down the CLI session after the wait [n], and bring up a fresh new CLI session;
    #                     since a new CLI session is started, this option allows a list of commands to be re-fed into the new session
    #                     via initCmdList input; "wait" is the default if [n] provided 
    # #sleep <secs>     : Sleep for specified seconds
    cmdList = configChain(chainStr)

    # Check if last command is a directive, as we have special processing for the last line and don't want directives there
    while RegexEmbeddedWarpBlock.match(cmdList[-1]) or RegexEmbeddedErrMode.match(cmdList[-1]) or RegexEmbeddedSleep.match(cmdList[-1]):
        cmdList.pop() # We just pop it off, they serve no purpose as last line anyway

    successStatus = True
    warpBlock = False
    warpBlockLines = 0
    warpBlockExec = False
    warpBlockWait = 0
    warpBlockReconnect = False
    for cmd in cmdList[:-1]: # All but last line
        embeddedWarpBlock = RegexEmbeddedWarpBlock.match(cmd)
        embeddedErrMode = RegexEmbeddedErrMode.match(cmd)
        embeddedSleep = RegexEmbeddedSleep.match(cmd)
        if embeddedWarpBlock and "warpBuffer_execute" in globals():
            warpBlockCmd = embeddedWarpBlock.group(1)
            warpBlockMode = embeddedWarpBlock.group(2)
            warpBlockTimer = embeddedWarpBlock.group(3)
            debug("sendCLI_configChain2() directive #block {}".format(warpBlockCmd))
            if warpBlockTimer:
                warpBlockWait = int(warpBlockTimer)
                debug("sendCLI_configChain2() directive #block waitTimer = {}".format(warpBlockWait))
                warpBlockReconnect = True if warpBlockMode == "reconnect" else False
                debug("sendCLI_configChain2() directive #block reconnect mode = {}".format(warpBlockReconnect))
            if warpBlockCmd == 'start':
                warpBlock = True
                continue # Next command
            elif warpBlockLines > 0: # and warpBlockCmd == 'execute'
                warpBlock = False
                warpBlockExec = True
                # Fall through
        elif embeddedErrMode:
            errorMode = embeddedErrMode.group(1)
            debug("sendCLI_configChain2() directive #error {}".format(errorMode))
            returnCliError = False if errorMode == 'fail' else True
            abortOnError = True if errorMode == 'stop' else False
            continue # Next command
        elif embeddedSleep:
            if not warpBlock:
                time.sleep(embeddedSleep.group(1))
            continue # Next command
        if warpBlock:
            warpBuffer_add(cmd)
            warpBlockLines += 1
            continue # warpBuffer_add always succeeds
        elif warpBlockExec:
            if warpBlockWait:
                warpBuffer_execute(None, waitForPrompt=False)
                debug("sendCLI_configChain2() #block exec sleeping {} secs after execute".format(warpBlockWait))
                time.sleep(warpBlockWait)
                if warpBlockReconnect: # Reconnect mode
                    emc_cli.close()
                    debug("sendCLI_configChain2() re-connecting new CLI session after sleep")
                    if not initCmdList:
                        initCmdList.append('') # We want to send at very least an empty command
                    for initCmd in initCmdList:
                        sendCLI_showCommand(initCmd, retries=initRetries, retryDelay=initRetryDelay)
                else: # Wait mode
                    debug("sendCLI_configChain2() sending carriage return after sleep")
                    emc_cli.send('') # Empty send, to re-sync output buffer
                success = sendCLI_configCommand('', returnCliError, msgOnError)
            else:
                success = warpBuffer_execute(None, returnCliError, msgOnError)
            warpBlock = False
            warpBlockLines = 0
            warpBlockExec = False
            warpBlockWait = 0
            warpBlockReconnect = False
        else:
            success = sendCLI_configCommand(cmd, returnCliError, msgOnError)
        if not success:
            successStatus = False
            if abortOnError:
                return False
    # Last line now
    if warpBlockLines > 0: # We execute the block even if we do not find last line #block execute
        if warpBlockWait:
            warpBuffer_execute(cmdList[-1], waitForPrompt=False)
            debug("sendCLI_configChain2() #block start sleep {} after execute".format(warpBlockWait))
            time.sleep(warpBlockWait)
            emc_cli.send('') # Empty send, to re-sync output buffer
            success = sendCLI_configCommand('', returnCliError, msgOnError, waitForPrompt)
        else:
            success = warpBuffer_execute(cmdList[-1], returnCliError, msgOnError, waitForPrompt)
    else:
        success = sendCLI_configCommand(cmdList[-1], returnCliError, msgOnError, waitForPrompt)
    if not success:
        return False
    return successStatus
