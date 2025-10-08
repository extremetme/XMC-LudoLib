#
# CLI append to config file functions (requires cli.py)
# cliAppend.py v7
#
AppendBuffer = []

def appendBuffer_add(chainStr): # v1 - Preload AppendBuffer with config or configChains; buffer can then be appended to config.cfg with appendConfigDotCfg()
    if Family != 'VSP Series':
        exitError('appendConfigDotCfg(): only supported with "VSP Series" family type')
    global AppendBuffer
    cmdList = configChain(chainStr)
    for cmd in cmdList:
        cmdAdd = re.sub(r'\n.+$', '', cmd) # Strip added CR+y or similar (these are not required when sourcing from file on VOSS and do not work on ERS anyway)
        AppendBuffer.append(cmdAdd)

def appendConfigDotCfg(chainStr=None): # v6 - Appends config commands to config.cfg (before 'end' statement) to be executed after reboot
    global LastError
    if Family != 'VSP Series':
        exitError('appendConfigDotCfg(): only supported with "VSP Series" family type')
    global AppendBuffer
    if chainStr:
        appendBuffer_add(chainStr)
    if Sanity:
        for cmd in AppendBuffer:
            printLog("SANITY(appended to config.cfg)> {}".format(cmd))
            ConfigHistory.append('[after reboot] ' + cmd)
        LastError = None
        return True
    # Edit config.cfg
    cmdStream = "edit config.cfg\n?end\nO" # Edit config, find 'end' from bottom of file, insert text above
    for cmd in AppendBuffer:
        cmdStream += cmd + "\n"
    cmdStream += "\x1bZZ" # Escape edit mode and save file
    debug("appendConfigDotCfg() - cmdStream:\n{}".format(cmdStream))
    resultObj = emc_cli.send(cmdStream)
    if resultObj.isSuccess():
        outputStr = cleanOutput(resultObj.getOutput())
        if outputStr and cliError("\n".join(outputStr.split("\n")[:4])): # If there is output, check for error in 1st 4 lines only
            abortError(cmd, outputStr)
        else:
            for cmd in AppendBuffer:
                printLog("Added to config.cfg: {}".format(cmd))
                ConfigHistory.append('[after reboot] ' + cmd)
            LastError = None
            AppendBuffer = []
            return True
    else:
        exitError(resultObj.getError())
