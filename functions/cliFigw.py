#
# FIGW CLI functions (requires VOSS 8.4.2 or later)(requires cli.py)
# cliFigw.py v6
#

def figwCLI_showCommand(cmd, returnCliError=False, msgOnError=None): # v2 - Send a FIGW CLI show command; return output
    # Only supported for family = 'VSP Series' and either a VSP7400 or VSP4900 with FIGW VM installed
    # VSP must be in config mode and cmd must not have any quotes or carriage returns
    global LastError
    figwCmd = CLI_Dict[Family]['figw_cli'].format(cmd)
    resultObj = emc_cli.send(figwCmd)
    if resultObj.isSuccess():
        outputStr = cleanOutput(resultObj.getOutput())
        if outputStr and cliError("\n".join(outputStr.split("\n")[:4])): # If there is output, check for error in 1st 4 lines only (timestamp banner might shift it by 3 lines)
            if returnCliError: # If we asked to return upon CLI error, then the error message will be held in LastError
                LastError = outputStr
                if msgOnError:
                    print "==> Ignoring above error: {}\n\n".format(msgOnError)
                return None
            abortError(figwCmd, outputStr)
        LastError = None
        return outputStr
    else:
        exitError(resultObj.getError())

def figwCLI_showRegex(cmdRegexStr, debugKey=None, returnCliError=False, msgOnError=None): # v1 - Send FIGW show command and extract values from output using regex
    # Only supported for family = 'VSP Series' and either a VSP7400 or VSP4900 with FIGW VM installed
    # VSP must be in config mode and cmd in cmdRegexStr must not have any quotes or carriage returns
    # Regex is by default case-sensitive; for case-insensitive include (?i) at beginning of regex on input string
    mode, cmdList, regex = parseRegexInput(cmdRegexStr)
    for cmd in cmdList:
        # If cmdList we try each command in turn until one works; we don't want to bomb out on cmds before the last one in the list
        ignoreCliError = True if len(cmdList) > 1 and cmd != cmdList[-1] else returnCliError
        outputStr = figwCLI_showCommand(cmd, ignoreCliError, msgOnError)
        if outputStr:
            break
    if not outputStr: # returnCliError true
        return None
    data = re.findall(regex, outputStr, re.MULTILINE)
    debug("figwCLI_showRegex() raw data = {}".format(data))
    # Format we return data in depends on what '<type>://' was pre-pended to the cmd & regex
    value = formatOutputData(data, mode)
    if Debug:
        if debugKey: debug("{} = {}".format(debugKey, value))
        else: debug("figwCLI_showRegex OUT = {}".format(value))
    return value

def figwCLI_configCommand(cmd, returnCliError=False, msgOnError=None, waitForPrompt=True): # v2 - Send a FIGW CLI config command
    # Only supported for family = 'VSP Series' and either a VSP7400 or VSP4900 with FIGW VM installed
    # VSP must be in config mode and cmd must not have any quotes or carriage returns
    global LastError
    figwCmd = CLI_Dict[Family]['figw_cli'].format(cmd)
    if Sanity:
        print "SANITY> {}".format(figwCmd)
        ConfigHistory.append(figwCmd)
        LastError = None
        return True
    resultObj = emc_cli.send(figwCmd, waitForPrompt)
    if resultObj.isSuccess():
        outputStr = cleanOutput(resultObj.getOutput())
        if outputStr and cliError("\n".join(outputStr.split("\n")[:4])): # If there is output, check for error in 1st 4 lines only
            if returnCliError: # If we asked to return upon CLI error, then the error message will be held in LastError
                LastError = outputStr
                if msgOnError:
                    print "==> Ignoring above error: {}\n\n".format(msgOnError)
                return False
            abortError(figwCmd, outputStr)
        ConfigHistory.append(figwCmd)
        LastError = None
        return True
    else:
        exitError(resultObj.getError())

def figwCLI_configChain(chainStr, returnCliError=False, msgOnError=None, waitForPrompt=True): # v1 - Send a semi-colon separated list of FIGW config commands
    # Only supported for family = 'VSP Series' and either a VSP7400 or VSP4900 with FIGW VM installed
    # VSP must be in config mode and cmds in chainStr must not have any quotes or carriage returns
    cmdList = configChain(chainStr)
    for cmd in cmdList[:-1]: # All but last
        success = figwCLI_configCommand(cmd, returnCliError, msgOnError)
        if not success:
            return False
    # Last now
    success = figwCLI_configCommand(cmdList[-1], returnCliError, msgOnError, waitForPrompt)
    if not success:
        return False
    return True
