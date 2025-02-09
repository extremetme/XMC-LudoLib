#
# CLI warp buffer functions (requires cli.py v26)
# cliWarp.py v9
#
import os                           # Used by warpBuffer_execute
WarpBuffer = []

def warpBuffer_add(chainStr): # v1 - Preload WarpBuffer with config or configChains; buffer can then be executed with warpBuffer_execute()
    global WarpBuffer
    cmdList = configChain(chainStr)
    for cmd in cmdList:
        cmdAdd = re.sub(r'\n.+$', '', cmd) # Strip added CR+y or similar (these are not required when sourcing from file on VOSS and do not work on ERS anyway)
        WarpBuffer.append(cmdAdd)

def warpBuffer_execute(chainStr=None, returnCliError=False, msgOnError=None, waitForPrompt=True, historyAppend=True): # v8 - Appends to existing WarpBuffer and then executes it
    # Same as sendCLI_configChain() but all commands are placed in a script file on the switch and then sourced there
    # Apart from being fast, this approach can be used to make config changes which would otherwise result in the switch becomming unreachable
    # Use of this function assumes that the connected device (VSP) is already in privExec + config mode
    global WarpBuffer
    global LastError
    xmcTftpRoot = '/tftpboot'
    xmcServerIP = emc_vars["serverIP"]
    switchIP = emc_vars["deviceIP"]
    userName = emc_vars["userName"].replace('.', '_').replace('@', '_')
    tftpCheck = {
        #'VSP Series':    'bool://show boot config flags||^flags tftpd true',
        'VSP Series':    True, # Always enabled as Client,
        'Summit Series': 'bool://show process tftpd||Ready',
        'ERS Series':    True, # Always enabled
    }
    tftpActivate = {
        #'VSP Series':    'boot config flags tftpd',
        'Summit Series': 'start process tftpd',
    }
    tftpDeactivate = {
        'VSP Series':    'no boot config flags tftpd',
        'Summit Series': 'terminate process tftpd graceful',
    }
    tftpExecute = { # XMC server IP (TFTP server), Script file to fetch and execute
        'VSP Series':    'copy "{0}:{1}" /intflash/.script.src -y; more .script.src; source .script.src debug',
        'Summit Series': 'tftp get {0} "{1}" .script.xsf; cat .script.xsf; run script .script.xsf',
        'ERS Series':    'configure network address {0} filename "{1}"',
    }

    if chainStr:
        warpBuffer_add(chainStr)
    if Family not in tftpCheck:
        exitError('Sourcing commands via TFTP only supported in family types: {}'.format(", ".join(list(tftpCheck.keys()))))

    # Determine whether switch can do TFTP
    if tftpCheck[Family] == True:
        tftpEnabled = True
    else:
        tftpEnabled = sendCLI_showRegex(tftpCheck[Family])
    if not tftpEnabled:
        if Sanity:
            print "SANITY> {}".format(tftpActivate[Family])
            if historyAppend:
                ConfigHistory.append(tftpActivate[Family])
        else:
            sendCLI_configCommand(tftpActivate[Family], returnCliError, msgOnError, historyAppend=historyAppend) # Activate TFTP now
        warpBuffer_add(tftpDeactivate[Family])      # Restore TFTP state on completion

    if Sanity:
        for cmd in WarpBuffer:
            print "SANITY(warp)> {}".format(cmd)
            if historyAppend:
                ConfigHistory.append(cmd)
        LastError = None
        return True

    # Write the commands to a file under XMC's TFTP root directory
    tftpFileName = userName + '.' + scriptName().replace(' ', '_') + '.' + switchIP.replace('.', '_')
    tftpFilePath = xmcTftpRoot + '/' + tftpFileName
    try:
        with open(tftpFilePath, 'w') as f:
            if Family == 'VSP Series': # Always add these 2 lines, as VSP source command does not inherit current context
                f.write("enable\n")
                f.write("config term\n")
            for cmd in WarpBuffer:
                f.write(cmd + "\n")
            f.write("\n") # Make sure we have an empty line at the end, or VSP sourcing won't process last line...
            debug("warpBuffer - write of TFTP config file : {}".format(tftpFilePath))
    except Exception as e: # Expect IOError
        print "{}: {}".format(type(e).__name__, str(e))
        exitError("Unable to write to TFTP file '{}'".format(tftpFilePath))

    # Make the switch fetch the file and execute it
    success = sendCLI_configChain(tftpExecute[Family].format(xmcServerIP, tftpFileName), returnCliError, msgOnError, waitForPrompt, historyAppend=False)
    # Clean up by deleting the file from XMC TFTP directory
    os.remove(tftpFilePath)
    debug("warpBuffer - delete of TFTP config file : {}".format(tftpFilePath))

    if not success: # In this case some commands might have executed, before the error; these won't be captured in ConfigHistory
        WarpBuffer = []
        return False
    if historyAppend:
        ConfigHistory.extend(WarpBuffer)
    WarpBuffer = []
    LastError = None
    return True
