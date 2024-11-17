#
# CLI functions2 - (requires cli.py; use of #block directive in sendCLI_configChain2() requires cliWarp.py)
# cli2.py v2
#
import time                         # Used by sendCLI_configChain2 with 'block directive

def sendCLI_configChain2(chainStr, returnCliError=False, msgOnError=None, waitForPrompt=True, abortOnError=True): # v2 - Enhanced sendCLI_configChain with embedded directives
    # Syntax: chainStr can be a multi-line string where individual commands are on new lines or separated by the semi-colon ";" character
    # Some embedded directive commands are allowed, these must always begin with the hash "#" character:
    # #error fail       : If a subsequent command generates an error, make the entire script fail
    # #error stop       : If a subsequent command generates an error, do not fail the script but stop processing firther commands
    # #error continue   : If a subsequent command generates an error, ignore it and continue executing remaining commands
    # #block start [n]  : Mark the beginning of a block of commands which will need to be sourced locally on the switch; requires warpBuffer functions
    #                     Used for commands which would otherwise temporarily compromise SSH/Telnet connectivity to the switch
    #                     [n] = Optional number of seconds to sleep after block execution
    # #block execute [n]: Mark the end of block of commands which are to sourced locally on the switch
    #                     If this directive is not seen, and the "#block start" was seen, all commands from the start of
    #                     block section to the last command in the list will be sourced locally on the switch using warpBuffer_execute()
    #                     [n] = Optional number of seconds to sleep after block execution
    cmdList = configChain(chainStr)
    regexWarpBlock = re.compile('^#block +(start|execute)(?: +(\d+))? *$')
    regexErrMode = re.compile('^#error +(fail|stop|continue) *$')

    # Check if last command is a directive, as we have special processing for the last line and don't want directives there
    if regexWarpBlock.match(cmdList[-1]) or regexErrMode.match(cmdList[-1]):
        cmdList.pop() # We just pop it off, they serve no purpose as last line anyway

    successStatus = True
    warpBlock = False
    warpBlockLines = 0
    warpBlockExec = False
    warpBlockWait = 0
    for cmd in cmdList[:-1]: # All but last line
        embeddedWarpBlock = regexWarpBlock.match(cmd)
        embeddedErrMode = regexErrMode.match(cmd)
        if embeddedWarpBlock and "warpBuffer_execute" in globals():
            warpBlockCmd = embeddedWarpBlock.group(1)
            warpBlockTimer = embeddedWarpBlock.group(2)
            debug("sendCLI_configChain2() directive #block {}".format(warpBlockCmd))
            if warpBlockTimer:
                warpBlockWait = int(warpBlockTimer)
                debug("sendCLI_configChain2() directive #block waitTimer = {}".format(warpBlockWait))
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
        if warpBlock:
            warpBuffer_add(cmd)
            warpBlockLines += 1
            continue # warpBuffer_add always succeeds
        elif warpBlockExec:
            if warpBlockWait:
                warpBuffer_execute(None, waitForPrompt=False)
                debug("sendCLI_configChain2() #block exec sleeping {} secs after execute".format(warpBlockWait))
                time.sleep(warpBlockWait)
                debug("sendCLI_configChain2() sending carriage return after sleep")
                emc_cli.send('') # Empty send, to re-sync output buffer
                success = sendCLI_configCommand('', returnCliError, msgOnError)
            else:
                success = warpBuffer_execute(None, returnCliError, msgOnError)
            warpBlock = False
            warpBlockLines = 0
            warpBlockExec = False
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
