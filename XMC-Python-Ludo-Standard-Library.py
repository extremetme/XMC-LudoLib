'''
This script is provided free of charge by Extreme. We hope such scripts are
helpful when used in conjunction with Extreme products and technology and can
be used as examples to modify and adapt for your ultimate requirements.
Extreme will not provide any official support for these scripts. If you do
have any questions or queries about any of these scripts you may post on
Extreme's community website "The Hub" (https://community.extremenetworks.com/)
under the scripting category.

ANY SCRIPTS PROVIDED BY EXTREME ARE HEREBY PROVIDED "AS IS", WITHOUT WARRANTY
OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL EXTREME OR ITS THIRD PARTY LICENSORS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE USE OR DISTRIBUTION OF SUCH
SCRIPTS.
'''

# --> Insert here script description, version and metadata <--

##########################################################
# XMC Script: <name of script>                           #
# Written by Ludovico Stevens, TME Extreme Networks      #
##########################################################

__version__ = '0.1'

'''
#@MetaDataStart
#@DetailDescriptionStart
#######################################################################################
# 
# <description, over multiple lines>
#
#######################################################################################
#@DetailDescriptionEnd
# ( = &#40;
# ) = &#41;
# , = &#44;
# < = &lt;
# > = &gt;
#@SectionStart (description = "Sanity / Debug")
#    @VariableFieldLabel (
#        description = "Sanity: enable if you do not trust this script and wish to first see what it does. In sanity mode config commands are not executed",
#        type = string,
#        required = no,
#        validValues = [Enable, Disable],
#        name = "userInput_sanity",
#    )
#    @VariableFieldLabel (
#        description = "Debug: enable if you need to report a problem to the script author",
#        type = string,
#        required = no,
#        validValues = [Enable, Disable],
#        name = "userInput_debug",
#    )
#@SectionEnd
#@MetaDataEnd
'''



##########################################################
# Ludo Standard library; Version 4.05                    #
# Written by Ludovico Stevens, TME Extreme Networks      #
##########################################################
Debug = False    # Enables debug messages
Sanity = False   # If enabled, config commands are not sent to host (show commands are operational)

#
# IMPORTS: distributed amongst sections below
#

#
# Base functions
# v7
import re                           # Used by scriptName
import time                         # Used by exitError
ExitErrorSleep = 10

def debug(debugOutput): # v1 - Use function to include debugging in script; set above Debug variable to True or False to turn on or off debugging
    if Debug:
        print debugOutput

def exitError(errorOutput, sleep=ExitErrorSleep): # v3 - Exit script with error message and setting status appropriately
    if 'workflowMessage' in emc_vars: # Workflow
        time.sleep(sleep) # When workflow run on multiple devices, want ones that error to be last to complete, so THEY set the workflow message
        emc_results.put("deviceMessage", errorOutput)
        emc_results.put("activityMessage", errorOutput)
        emc_results.put("workflowMessage", errorOutput)
    emc_results.setStatus(emc_results.Status.ERROR)
    raise RuntimeError(errorOutput)

def abortError(cmd, errorOutput): # v1 - A CLI command failed, before bombing out send any rollback commands which may have been set
    print "Aborting script due to error on previous command"
    try:
        rollbackStack()
    finally:
        print "Aborting because this command failed: {}".format(cmd)
        exitError(errorOutput)

def scriptName(): # v1 - Returns the assigned name of the Script or Workflow
    name = None
    if 'workflowName' in emc_vars: # Workflow
        name = emc_vars['workflowName']
    elif 'javax.script.filename' in emc_vars: # Script
        nameMatch = re.search(r'\/([^\/\.]+)\.py$', emc_vars['javax.script.filename'])
        name = nameMatch.group(1) if nameMatch else None
    return name

def workflow_DeviceMessage(msg): # v1 - Set workflow messages appropriately; '<>' is replaced with device IP or list
    singleDeviceMsg = manyDevicesMsg = msg
    if '<>' in msg:
        devicesListStr = emc_vars['devices'][1:-1]
        singleDeviceMsg = msg.replace('<>', emc_vars['deviceIP']).replace('(s)', '').replace('(es)', '')
        if len(devicesListStr.split(',')) > 1:
            manyDevicesMsg = msg.replace('<>', devicesListStr).replace('(s)', 's').replace('(es)', 'es')
        else:
            manyDevicesMsg = singleDeviceMsg
    emc_results.put("deviceMessage", singleDeviceMsg)
    emc_results.put("activityMessage", manyDevicesMsg)
    emc_results.put("workflowMessage", manyDevicesMsg)


#
# Family functions
# v3
Family = None # This needs to get set by setFamily()
FamilyChildren = { # Children will be rolled into parent family for these scripts
    'Extreme Access Series' : 'VSP Series',
    'Unified Switching VOSS': 'VSP Series',
    'Unified Switching EXOS': 'Summit Series',
    'Universal Platform VOSS': 'VSP Series',
    'Universal Platform EXOS': 'Summit Series',
    'Universal Platform Fabric Engine': 'VSP Series',
    'Universal Platform Switch Engine': 'Summit Series',
    'ISW-24W-4X': 'ISW-Series-Marvell',
}

def setFamily(cliDict={}, family=None): # v3 - Set global Family variable; automatically handles family children, as far as this script is concerned
    global Family
    if family:
        Family = family
    elif emc_vars["family"] in FamilyChildren:
        Family = FamilyChildren[emc_vars["family"]]
    elif emc_vars["deviceType"] in FamilyChildren:
        Family = FamilyChildren[emc_vars["deviceType"]]
    else:
        Family = emc_vars["family"]
    print "Using family type '{}' for this script".format(Family)
    if cliDict and Family not in cliDict:
        exitError('This scripts only supports family types: {}'.format(", ".join(list(cliDict.keys()))))
    return Family


#
# CLI/SNMP Rollback functions
# v4
RollbackStack = [] # Format [ ['cli', <command>], ['snmp', [requestDict, instance, oldValue], ...]]

def rollbackStack(): # v2 - Execute all commands on the rollback stack
    if RollbackStack:
        print "\nApplying rollback commands to undo partial config and return device to initial state"
        while RollbackStack:
            cfgType, data = RollbackStack.pop()
            if cfgType == 'cli':
                sendCLI_configChain(data, returnCliError=True)
            elif cfgType == 'snmp':
                snmpSet(data[0], instance=data[1], value=data[2], returnError=True)
            else:
                print "Invalid rollback stack data entry: {}".format(cfgType)

def rollbackCommand(cmd): # v2 - Add a command to the rollback stack; these commands will get popped and executed should we need to abort
    global RollbackStack
    RollbackStack.append(['cli', cmd])
    cmdList = map(str.strip, re.split(r'[;\n]', cmd)) # cmd could be a configChain
    cmdList = [x for x in cmdList if x] # Weed out empty elements 
    cmdOneLiner = " / ".join(cmdList)
    print "Pushing onto rollback stack CLI: {}\n".format(cmdOneLiner)

def rollbackSnmp(requestDict, instance, oldValue): # v1 - Add SNMP request to rollback stack
    # These commands will get popped and executed as snmpSet should we need to abort
    global RollbackStack
    RollbackStack.append(['snmp', [requestDict, instance, oldValue]])
    oidList, instList, _, valueList = snmpInputLists("rollbackSnmp", requestDict, instance, oldValue)
    print "Pushing onto rollback stack SNMP:"
    for inOid, inst, currVal in zip(oidList, instList, valueList):
        displayOid, oid = separateOid(inOid)
        setOid = '.'.join([oid, str(inst)]) if inst != None else oid
        print " - {}{} revert to {}".format(displayOid, setOid, currVal)

def rollBackPop(number=0): # v1 - Remove entries from RollbackStack
    global RollbackStack
    if number == 0:
        RollbackStack = []
        print "Rollback stack emptied"
    else:
        del RollbackStack[-number:]
        print "Rollback stack popped last {} entries".format(number)


#
# CLI functions
# v25
import re
RegexPrompt = re.compile('.*[\?\$%#>]\s?$')
RegexError  = re.compile(
    '^%|\x07|error|invalid|cannot|unable|bad|not found|not exist|not allowed|no such|out of range|incomplete|failed|denied|can\'t|ambiguous|do not|unrecognized',
    re.IGNORECASE | re.MULTILINE
)
RegexNoError  = re.compile( # Messages which would be false positives for an error condition, when they are just a warning..
    '(?:'
    + 'Both ends of MACsec link cannot have the same key-parity value'
    + '|% Saving \d+ bytes to flash:startup-config' # ISW: copy running-config startup-config
    + ')',
    re.IGNORECASE | re.MULTILINE
)
RegexContextPatterns = { # Ported from acli.pl
    'ERS Series' : [
        re.compile('^(?:interface |router \w+$|route-map (?:\"[\w\d\s\.\+-]+\"|[\w\d\.-]+) \d+$|ip igmp profile \d+$|wireless|application|ipv6 dhcp guard policy |ipv6 nd raguard policy )'), # level0
        re.compile('^(?:security|crypto|ap-profile |captive-portal |network-profile |radio-profile )'), # level1
        re.compile('^(?:locale)'), # level2
    ],
    'VSP Series' : [
        re.compile('^ *(?:interface |router \w+$|router vrf|route-map (?:\"[\w\d\s\.\+-]+\"|[\w\d\.-]+) \d+$|application|i-sid \d+|wireless|logical-intf isis \d+|mgmt (?:\d|clip|vlan|oob)|ovsdb$)'), # level0
        re.compile('^ *(?:route-map (?:\"[\w\d\s\.\+-]+\"|[\w\d\.-]+) \d+$)'), # level1
    ],
    'ISW-Series' : [
        re.compile('^ *(?:ringv2-group |interface )'), # level0
    ],
    'ISW-Series-Marvell' : [
        re.compile('^ *(?:ringv2-group |interface )'), # level0
    ],
}
RegexExitInstance = re.compile('^ *(?:exit|back|end|config|save)(?:\s|$)')
Indent = 3 # Number of space characters for each indentation
LastError = None
ConfigHistory = []

def cliError(outputStr): # v1 - Check command output for CLI error message
    if not RegexNoError.search(outputStr) and RegexError.search(outputStr):
        return True
    else:
        return False

def cleanOutput(outputStr): # v5 - Remove echoed command and final prompt from output
    if re.match(r'Error:', outputStr): # Case where emc_cli.send timesout: "Error: session exceeded timeout: 30 secs"
        return outputStr
    outputLines = outputStr.splitlines()
    lastLine = outputLines[-1]
    if RegexPrompt.match(lastLine):
        return '\n'.join(outputLines[1:-1])
    else:
        return '\n'.join(outputLines[1:])

def configChain(chainStr): # v2 - Produces a list of a set of concatenated commands (either with ';' or newlines)
    chainStr = re.sub(r'\n(\w)(\x0d?\n|\s*;|$)', chr(0) + r'\1\2', chainStr) # Mask trailing "\ny" or "\nn" on commands before making list
    # Checking for \x0d? is necessary when DOS text files are transferred to XIQ-SE, and read and processed locally..
    cmdList = map(str.strip, re.split(r'[;\n]', chainStr))
    cmdList = filter(None, cmdList) # Filter out empty lines, if any
    cmdList = [re.sub(r'\x00(\w)(\x0d?\n|$)', r'\n\1\2', x) for x in cmdList] # Unmask after list made
    return cmdList

def parseRegexInput(cmdRegexStr): # v1 - Parses input command regex for both sendCLI_showRegex() and xmcLinuxCommand()
    # cmdRegexStr format: <type>://<cli-show-command> [& <additional-show-cmd>]||<regex-to-capture-with>
    if re.match(r'\w+(?:-\w+)?://', cmdRegexStr):
        mode, cmdRegexStr = map(str.strip, cmdRegexStr.split('://', 1))
    else:
        mode = None
    cmd, regex = map(str.strip, cmdRegexStr.split('||', 1))
    cmdList = map(str.strip, cmd.split('&'))
    return mode, cmdList, regex

def formatOutputData(data, mode): # v3 - Formats output data for both sendCLI_showRegex() and xmcLinuxCommand()
    if not mode                 : value = data                                   # Legacy behaviour same as list
    elif mode == 'bool'         : value = bool(data)                             # No regex capturing brackets required
    elif mode == 'str'          : value = str(data[0]) if data else None         # Regex should have 1 capturing bracket at most
    elif mode == 'str-lower'    : value = str(data[0]).lower() if data else None # Same as str but string made all lowercase
    elif mode == 'str-upper'    : value = str(data[0]).upper() if data else None # Same as str but string made all uppercase
    elif mode == 'str-join'     : value = ''.join(data)                          # Regex with max 1 capturing bracket, joins list to string
    elif mode == 'str-nwlnjoin' : value = "\n".join(data)                        # Regex with max 1 capturing bracket, joins list to multi-line string
    elif mode == 'int'          : value = int(data[0]) if data else None         # Regex must have 1 capturing bracket at most
    elif mode == 'list'         : value = data                                   # If > 1 capturing brackets, will be list of tuples
    elif mode == 'list-reverse' : value = list(reversed(data))                   # Same as list but in reverse order
    elif mode == 'list-diagonal': value = [data[x][x] for x in range(len(data))] # Regex pat1|pat2 = list of tuples; want [0][0],[1][1],etc
    elif mode == 'tuple'        : value = data[0] if data else ()                # Regex > 1 capturing brackets on same line, returns 1st tuple
    elif mode == 'dict'         : value = dict(data)                             # Regex must have 2 capturing brackets exactly
    elif mode == 'dict-reverse' : value = dict(map(reversed, data))              # Same as dict, but key/values will be flipped
    elif mode == 'dict-both'    : value = dict(data), dict(map(reversed, data))  # Returns 2 dict: dict + dict-reverse
    elif mode == 'dict-diagonal': value = dict((data[x][x*2],data[x][x*2+1]) for x in range(len(data))) # {[0][0]:[0][1], [1][2]:[1][3], etc}
    elif mode == 'dict-sequence': value = dict((data[x*2][0],data[x*2+1][1]) for x in range(len(data)/2)) # {[0][0]:[1][1], [2][0]:[3][1], etc}
    else:
        RuntimeError("formatOutputData: invalid scheme type '{}'".format(mode))
    return value

def sendCLI_showCommand(cmd, returnCliError=False, msgOnError=None): # v2 - Send a CLI show command; return output
    global LastError
    resultObj = emc_cli.send(cmd)
    if resultObj.isSuccess():
        outputStr = cleanOutput(resultObj.getOutput())
        if outputStr and cliError("\n".join(outputStr.split("\n")[:4])): # If there is output, check for error in 1st 4 lines only (timestamp banner might shift it by 3 lines)
            if returnCliError: # If we asked to return upon CLI error, then the error message will be held in LastError
                LastError = outputStr
                if msgOnError:
                    print "==> Ignoring above error: {}\n\n".format(msgOnError)
                return None
            abortError(cmd, outputStr)
        LastError = None
        return outputStr
    else:
        exitError(resultObj.getError())

def sendCLI_showRegex(cmdRegexStr, debugKey=None, returnCliError=False, msgOnError=None): # v1 - Send show command and extract values from output using regex
    # Regex is by default case-sensitive; for case-insensitive include (?i) at beginning of regex on input string
    mode, cmdList, regex = parseRegexInput(cmdRegexStr)
    for cmd in cmdList:
        # If cmdList we try each command in turn until one works; we don't want to bomb out on cmds before the last one in the list
        ignoreCliError = True if len(cmdList) > 1 and cmd != cmdList[-1] else returnCliError
        outputStr = sendCLI_showCommand(cmd, ignoreCliError, msgOnError)
        if outputStr:
            break
    if not outputStr: # returnCliError true
        return None
    data = re.findall(regex, outputStr, re.MULTILINE)
    debug("sendCLI_showRegex() raw data = {}".format(data))
    # Format we return data in depends on what '<type>://' was pre-pended to the cmd & regex
    value = formatOutputData(data, mode)
    if Debug:
        if debugKey: debug("{} = {}".format(debugKey, value))
        else: debug("sendCLI_showRegex OUT = {}".format(value))
    return value

def sendCLI_configCommand(cmd, returnCliError=False, msgOnError=None, waitForPrompt=True): # v4 - Send a CLI config command
    global LastError
    cmd = re.sub(r':\/\/', ':' + chr(0) + chr(0), cmd) # Mask any https:// type string
    cmd = re.sub(r' *\/\/ *', r'\n', cmd) # Convert "//" to "\n" for embedded // passwords
    cmd = re.sub(r':\x00\x00', r'://', cmd) # Unmask after // replacemt
    cmdStore = re.sub(r'\n.+$', '', cmd, flags=re.DOTALL) # Strip added "\n"+[yn] or // passwords
    if Sanity:
        print "SANITY> {}".format(cmd)
        ConfigHistory.append(cmdStore)
        LastError = None
        return True
    resultObj = emc_cli.send(cmd, waitForPrompt)
    if resultObj.isSuccess():
        outputStr = cleanOutput(resultObj.getOutput())
        if outputStr and cliError("\n".join(outputStr.split("\n")[:4])): # If there is output, check for error in 1st 4 lines only
            if returnCliError: # If we asked to return upon CLI error, then the error message will be held in LastError
                LastError = outputStr
                if msgOnError:
                    print "==> Ignoring above error: {}\n\n".format(msgOnError)
                return False
            abortError(cmd, outputStr)
        ConfigHistory.append(cmdStore)
        LastError = None
        return True
    else:
        exitError(resultObj.getError())

def sendCLI_configChain(chainStr, returnCliError=False, msgOnError=None, waitForPrompt=True, abortOnError=True): # v4 - Send a list of config commands
    # Syntax: chainStr can be a multi-line string where individual commands are on new lines or separated by the semi-colon ";" character
    # Some embedded directive commands are allowed, these must always begin with the hash "#" character:
    # #error fail       : If a subsequent command generates an error, make the entire script fail
    # #error stop       : If a subsequent command generates an error, do not fail the script but stop processing firther commands
    # #error continue   : If a subsequent command generates an error, ignore it and continue executing remaining commands
    cmdList = configChain(chainStr)
    successStatus = True
    for cmd in cmdList[:-1]: # All but last
        embedded = re.match(r'^#error +(fail|stop|continue) *$', cmd)
        if embedded:
            errorMode = embedded.group(1)
            returnCliError = False if errorMode == 'fail' else True
            abortOnError = True if errorMode == 'stop' else False
            continue # After setting the above, we skip the embedded command
        success = sendCLI_configCommand(cmd, returnCliError, msgOnError)
        if not success:
            successStatus = False
            if abortOnError:
                return False
    # Last now
    success = sendCLI_configCommand(cmdList[-1], returnCliError, msgOnError, waitForPrompt)
    if not success:
        return False
    return successStatus

def printConfigSummary(): # v4 - Print summary of all config commands executed with context indentation
    global ConfigHistory
    emc_cli.close()
    if not len(ConfigHistory):
        print "No configuration was performed"
        return
    print "The following configuration was successfully performed on switch:"
    indent = ''
    level = 0
    if Family in RegexContextPatterns:
        maxLevel = len(RegexContextPatterns[Family])
    for cmd in ConfigHistory:
        if Family in RegexContextPatterns:
            if level < maxLevel and RegexContextPatterns[Family][level].match(cmd):
                print "-> {}{}".format(indent, cmd)
                level += 1
                indent = ' ' * Indent * level
                continue
            elif RegexExitInstance.match(cmd):
                if level > 0:
                    level -= 1
                indent = ' ' * Indent * level
        print "-> {}{}".format(indent, cmd)
    ConfigHistory = []


#
# CLI functions2 (use of #block directive in sendCLI_configChain2() requires CLI warp buffer functions)
# v1
import time                         # Used by sendCLI_configChain2 with 'block directive

def sendCLI_configChain2(chainStr, returnCliError=False, msgOnError=None, waitForPrompt=True, abortOnError=True): # v1 - Enhanced sendCLI_configChain with embedded directives
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
            debug("sendCLI_configChain() directive #block {}".format(warpBlockCmd))
            if warpBlockTimer:
                warpBlockWait = int(warpBlockTimer)
                debug("sendCLI_configChain() directive #block waitTimer = {}".format(warpBlockWait))
            if warpBlockCmd == 'start':
                warpBlock = True
                continue # Next command
            elif warpBlockLines > 0: # and warpBlockCmd == 'execute'
                warpBlock = False
                warpBlockExec = True
                # Fall through
        elif embeddedErrMode:
            errorMode = embeddedErrMode.group(1)
            debug("sendCLI_configChain() directive #error {}".format(errorMode))
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
                debug("sendCLI_configChain() #block exec sleep {} after execute".format(warpBlockWait))
                time.sleep(warpBlockWait)
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
            debug("sendCLI_configChain() #block start sleep {} after execute".format(warpBlockWait))
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


#
# CLI append to config file functions (requires CLI functions)
# v6
AppendBuffer = []

def appendBuffer_add(chainStr): # v1 - Preload AppendBuffer with config or configChains; buffer can then be appended to config.cfg with appendConfigDotCfg()
    if Family != 'VSP Series':
        exitError('appendConfigDotCfg(): only supported with "VSP Series" family type')
    global AppendBuffer
    cmdList = configChain(chainStr)
    for cmd in cmdList:
        cmdAdd = re.sub(r'\n.+$', '', cmd) # Strip added CR+y or similar (these are not required when sourcing from file on VOSS and do not work on ERS anyway)
        AppendBuffer.append(cmdAdd)

def appendConfigDotCfg(chainStr=None): # v5 - Appends config commands to config.cfg (before 'end' statement) to be executed after reboot
    global LastError
    if Family != 'VSP Series':
        exitError('appendConfigDotCfg(): only supported with "VSP Series" family type')
    global AppendBuffer
    if chainStr:
        appendBuffer_add(chainStr)
    if Sanity:
        for cmd in AppendBuffer:
            print "SANITY(appended to config.cfg)> {}".format(cmd)
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
                print "Added to config.cfg: {}".format(cmd)
                ConfigHistory.append('[after reboot] ' + cmd)
            LastError = None
            AppendBuffer = []
            return True
    else:
        exitError(resultObj.getError())


#
# CLI warp buffer functions (requires CLI functions)
# v5
import os                           # Used by warpBuffer_execute
WarpBuffer = []

def warpBuffer_add(chainStr): # v1 - Preload WarpBuffer with config or configChains; buffer can then be executed with warpBuffer_execute()
    global WarpBuffer
    cmdList = configChain(chainStr)
    for cmd in cmdList:
        cmdAdd = re.sub(r'\n.+$', '', cmd) # Strip added CR+y or similar (these are not required when sourcing from file on VOSS and do not work on ERS anyway)
        WarpBuffer.append(cmdAdd)

def warpBuffer_execute(chainStr=None, returnCliError=False, msgOnError=None, waitForPrompt=True): # v4 - Appends to existing WarpBuffer and then executes it
    # Same as sendCLI_configChain() but all commands are placed in a script file on the switch and then sourced there
    # Apart from being fast, this approach can be used to make config changes which would otherwise result in the switch becomming unreachable
    # Use of this function assumes that the connected device (VSP) is already in privExec + config mode
    global WarpBuffer
    global LastError
    xmcTftpRoot = '/tftpboot'
    xmcServerIP = emc_vars["serverIP"]
    switchIP = emc_vars["deviceIP"]
    userName = emc_vars["userName"].replace('.', '_')
    tftpCheck = {
        'VSP Series':    'bool://show boot config flags||^flags tftpd true',
        'Summit Series': 'bool://show process tftpd||Ready',
        'ERS Series':    True, # Always enabled
    }
    tftpActivate = {
        'VSP Series':    'boot config flags tftpd',
        'Summit Series': 'start process tftpd',
    }
    tftpDeactivate = {
        'VSP Series':    'no boot config flags tftpd',
        'Summit Series': 'terminate process tftpd graceful',
    }
    tftpExecute = { # XMC server IP (TFTP server), Script file to fetch and execute
        'VSP Series':    'copy "{0}:{1}" /intflash/.script.src -y; source .script.src debug',
        'Summit Series': 'tftp get {0} "{1}" .script.xsf; run script .script.xsf',
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
            ConfigHistory.append(tftpActivate[Family])
        else:
            sendCLI_configCommand(tftpActivate[Family], returnCliError, msgOnError) # Activate TFTP now
        warpBuffer_add(tftpDeactivate[Family])      # Restore TFTP state on completion

    if Sanity:
        for cmd in WarpBuffer:
            print "SANITY(warp)> {}".format(cmd)
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
    success = sendCLI_configChain(tftpExecute[Family].format(xmcServerIP, tftpFileName), returnCliError, msgOnError, waitForPrompt)
    # Clean up by deleting the file from XMC TFTP directory
    os.remove(tftpFilePath)
    debug("warpBuffer - delete of TFTP config file : {}".format(tftpFilePath))

    if not success: # In this case some commands might have executed, before the error; these won't be captured in ConfigHistory
        WarpBuffer = []
        return False
    ConfigHistory.extend(WarpBuffer)
    WarpBuffer = []
    LastError = None
    return True


#
# XMC GraphQl NBI functions via HTTP requests
# v2
import json
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
NbiAuth = None

def nbiSetSession(xmcServerIp=None, xmcTcpPort=8443, xmcUsername='root', xmcPassword='password'): # v1 - Set up HTTP session, to use nbiQuery() & nbiMutation() with external XMC
    global NbiUrl
    global NbiAuth
    if xmcServerIp: # Set the Url
        NbiUrl      = 'https://' + xmcServerIp + ':' + str(xmcTcpPort) + '/nbi/graphql'
        NbiAuth     = (xmcUsername, xmcPassword)
    else:
        NbiUrl = None
        NbiAuth = None

def nbiSessionPost(jsonQuery, returnKeyError=False): # v1 - Internal method, automatically invoked by nbiQuery() & nbiMutation() once nbiSetSession() called
    global LastNbiError
    # Prep the HTTP session data (On XMC we can't seem to be able to re-use a session...)
    session         = requests.Session()
    session.verify  = False
    session.timeout = 10
    session.auth    = NbiAuth
    session.headers.update({'Accept':           'application/json',
                            'Accept-Encoding':  'gzip, deflate, br',
                            'Connection':       'keep-alive',
                            'Content-type':     'application/json',
                            'Cache-Control':    'no-cache',
                            'Pragma':           'no-cache',
                           })
    try:
        response = session.post(NbiUrl, json={'operationName': None, 'query': jsonQuery, 'variables': None })
        response.raise_for_status()
    except requests.exceptions.RequestException as error:
        if returnKeyError: # If we asked to return upon NBI error, then the error message will be held in LastNbiError
            LastNbiError = error
            return None
        abortError("nbiQuery for\n{}".format(jsonQuery), error)
    debug("nbiQuery response server = {}".format(response.headers['server']))
    debug("nbiQuery response server version = {}".format(response.headers['server-version']))
    try:
        jsonResponse = json.loads(response.text)
    except:
        if returnKeyError: # If we asked to return upon NBI error, then the error message will be held in LastNbiError
            LastNbiError = "JSON decoding failed"
            return None
        abortError("nbiQuery for\n{}".format(jsonQuery), "JSON decoding failed")
    debug("nbiSessionPost() jsonResponse = {}".format(jsonResponse))
    return jsonResponse


#
# XMC GraphQl & RESTCONF required functions
# v2
from java.util import LinkedHashMap

def recursionKeySearch(nestedDict, returnKey): # v1 - Used by both nbiQuery() and nbiMutation() and restconfCall()
    for key, value in nestedDict.iteritems():
        if key == returnKey:
            return True, value
    for key, value in nestedDict.iteritems():
        if isinstance(value, (dict, LinkedHashMap)): # XMC Python is Jython where a dict is in fact a java.util.LinkedHashMap
            foundKey, foundValue = recursionKeySearch(value, returnKey)
            if foundKey:
                return True, foundValue
        return [None, None] # If we find nothing

def recursionStatusSearch(nestedDict): # v1 - Used by nbiMutation()
    for key, value in nestedDict.iteritems():
        if key == 'status':
            if 'message' in nestedDict:
                return True, value, nestedDict['message']
            else:
                return True, value, None
    for key, value in nestedDict.iteritems():
        if isinstance(value, (dict, LinkedHashMap)): # XMC Python is Jython where a dict is in fact a java.util.LinkedHashMap
            foundKey, foundValue, foundMsg = recursionStatusSearch(value)
            if foundKey:
                return True, foundValue, foundMsg
        return [None, None, None] # If we find nothing

def replaceKwargs(queryString, kwargs): # v1 - Used by both nbiQuery() and nbiMutation() and restconfCall()
    for key in kwargs:
        replaceValue = str(kwargs[key]).lower() if type(kwargs[key]) == bool else str(kwargs[key])
        queryString = queryString.replace('<'+key+'>', replaceValue)
    return queryString


#
# XMC GraphQl NBI functions
# v14
LastNbiError = None
NbiUrl = None

def nbiQuery(jsonQueryDict, debugKey=None, returnKeyError=False, **kwargs): # v7 - Makes a GraphQl query of XMC NBI; if returnKey provided returns that key value, else return whole response
    global LastNbiError
    jsonQuery = replaceKwargs(jsonQueryDict['json'], kwargs)
    returnKey = jsonQueryDict['key'] if 'key' in jsonQueryDict else None
    debug("NBI Query:\n{}\n".format(jsonQuery))
    response = nbiSessionPost(jsonQuery, returnKeyError) if NbiUrl else emc_nbi.query(jsonQuery)
    debug("nbiQuery response = {}".format(response))
    if response == None: # Should only happen from nbiSessionPost if returnKeyError=True
        return None
    if 'errors' in response: # Query response contains errors
        if returnKeyError: # If we asked to return upon NBI error, then the error message will be held in LastNbiError
            LastNbiError = response['errors'][0].message
            return None
        abortError("nbiQuery for\n{}".format(jsonQuery), response['errors'][0].message)
    LastNbiError = None

    if returnKey: # If a specific key requested, we find it
        foundKey, returnValue = recursionKeySearch(response, returnKey)
        if foundKey:
            if Debug:
                if debugKey: debug("{} = {}".format(debugKey, returnValue))
                else: debug("nbiQuery {} = {}".format(returnKey, returnValue))
            return returnValue
        if returnKeyError:
            return None
        # If requested key not found, raise error
        abortError("nbiQuery for\n{}".format(jsonQuery), 'Key "{}" was not found in query response'.format(returnKey))

    # Else, return the full response
    if Debug:
        if debugKey: debug("{} = {}".format(debugKey, response))
        else: debug("nbiQuery response = {}".format(response))
    return response

def nbiMutation(jsonQueryDict, returnKeyError=False, debugKey=None, **kwargs): # v7 - Makes a GraphQl mutation query of XMC NBI; returns true on success
    global LastNbiError
    jsonQuery = replaceKwargs(jsonQueryDict['json'], kwargs)
    returnKey = jsonQueryDict['key'] if 'key' in jsonQueryDict else None
    if Sanity:
        print "SANITY - NBI Mutation:\n{}\n".format(jsonQuery)
        LastNbiError = None
        return True
    print "NBI Mutation Query:\n{}\n".format(jsonQuery)
    response = nbiSessionPost(jsonQuery, returnKeyError) if NbiUrl else emc_nbi.query(jsonQuery)
    debug("nbiQuery response = {}".format(response))
    if 'errors' in response: # Query response contains errors
        if returnKeyError: # If we asked to return upon NBI error, then the error message will be held in LastNbiError
            LastNbiError = response['errors'][0].message
            return None
        abortError("nbiQuery for\n{}".format(jsonQuery), response['errors'][0].message)

    foundKey, returnStatus, returnMessage = recursionStatusSearch(response)
    if foundKey:
        debug("nbiMutation status = {} / message = {}".format(returnStatus, returnMessage))
    elif not returnKeyError:
        # If status key not found, raise error
        abortError("nbiMutation for\n{}".format(jsonQuery), 'Key "status" was not found in query response')

    if returnStatus == "SUCCESS":
        LastNbiError = None
        if returnKey: # If a specific key requested, we find it
            foundKey, returnValue = recursionKeySearch(response, returnKey)
            if foundKey:
                if Debug:
                    if debugKey: debug("{} = {}".format(debugKey, returnValue))
                    else: debug("nbiQuery {} = {}".format(returnKey, returnValue))
                return returnValue
            if returnKeyError:
                return None
            # If requested key not found, raise error
            abortError("nbiMutation for\n{}".format(jsonQuery), 'Key "{}" was not found in mutation response'.format(returnKey))
        return True
    else:
        LastNbiError = returnMessage
        return False


#
# RESTCONF functions
# v1
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
RestconfAuthToken = None
RestconfUrl = None
LastRestconfError = None
HTTP_RESONSE_OK = {
    'GET':      200,
    'PUT':      201,
    'POST':     201,
    'PATCH':    200,
    'DELETE':   204,
}
RestConfFamilyDefaults = {
    'VSP Series': {
        'tcpPort'  : 8080,
        'protocol' : 'http',
        'restPath' : '/rest/restconf/data',
    },
    'Summit Series': {
        'tcpPort'  : None,
        'protocol' : 'http',
        'restPath' : '/rest/restconf/data',
    },
}


def restconfSession(authToken=None, body=None): # v1 - On XMC we don't seem to be able to re-use a session... so we spin a new one every time...
    session = requests.Session()
    session.verify  = False
    session.timeout = 2
    session.headers.update({'Accept':           'application/json',
                            'Connection':       'keep-alive',
                            'Cache-Control':    'no-cache',
                            'Pragma':           'no-cache',
                           })
    if authToken:
        session.headers.update({ 'X-Auth-Token': authToken })
    if body:
        session.headers.update({ 'Content-Type': 'application/json' })
    return session


def restconfStart(host=None, tcpPort=None, protocol=None, username=None, password=None, restPath=None): # v1 - Set up RESTCONF session
    global RestconfAuthToken
    global RestconfUrl
    if not host:
        if not emc_vars['deviceIP']:
            exitError("restconfStart() no host provided and emc_vars['deviceIP'] is not set either")
        host = emc_vars['deviceIP']
        if not tcpPort and not protocol and not Family:
            exitError("restconfStart() cannot use emc_vars['deviceIP'] as host unless Family is set; call setFamily() first")
        if not tcpPort:
            tcpPort = RestConfFamilyDefaults[Family]['tcpPort']
        if not protocol:
            protocol = RestConfFamilyDefaults[Family]['protocol']
        if not restPath:
            restPath = RestConfFamilyDefaults[Family]['restPath']
        if not username:
            try:
                profileName = nbiQuery(NBI_Query['getDeviceAdminProfile'], debugKey='profileName', IP=host)
                authCred = nbiQuery(NBI_Query['getAdminProfileCreds'], debugKey='authCred', PROFILE=profileName)
                username = authCred['userName']
                password = authCred['loginPassword']
            except:
                if Family in RestConfFamilyDefaults:
                    username = RestConfFamilyDefaults[Family]['username']
                    password = RestConfFamilyDefaults[Family]['password']
                else:
                    exitError("restconfStart() need to be able to execute nbiQuery() to derive device credentials")

    if host: # Create the HTTP session
        if not restPath:
            restPath = '/rest/restconf/data' # Default path, normally provided from /.well-known/host-meta
        if tcpPort and tcpPort != 80:
            loginUrl = "{}://{}:{}/auth/token".format(protocol, host, tcpPort)
        else:
            loginUrl = "{}://{}/auth/token".format(protocol, host)
        if password:
            body     = '{"username": "%s", "password" : "%s" }' % (username, password)
        else: # EXOS with default admin account only...
            body     = '{"username": "%s", "password" : "" }' % (username)
        session = restconfSession(body=True)
        try:
            response = session.post(loginUrl, body)
            print "RESTCONF call: POST {}".format(loginUrl)
            debug("{}".format(body))
            response.raise_for_status()
        except requests.exceptions.RequestException as error:
            abortError("RESTCONF {}: ".format(loginUrl), error)

        # Extract the token and store it in global variable
        debug("RESTCONF response data = {}".format(response.text))
        RestconfAuthToken = json.loads(response.text)['token']
        debug("restconfSetSession(): extracted token {}".format(RestconfAuthToken))
        # Set the RESTCONF url and also store it in global variable
        if tcpPort:
            RestconfUrl = "{}://{}:{}{}/".format(protocol, host, tcpPort, restPath)
        else:
            RestconfUrl = "{}://{}{}/".format(protocol, host, restPath)


def restconfCall(restconfDict, returnKeyError=False, debugKey=None, **kwargs): # v2 - Makes a RESTCONF call
    if not RestconfAuthToken or not RestconfUrl:
        exitError("restconfCall() cannot be called without first setting up a RESTCONF session via restconfStart()")
    global LastRestconfError
    httpCall = restconfDict['http']
    restUri = replaceKwargs(restconfDict['uri'], kwargs)
    queryStr = restconfDict['query'] if 'query' in restconfDict else None
    jsonStr  = replaceKwargs(restconfDict['body'], kwargs) if 'body' in restconfDict else None
    if queryStr:
        restUri += '?' + queryStr
    jsonBody = json.loads(jsonStr) if jsonStr else None
    returnKey = restconfDict['key'] if 'key' in restconfDict else None
    if Sanity and httpCall.lower() != 'get':
        print "SANITY - RESTCONF call: {}\n{}".format(restUri ,json.dumps(jsonBody, indent=4, sort_keys=True))
        LastRestconfError = None
        return []

    # Display info about the RESTCONF call we are about to perform
    if jsonBody:
        print "\nRESTCONF call: {} {}{}\n{}".format(httpCall, RestconfUrl, restUri ,json.dumps(jsonBody, indent=4, sort_keys=True))
    else:
        print "\nRESTCONF call: {} {}{}".format(httpCall, RestconfUrl, restUri)

    # Make the RESTCONF call
    session = restconfSession(RestconfAuthToken, jsonBody)
    sessionHttpMethod = getattr(session, httpCall.lower())
    response = sessionHttpMethod(RestconfUrl + restUri, json=jsonBody)

    debug("RESTCONF response = {}".format(response))
    debug("RESTCONF response reason = {}".format(response.reason))
    debug("RESTCONF response data = {}".format(response.text))

    if response.status_code == HTTP_RESONSE_OK[httpCall.upper()]:
        LastRestconfError = None
        responseDict = json.loads(response.text) if response.text else True
        if returnKey: # If a specific key requested, we find it
            foundKey, returnValue = recursionKeySearch(responseDict, returnKey)
            if foundKey:
                if Debug:
                    if debugKey: debug("RESTCONF returnKey {} = {}".format(debugKey, returnValue))
                    else: debug("RESTCONF returnKey {} = {}".format(returnKey, returnValue))
                return returnValue
            if returnKeyError:
                return None
            # If requested key not found, raise error
            abortError("RESTCONF {} for {}".format(restconfDict['http'], restUri), 'Key "{}" was not found in response data'.format(returnKey))

        # Else, return the full response
        if Debug:
            if debugKey: debug("RESTCONF return {} = {}".format(debugKey, responseDict))
            else: debug("RESTCONF return data = {}".format(responseDict))
        return responseDict
    else:
        LastRestconfError = response.reason + ":" + response.text
        return None


#
# Port processing functions
# v6
RegexPort = re.compile('^(?:[1-9]\d{0,2}[/:])?\d+(?:[/:]\d)?$')
RegexPortRange = re.compile('^(?:([1-9]\d{0,2})([/:]))?(\d+)(?:[/:](\d))?-(?:([1-9]\d{0,2})[/:])?(\d+)(?:[/:](\d))?$')
RegexStarRange = re.compile('^([1-9]\d{0,2})(:)\*$') # XOS only
SlotPortRange = None # Gets set to dict by getSlotPortRanges()

def portValue(port): # v1 - Function to pass to sorted(key) to sort port lists
    slotPort = re.split('[/:]', port)
    if len(slotPort) == 3: # slot/port/chan format
        idx = int(slotPort[0])*400 + int(slotPort[1])*4 + int(slotPort[2])
    elif len(slotPort) == 2: # slot/port format
        idx = int(slotPort[0])*400 + int(slotPort[1])*4
    else: # standalone port (no slot)
        idx = int(slotPort[0])*4
    return idx

def getSlotPortRanges(): # v1 - Populates the SlotPortRange dict
    global SlotPortRange
    slotCommand = {'Summit Series': 'dict://show slot||^Slot-(\d+) +\S+ +\S+ +\S+ +(\d+)'} # Only XOS supported
    if Family not in slotCommand:
        SlotPortRange = {}
        return
    SlotPortRange = sendCLI_showRegex(slotCommand[Family])
    debug("getSlotPortRanges = {}".format(SlotPortRange))

def generatePortList(portStr, debugKey=None): # v3 - Given a port list/range, validates it and returns an ordered port list with no duplicates (can also be used for VLAN-id ranges)
    # This version of this function will not handle port ranges which span slots
    debug("generatePortList IN = {}".format(portStr))
    portDict = {} # Use a dict, will ensure no port duplicate keys
    for port in portStr.split(','):
        port = re.sub(r'^[\s\(]+', '', port) # Remove leading spaces  [ or '(' ]
        port = re.sub(r'[\s\)]+$', '', port) # Remove trailing spaces [ or ')' => XMC bug on ERS standalone units]
        if not len(port): # Skip empty string
            continue
        rangeMatch = RegexPortRange.match(port)
        starMatch = RegexStarRange.match(port)
        if rangeMatch: # We have a range of ports
            startSlot = rangeMatch.group(1)
            separator = rangeMatch.group(2)
            startPort = int(rangeMatch.group(3))
            startChan = int(rangeMatch.group(4)) if rangeMatch.group(4) else None
            endSlot = rangeMatch.group(5)
            endPort = int(rangeMatch.group(6))
            endChan = int(rangeMatch.group(7)) if rangeMatch.group(4) else None
            if endSlot and startSlot != endSlot:
                print "ERROR! generatePortList no support for ranges spanning slots: {}".format(port)
            elif (startChan or endChan) and endPort and startPort != endPort:
                print "ERROR! generatePortList no support for ranges spanning channelized ports: {}".format(port)
            elif not (startChan or endChan) and startPort >= endPort:
                print "ERROR! generatePortList invalid range: {}".format(port)
            elif (startChan or endChan) and startChan >= endChan:
                print "ERROR! generatePortList invalid range: {}".format(port)
            else: # We are good
                if startChan:
                    for portCount in range(startChan, endChan + 1):
                        portDict[startSlot + separator + str(startPort) + separator + str(portCount)] = 1
                else:
                    for portCount in range(startPort, endPort + 1):
                        if startSlot: # slot-based range
                            portDict[startSlot + separator + str(portCount)] = 1
                        else: # simple port range (no slot info)
                            portDict[str(portCount)] = 1
        elif starMatch: # We have a slot/* range
            slot = starMatch.group(1)
            separator = starMatch.group(2)
            if SlotPortRange == None: # Structure not populated
                getSlotPortRanges()
            if SlotPortRange:
                if slot in SlotPortRange:
                    for portCount in range(1, int(SlotPortRange[slot]) + 1):
                        portDict[slot + separator + str(portCount)] = 1
                else:
                    print "Warning: no range for slot {}; skipping: {}".format(slot, port)
            else:
                print "Warning: generatePortList skipping star range as not supported on this switch type: {}".format(port)
        elif RegexPort.match(port): # Port is in valid format
            portDict[port] = 1
        else: # Port is in an invalid format; don't add to dict, print an error message, don't raise exception 
            print "Warning: generatePortList skipping unexpected port format: {}".format(port)

    # Sort and return the list as a comma separated string
    portList = sorted(portDict, key=portValue)

    if Debug:
        if debugKey: debug("{} = {}".format(debugKey, portList))
        else: debug("generatePortList OUT = {}".format(portList))
    return portList

def generatePortRange(portList, debugKey=None): # v3 - Given a list of ports, generates a compacted port list/range string for use on CLI commands
    # Ported from acli.pl; this version of this function only compacts ranges within same slot
    debug("generatePortRange IN = {}".format(portList))
    rangeMode = {'VSP Series': 2, 'ERS Series': 1, 'Summit Series': 1}
    elementList = []
    elementBuild = None
    currentType = None
    currentSlot = None
    currentPort = None
    currentChan = None
    rangeLast = None

    # First off, sort the list
    portList = sorted(portList, key=portValue)
    for port in portList:
        slotPort = re.split("([/:])", port) # Split on '/' (ERS/VSP) or ':'(XOS)
        # slotPort[0] = slot / slotPort[1] = separator ('/' or ':') / slotPort[2] = port / slotPort[4] = channel
        if len(slotPort) == 5: # slot/port/chan
            if elementBuild:
                if currentType == 's/p' and slotPort[0] == currentSlot and slotPort[2] == currentPort and currentChan and slotPort[4] == str(int(currentChan)+1):
                    currentChan = slotPort[4]
                    if rangeMode[Family] == 1:
                        rangeLast = currentChan
                    else: # rangeMode = 2
                        rangeLast = currentSlot + slotPort[1] + currentPort + slotPort[1] + currentChan
                    continue
                else: # Range complete
                    if rangeLast:
                        elementBuild += '-' + rangeLast
                    elementList.append(elementBuild)
                    elementBuild = None
                    rangeLast = None
                    # Fall through below
            currentType = 's/p'
            currentSlot = slotPort[0]
            currentPort = slotPort[2]
            currentChan = slotPort[4]
            elementBuild = port

        if len(slotPort) == 3: # slot/port
            if elementBuild:
                if currentType == 's/p' and slotPort[0] == currentSlot and slotPort[2] == str(int(currentPort)+1) and not currentChan:
                    currentPort = slotPort[2]
                    if rangeMode[Family] == 1:
                        rangeLast = currentPort
                    else: # rangeMode = 2
                        rangeLast = currentSlot + slotPort[1] + currentPort
                    continue
                else: # Range complete
                    if rangeLast:
                        elementBuild += '-' + rangeLast
                    elementList.append(elementBuild)
                    elementBuild = None
                    rangeLast = None
                    # Fall through below
            currentType = 's/p'
            currentSlot = slotPort[0]
            currentPort = slotPort[2]
            currentChan = None
            elementBuild = port

        if len(slotPort) == 1: # simple port (no slot)
            if elementBuild:
                if currentType == 'p' and port == str(int(currentPort)+1):
                    currentPort = port
                    rangeLast = currentPort
                    continue
                else: # Range complete
                    if rangeLast:
                        elementBuild += '-' + rangeLast
                    elementList.append(elementBuild)
                    elementBuild = None
                    rangeLast = None
                    # Fall through below
            currentType = 'p'
            currentPort = port
            elementBuild = port

    if elementBuild: # Close off last element we were holding
        if rangeLast:
            elementBuild += '-' + rangeLast
        elementList.append(elementBuild)

    portStr = ','.join(elementList)
    if Debug:
        if debugKey: debug("{} = {}".format(debugKey, portStr))
        else: debug("generatePortRange OUT = {}".format(portStr))
    return portStr


#
# FIGW CLI functions (requires VOSS 8.4.2 or later)(requires CLI functions)
# v6

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


#
# IP address processing functions
# v5
import re                           # Used by maskToNumber

def ipToNumber(dottedDecimalStr): # v1 - Method to convert an IP/Mask dotted decimal address into a long number; can also use for checking validity of IP addresses
    try: # bytearray ensures that IP bytes are valid (1-255)
        ipByte = list(bytearray([int(byte) for byte in dottedDecimalStr.split('.')]))
    except:
        return None
    if len(ipByte) != 4:
        return None
    debug("ipByte = {}".format(ipByte))
    ipNumber = (ipByte[0]<<24) + (ipByte[1]<<16) + (ipByte[2]<<8) + ipByte[3]
    debug("dottedDecimalStr {} = ipNumber {}".format(dottedDecimalStr, hex(ipNumber)))
    return ipNumber

def numberToIp(ipNumber): # v1 - Method to convert a long number into an IP/Mask dotted decimal address
    dottedDecimalStr = '.'.join( [ str(ipNumber >> (i<<3) & 0xFF) for i in range(4)[::-1] ] )
    debug("ipNumber {} = dottedDecimalStr {}".format(hex(ipNumber), dottedDecimalStr))
    return dottedDecimalStr

def maskToNumber(mask): # v1 - Method to convert a mask (dotted decimal or Cidr number) into a long number
    if isinstance(mask, int) or re.match(r'^\d+$', mask): # Mask as number
        if int(mask) > 0 and int(mask) <= 32:
            maskNumber = (2**32-1) ^ (2**(32-int(mask))-1)
        else:
            maskNumber = None
    else:
        maskNumber = ipToNumber(mask)
    if maskNumber:
        debug("maskNumber = {}".format(hex(maskNumber)))
    return maskNumber

def subnetMask(ip, mask): # v1 - Return the IP subnet and Mask in dotted decimal and cidr formats for the provided IP address and mask
    ipNumber = ipToNumber(ip)
    maskNumber = maskToNumber(mask)
    subnetNumber = ipNumber & maskNumber
    ipSubnet = numberToIp(subnetNumber)
    ipDottedMask = numberToIp(maskNumber)
    ipCidrMask = bin(maskNumber).count('1')
    debug("ipSubnet = {} / ipDottedMask = {} / ipCidrMask = {}".format(ipSubnet, ipDottedMask, ipCidrMask))
    return ipSubnet, ipDottedMask, ipCidrMask

def ipGateway(ip, mask, gw): # v1 - Return the gateway IP address, as first or last IP in subnet, based on own IP/mask
    ipNumber = ipToNumber(ip)
    maskNumber = maskToNumber(mask)
    subnetNumber = ipNumber & maskNumber
    if gw == 'first':
        gwNumber = subnetNumber + 1
        ip1numb = gwNumber + 1
        ip2numb = gwNumber + 2
    elif gw == 'last':
        gwNumber = subnetNumber + 2**(32-int(mask)) - 2
        ip1numb = gwNumber - 2
        ip2numb = gwNumber - 1
    else: # Error condition
        exitError('ipGateway(): invalid gw type {}'.format(gw))
    debug("gwNumber = {} / ip1numb = {} / ip2numb = {}".format(hex(gwNumber), hex(ip1numb), hex(ip2numb)))
    gatewayIP = numberToIp(gwNumber)
    ip1 = numberToIp(ip1numb)
    ip2 = numberToIp(ip2numb)
    debug("gatewayIP = {} / ip1 = {} / ip2 = {}".format(gatewayIP, ip1, ip2))
    return gatewayIP, ip1, ip2


#
# Save Config functions (requires CLI functions)
# v4
import re                           # Used by vossSaveConfigRetry
import time                         # Used by vossSaveConfigRetry & vossWaitNoUsersConnected

def vossSaveConfigRetry(waitTime=10, retries=3, returnCliError=False, aggressive=False): # v3 - On VOSS a save config can fail, if another CLI session is doing "show run", so we need to be able to backoff and retry
    # Only supported for family = 'VSP Series'
    global LastError
    cmd = 'save config'
    if Sanity:
        print "SANITY> {}".format(cmd)
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
                    print "==> Save config did not happen. Getting aggressive... killing all other CLI sessions..."
                    cliSessionsList = sendCLI_showRegex('list://show users||^(Telnet|SSH)(\d+) +\S+ +\S+ +[\d\.\:]+ *$', 'cliSessionsList')
                    for sessionTuple in cliSessionsList:
                        sendCLI_showCommand('clear {} {}'.format(sessionTuple[0], sessionTuple[1]), returnCliError=True)
                else: # Wait and try again
                    if retryCount > retries:
                        print "==> Save config did not happen. Exausted retries..."
                    else:
                        print "==> Save config did not happen. Waiting {} seconds before retry...".format(waitTime)
                        time.sleep(waitTime)
                        print "==> Retry {}\n".format(retryCount)
        else:
            exitError(resultObj.getError())

    if returnCliError: # If we asked to return upon CLI error, then the error message will be held in LastError
        LastError = outputStr
        return False
    exitError(outputStr)

def vossWaitNoUsersConnected(waitTime=10, retries=3, aggressive=False): # v2 - Waits until no other Telnet/SSH connections to VSP switch
    # Only supported for family = 'VSP Series'
    retryCount = 0
    while retryCount <= retries:
        if sendCLI_showRegex('bool://show users||^(?:Telnet|SSH).+\d *$'):
            retryCount += 1
            if retries > 0:
                if aggressive and retryCount == retries:
                    # We become aggressive, we kill all other SSH/Telnet sessions
                    print "==> Some users are still connected. Getting aggressive... killing all other CLI sessions..."
                    cliSessionsList = sendCLI_showRegex('list://show users||^(Telnet|SSH)(\d+) +\S+ +\S+ +[\d\.\:]+ *$', 'cliSessionsList')
                    for sessionTuple in cliSessionsList:
                        sendCLI_showCommand('clear {} {}'.format(sessionTuple[0], sessionTuple[1]), returnCliError=True)
                else: # Wait and try again
                    if retryCount > retries:
                        print "==> Some users are still connected. Exausted retries..."
                        return False
                    else:
                        print "==> Some users are still connected. Waiting {} seconds before retry...".format(waitTime)
                        time.sleep(waitTime)
                        print "==> Retry {}\n".format(retryCount)
        else:
            return True


#
# Read Custom Site Variables (requires nbi functions & getDeviceSiteVariables + getSiteVariables)
# v8
import re

def readSiteCustomVariables(deviceIp): # v4 - Obtains a dict of custom site variables starting from Site of deviceIp
    siteVariablesHash = nbiQuery(NBI_Query['getDeviceSiteVariables'], debugKey='siteVariablesHash', returnKeyError=True, IP=deviceIp)
    debug("readSiteCustomVariables customVariables = {}".format(siteVariablesHash))
    # Sample of what we should get back
    # "device": {
    #   "sitePath": "/World/PoC/Zero Touch Fabric/Access",
    #   "customVariables": [
    #     {
    #       "globalAttribute": true,  <== these we accept only if a site-specific version of same var does not exist
    #       "name": "VoiceVlan",
    #       "scopeCategory": "SITE",  <== we only look at "SITE" ones
    #       "value": "200",
    #       "valueType": "NUMBER"
    #     },
    #     {
    #       "globalAttribute": false,  <== these we prefer as site-specific
    #       "name": "nacLocation",
    #       "scopeCategory": "SITE",   <== we only look at "SITE" ones
    #       "value": "Building1",
    #       "valueType": "STRING"
    #     }
    #   ]
    # }
    # Or we get None
    siteVarDict = {}

    if siteVariablesHash:
        def value(varHash): # Map valid null values to empty string
            if varHash["valueType"] == "NUMBER" and varHash["value"] == 0:
                return ""
            if varHash["valueType"] == "STRING" and (varHash["value"] == "0" or varHash["value"] == "''" or varHash["value"] == '""'):
                return ""
            if varHash["valueType"] == "IP" and varHash["value"] == "0.0.0.0":
                return ""
            if varHash["valueType"] == "MAC_ADDRESS" and varHash["value"] == "00:00:00:00:00:00":
                return ""
            # Else we take the value
            return varHash["value"]

        sitePath = siteVarDict['__PATH__'] = siteVariablesHash["sitePath"]
        # First pass, only read site non-global variables, as we prefer these
        debug("First pass, site local variables:")
        for varHash in siteVariablesHash["customVariables"]:
            if varHash["globalAttribute"] or varHash["scopeCategory"] != 'SITE':
                continue # Skip these entries
            siteVarDict[varHash["name"]] = value(varHash)
            debug("---> {} = {}".format(varHash["name"], siteVarDict[varHash["name"]]))

        # Next, parse all the parent sites, for non-global variables
        debug("Second pass, parent site local variables:")
        sitePath = re.sub(r'/[^/]+$', '', sitePath) # Nibble away at the site path to work up parent sites
        while sitePath:
            debug("-> {}".format(sitePath))
            siteVariablesHash = nbiQuery(NBI_Query['getSiteVariables'], debugKey='siteVariablesHash', returnKeyError=True, SITE=sitePath)
            # Sample of what we should get back
            # "siteByLocation": {
            #   "customVariables": [
            #     {
            #       "globalAttribute": true,  <== these we accept only if a site-specific version of same var does not exist
            #       "name": "VoiceVlan",
            #       "scopeCategory": "SITE",  <== we only look at "SITE" ones
            #       "value": "200",
            #       "valueType": "NUMBER"
            #     },
            #   ]
            # }
            # Or we get None
            for varHash in siteVariablesHash["customVariables"]:
                if varHash["globalAttribute"] or varHash["scopeCategory"] != 'SITE' or varHash["name"] in siteVarDict:
                    continue # Skip these entries
                siteVarDict[varHash["name"]] = value(varHash)
                debug("---> {} = {}".format(varHash["name"], siteVarDict[varHash["name"]]))
            sitePath = re.sub(r'/[^/]+$', '', sitePath) # Nibble away at the site path to work up parent sites

        # Thrid pass, read global variables but only if a site specific one was not already read in 1st pass
        debug("Third pass, global variables:")
        for varHash in siteVariablesHash["customVariables"]:
            if varHash["scopeCategory"] != 'SITE' or varHash["name"] in siteVarDict:
                continue # Skip these entries
            siteVarDict[varHash["name"]] = value(varHash)
            debug("---> {} = {}".format(varHash["name"], siteVarDict[varHash["name"]]))

    debug("readSiteCustomVariables siteVarDict = {}".format(siteVarDict))
    return siteVarDict

def siteVarLookup(inputStr, siteVarDict): # v4 - Replaces embedded ${<site-custom-variables>} in the input string
    siteVarsUsed = {x.group(1):1 for x in re.finditer(r'\$\{([\w -]+)\}', inputStr)}
    outputStr = inputStr
    if siteVarsUsed:
        debug("siteVarLookup siteVarsUsed = {}".format(siteVarsUsed))
        missingVarList = [x for x in siteVarsUsed if x not in siteVarDict]
        if missingVarList:
            exitError("siteVarLookup: the following variables were not found in Site Path {} nor in its parent sites nor in global variables:\n{}".format(siteVarDict['__PATH__'], missingVarList))
        for siteVar in siteVarsUsed:
            outputStr = re.sub(r'\$\{' + siteVar + '\}', siteVarDict[siteVar], outputStr)
        if "\n" in inputStr:
            debug("siteVarLookup input: {}\n{}\n".format(type(inputStr), inputStr))
            debug("siteVarLookup output: {}\n{}\n".format(type(outputStr), outputStr))
        else:
            debug("siteVarLookup {} {} =  {} {}".format(type(inputStr), inputStr, type(outputStr), outputStr))
    return outputStr


#
# CSV data input
# v9
import os.path
import csv
import json
import re
import io

def readCsvToDict(csvFilePath, lookup=None, delimiter=','): # v3 - Read CSV data file, return dict with data
    # It is expected that the 1st CSV row has the column value keys
    # And that the index to data are the values in column 0
    # Row0 Column0 is returned as 2nd value
    # Example CSV:
    #    ip,      var1, var2
    #    1.1.1.1, 11,   21
    #    2.2.2.2, 12,   22
    # Returns csvVarDict:
    # {
    #    "1.1.1.1": { "var1": 11, "var2": 21 },
    #    "2.2.2.2": { "var1": 12, "var2": 22 }
    #    "__PATH__": csvFilePath
    #    "__INDEX__": "ip"
    # }

    # First check existence of the input csv file
    if not os.path.exists(csvFilePath):
        exitError("readCsvToDict: CSV file {} not found!".format(csvFilePath))
    # Read in the CSV file
    csvVarDict = {}
    with io.open(csvFilePath, mode='r', encoding='utf-8-sig') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=delimiter)
        firstRow = True
        for row in csv_reader:
            if len(row) > 0: # Skip empty lines
                if firstRow:
                    indexKey = re.sub(r'^\\ufeff', '', row.pop(0)) 
                    valueKeys = map(str.strip, row)
                    firstRow = False
                else:
                    key = row.pop(0)
                    if not lookup or key == lookup:
                        csvVarDict[key] = dict(zip(valueKeys, map(str.strip, row)))
                        csvVarDict['__LOOKUP__'] = key
    csvVarDict['__INDEX__'] = indexKey
    csvVarDict['__PATH__'] = csvFilePath
    debug("readCsvToDict() csvVarDict =\n{}".format(json.dumps(csvVarDict, indent=4, sort_keys=True)))
    return csvVarDict

def csvVarLookup(inputStr, csvVarDict, lookup): # v6 - Replaces embedded $<csv-variables> or $(csv-variables) in the input string
    csvVarsUsed = {x.group(1):1 for x in list(re.finditer(r'\$<([\w -]+)>', inputStr)) + list(re.finditer(r'\$\(([\w -]+)\)', inputStr))}
    outputStr = inputStr
    if csvVarsUsed:
        debug("csvVarLookup csvVarsUsed = {}".format(csvVarsUsed))
        missingVarList = [x for x in csvVarsUsed if lookup not in csvVarDict or x not in csvVarDict[lookup]]
        if missingVarList:
            if csvVarDict:
                exitError("csvVarLookup: the following variables were not found in the CSV file {} for lookup {}:\n{}".format(csvVarDict['__PATH__'], lookup, missingVarList))
            else:
                exitError("csvVarLookup: no CSV file provided but the following variables were found requiring CSV lookup {}:\n{}".format(lookup, missingVarList))
        for csvVar in csvVarsUsed:
            outputStr = re.sub(r'(?:\$<' + csvVar + '>|\$\(' + csvVar + '\))', csvVarDict[lookup][csvVar], outputStr)
        if "\n" in inputStr:
            debug("csvVarLookup input: {}\n{}\n".format(type(inputStr), inputStr))
            debug("csvVarLookup output: {}\n{}\n".format(type(outputStr), outputStr))
        else:
            debug("csvVarLookup {} {} =  {} {}".format(type(inputStr), inputStr, type(outputStr), outputStr))
    return outputStr


#
# Device UserData1-4 input (requires nbi functions & getDeviceUserData)
# v2

def readDeviceUserData(deviceIp): # v1 - Read in device UserData1-4 fields
    # Fields can be set as "parameter = 10" and the retained value will be "10"
    userDataDict = nbiQuery(NBI_Query['getDeviceUserData'], IP=deviceIp) # Get the device user data 1-4
    udVarList = [None] * 4  # Create list of 4, unset values
    for ud in userDataDict:
        if userDataDict[ud]:
            udVarList[int(ud[-1])-1] = str(userDataDict[ud].split("=")[-1].strip()) # We want str values, not unicode
    debug("readDeviceUserData udVarList = {}".format(udVarList))
    return udVarList

def udVarLookup(inputStr, udVarList): # v1 - Replaces embedded $UD<1-4> variables in the input string
    udVarsUsed = {x.group(1):1 for x in re.finditer(r'\$UD([1-4])', inputStr)}
    outputStr = inputStr
    if udVarsUsed:
        debug("udVarLookup udVarsUsed = {}".format(udVarsUsed))
        missingVarList = [x for x in udVarsUsed if not udVarList[int(x)-1]]
        if missingVarList:
            exitError("udVarLookup: the following variables were not found in the device UserData1-4 fields: {}".format(['UD' + x for x in missingVarList]))
        for udVar in udVarsUsed:
            outputStr = re.sub(r'\$UD' + udVar, udVarList[int(udVar)-1], outputStr)
        if "\n" in inputStr:
            debug("udVarLookup input: {}\n{}\n".format(type(inputStr), inputStr))
            debug("udVarLookup output: {}\n{}\n".format(type(outputStr), outputStr))
        else:
            debug("udVarLookup {} {} =  {} {}".format(type(inputStr), inputStr, type(outputStr), outputStr))
    return outputStr


#
# Linux shell functions (requires CLI functions)
# v3
import re
import os
import subprocess

def xmcLinuxExecute(cmd): # v1 - Execute a command on XMC for which no output expected
    debug("xmcLinuxExecute about to execute : {}".format(cmd))
    try:
        os.system(cmd)
        return True
    except Exception as e: # Expect OSError
        print "{}: {}".format(type(e).__name__, str(e))
        print "Error executing '{}' on XMC shell".format(cmd)
        return False

def xmcLinuxCommand(cmdRegexStr, debugKey=None): # v2 - Execute a command on XMC and recover the output
    mode, cmdList, regex = parseRegexInput(cmdRegexStr)
    cmd = cmdList[0] # We only support single shell command syntax for now
    cmdList = cmd.split(' ')
    try:
        emc_vars
    except: # If not running on XMC Jython...I develop on my Windows laptop...
        cmdList[0] += '.bat'
    debug("xmcLinuxCommand about to execute : {}".format(cmd))
    try:
        outputStr = subprocess.check_output(cmdList)
    except Exception as e: # Expect OSError
        print "{}: {}".format(type(e).__name__, str(e))
        print "Error executing '{}' on XMC shell".format(cmd)
        return
    data = re.findall(regex, outputStr, re.MULTILINE)
    # Format we return data in depends on what '<type>://' was pre-pended to the cmd & regex
    value = formatOutputData(data, mode)
    if Debug:
        if debugKey: debug("{} = {}".format(debugKey, value))
        else: debug("xmcLinuxCommand OUT = {}".format(value))
    return value


#
# Syslog functions
# v1
import socket                       # Used by addXmcSyslogEvent

def addXmcSyslogEvent(severity, message, ip=None): # v1 - Adds a syslog event to XMC (only needed for Scripts)
    severityHash = {'emerg': 0, 'alert': 1, 'crit': 2, 'err': 3, 'warning': 4, 'notice': 5, 'info': 6, 'debug': 7}
    severityLevel = severityHash[severity] if severity in severityHash else 6
    session = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    session.connect(('127.0.0.1', 514))
    if ip:
        session.send("<{}> XMC Script {} / Device: {} / {}".format(severityLevel,scriptName(),ip,message))
    else:
        session.send("<{}> XMC Script {} / {}".format(severityLevel,scriptName(),ip,message))
    session.close()


#
# Workflow execution functions (requires nbi functions & getWorkflowIds + executeWorkflow)
# v4
import re
import json

def getWorkflowId(worflowPathName): # v1 - Returns the workflow id, or None if it does not exist or cannot be found
                                    # Syntax: workflowExists("Provisioning/Onboard VSP")
    # Get the name and category separately
    worflowCategory, worflowName = worflowPathName.split('/') 
    debug("getWorkflowId() worflowCategory = {} / worflowName = {}".format(worflowCategory, worflowName))
    # Get full list of workflows and their ids
    workflowsList = nbiQuery(NBI_Query['getWorkflowIds'], debugKey='workflowsList', returnKeyError=True)
    if LastNbiError:
        print "getWorkflowId() unable to extract workflowList; query:\n{}\nFailed with: {}".format(NBI_Query['getWorkflowIds'], LastNbiError)
        return None
    if not workflowsList:
        print "getWorkflowId() unable to extract workflowList; query:\n{}\nReturned None".format(NBI_Query['getWorkflowIds'])
        return None
    # Make a Dict of workflow names (keys) for workflow ids (values)
    worflowId = None
    workflowPath = None
    for wrkfl in workflowsList:
        if worflowCategory == wrkfl['category'] and worflowName == wrkfl['name']:
            if worflowId:
                print "getWorkflowId() duplicate workflow '{}' found in paths: {} and {}".format(worflowName, workflowPath, wrkfl['path'])
                return None
            worflowId = wrkfl['id']
            workflowPath = wrkfl['path']
    debug("getWorkflowId() workflowId = {}".format(worflowId))
    if not worflowId:
        print "getWorkflowId() workflow '{}' in category '{}' not found".format(worflowName, worflowCategory)
        return None
    return worflowId

def workflowExecute(worflowPathNameOrId, **kwargs): # v3 - Execute named workflow with inputs key:values
                                                    # Syntax: workflowExecute("Provisioning/Onboard VSP", deviceIP="10.10.10.10")
    # Get the workflow id
    if str(worflowPathNameOrId).isdigit():
        worflowId = worflowPathNameOrId
    else:
        worflowId = getWorkflowId(worflowPathNameOrId)
    debug("workflowExecute() workflowId = {}".format(worflowId))

    # Execute the workflow with inputs hash provided
    executionId = nbiMutation(NBI_Query['executeWorkflow'], ID=str(worflowId), JSONINPUTS=re.sub(r'"(.*?)"(?=:)',r'\1',json.dumps(kwargs)))
    return executionId


#
# Parsing of config template for #if/#elseif/#else/#end velocity type statements
# v4
import re
RegexIfElse = re.compile('^#(if|elseif|else|end) *(?:\((.+?)\) *$|(\S+))?')

def preParseIfElseBlocks(config): # v3 - Pre-parses config for embedded ${}/$<>/$()/$UD1-4 variables used on #if/#elseif/#else/#end velocity type statements
    # Since the #if/#elseif conditionals will be eval()-ed, any variable replacement will need to be quoted for a string
    parsedConfig = []
    for line in config.splitlines():
        regexMatch = RegexIfElse.match(line)
        if regexMatch:
            line = re.sub(r'(\$\{.+?\}|\$<.+?>|\$\(.+?\)|\$UD\d)', r'"\1"', line)
        parsedConfig.append(line)
    finalConfig = "\n".join(parsedConfig)
    debug("preParseIfElseBlocks finalConfig:\n{}\n".format(finalConfig))
    return finalConfig

def parseIfElseBlocks(config): # v1 - Parses config for embedded #if/#elseif/#else/#end velocity type statements
    parsedConfig = []
    includeLines = True
    ifMatch = False
    expectedStatements = []
    lineNumber = 0
    for line in config.splitlines():
        lineNumber += 1
        regexMatch = RegexIfElse.match(line)
        if regexMatch:
            statement = regexMatch.group(1).lower()
            evalString = regexMatch.group(2)
            invalidArg = regexMatch.group(3)
            if invalidArg:
                exitError("Error parsing config file line number {}: invalid syntax for statement '#{}'".format(lineNumber, statement))
            try:
                condition = bool(eval(evalString, {})) if evalString else False
            except SyntaxError:
                exitError("Error parsing config file line number {}: cannot Python eval() conditional: '({})'".format(lineNumber, evalString))
            if statement == "if":
                if condition == True:
                    ifMatch = True
                else:
                    includeLines = False
                expectedStatements = ["elseif", "else", "end"]
                continue
            elif statement not in expectedStatements:
                exitError("Error parsing config file line number {}: found unexpected statement '#{}'".format(lineNumber, statement))
            elif statement == "elseif":
                if ifMatch == False and condition == True:
                    includeLines = True
                    ifMatch = True
                else:
                    includeLines = False
                continue
            elif statement == "else":
                if evalString:
                    exitError("Error parsing config file line number {}: statement '#{}' should have no arguments".format(lineNumber, statement))
                includeLines = True if ifMatch == False else False
                expectedStatements = ["end"]
                continue
            elif statement == "end":
                if evalString:
                    exitError("Error parsing config file line number {}: statement '#{}' should have no arguments".format(lineNumber, statement))
                includeLines = True
                expectedStatements = []
                continue
            else:
                exitError("Error parsing config file line number {}: found unsupported statement '#{}'".format(lineNumber, statement))
        if includeLines:
            parsedConfig.append(line)
    if expectedStatements:
        exitError("Error parsing config file line number {}: never found expected statement '#{}'".format(lineNumber, expectedStatements[0]))
    finalConfig = "\n".join(parsedConfig)
    debug("parseIfElseBlocks finalConfig:\n{}\n".format(finalConfig))
    return finalConfig


#
# SNMP functions - (use of rollback requires rollback functions)
# v2
import re
from xmclib.snmplib import SnmpRequest
from xmclib.snmplib import SnmpVarbind
from xmclib.snmplib import ASN_INTEGER, ASN_OCTET_STR, ASN_OCTET_STR_DEC, ASN_OCTET_STR_HEX, ASN_OCTET_STR_PRINTABLE, \
                           ASN_OBJECT_ID, ASN_IPADDRESS, ASN_COUNTER, ASN_UNSIGNED, ASN_GAUGE, ASN_TIMETICKS, ASN_COUNTER64, \
                           ASN_OPAQUE_FLOAT, ASN_OPAQUE_DOUBLE, ASN_OPAQUE_U64, ASN_OPAQUE_I64
SnmpTarget = None
SnmpTimeout = 3
SnmpRetries = 3
LastSnmpError = None

def snmpTarget(ipAddress=emc_vars["deviceIP"], timeout=None, retries=None): # v1 - Sets SNMP target IP
    global SnmpTarget
    SnmpTarget = SnmpRequest(ipAddress)
    if timeout:
        global SnmpTimeout
        SnmpTimeout = timeout
    if retries:
        global SnmpRetries
        SnmpRetries = retries


def separateOid(inOid): # v1 - Separates the OID name from the OID value
    if re.search(r':', inOid):
        displayOid, oid = map(str.strip, inOid.split(':', 1))
        displayOid += ':'
    else:
        displayOid = ''
        oid = inOid
    return displayOid, oid


def snmpInputLists(caller, requestDict, instance=None, value=None): # v1 - Validate inputs and prepare input lists
    if not SnmpTarget:
        exitError("{}() cannot be called without first setting up an SNMP target with snmpTarget()".format(caller))
    if not requestDict:
        exitError("{}() no request dictionary definition supplied".format(caller))

    if caller in ('snmpSet', 'snmpCheckSet') and value == None:
        if 'set' in requestDict:
            value = requestDict['set']
        else:
            exitError("{}() no value to set".format(caller))

    if isinstance(requestDict['oid'], str): # If a string.. i.e. single OID
        if isinstance(requestDict['asn'], list):
            exitError("{}() single OID provided but list of {} ASN types".format(caller, len(requestDict['asn'])))
        if isinstance(instance, list):
            oidList = [requestDict['oid']] * len(instance) # Make it a list of same size as instances with all the same OID value
            asnList = [requestDict['asn']] * len(instance) # Do the same for ASN types
        else:
            oidList = [requestDict['oid']] # Make it a 1 element list
            asnList = [requestDict['asn']] # Do the same for ASN type
    else:
        oidList = requestDict['oid']

    if isinstance(requestDict['asn'], list): # List of ASN types provided
        if len(requestDict['asn']) != len(oidList):
            exitError("{}() supplied list of {} OIDs but list of {} ASN types".format(caller, len(oidList), len(requestDict['asn'])))
        asnList = requestDict['asn']

    if instance == None:
        instList = [None] * len(oidList)
    elif isinstance(instance, list): # List of instances provided
        if len(instance) != len(oidList):
            exitError("{}() supplied list of {} OIDs but list of {} instances".format(caller, len(oidList), len(instance)))
        instList = instance
    else: # Single instance provided
        instList = [instance] * len(oidList) # Make a list of same size as OIDs with all the same value

    if value == None:
        valueList = []
    if isinstance(value, list): # List of values provided
        if len(value) != len(oidList):
            exitError("{}() supplied list of {} OIDs but list of {} values".format(caller, len(oidList), len(value)))
        for val in value:
            if 'map' in requestDict and val in requestDict['map']:
                valueList.append(requestDict['map'][value])
            else:
                valueList.append(val)
    else: # Single value provided
        if 'map' in requestDict and value in requestDict['map']:
            valueList = [requestDict['map'][value]] * len(oidList) # Make a list of same size as OIDs with all the same value
        else:
            valueList = [value] * len(oidList) # Make a list of same size as OIDs with all the same value

    debug("{} snmpInputLists:\n - oidList = {}\n - instList = {}\n - asnList = {}\n - valueList = {}".format(caller, oidList, instList, asnList, valueList))
    return oidList, instList, asnList, valueList


def snmpGet(requestDict, instance=None, timeout=None, retries=None, debugVal=None, returnError=False): # v2 - Performs SNMP get
    # RequestDict oid key can be a single OID, or it can be a list of OIDs
    # If a list of OIDs, then instance can either be a single value or a list
    #    - if single instance, then the instance will be applied to all OIDs
    #    - if list of instances, then these need to be of same size as the list of OIDs
    # If a single OID, then instance can again either be a single value or a list
    # Returns either single value (for single OID)
    # or a list of values (for multiple OIDs) in same order

    global LastSnmpError

    # Validate and prepare input lists
    oidList, instList, _, _ = snmpInputLists("snmpGet", requestDict, instance)

    # Prepare SNMP varbinds
    varbinds = []
    for inOid, inst in zip(oidList, instList):
        displayOid, oid = separateOid(inOid)
        getOid = '.'.join([oid, str(inst)]) if inst != None else oid
        varbinds.append(SnmpVarbind(oid=getOid))
        debug("snmpGet request {}{}".format(displayOid, getOid))
    timeout = timeout if timeout else SnmpTimeout
    retries = retries if retries else SnmpRetries

    # Perform SNMP request
    response = SnmpTarget.snmp_get(varbinds, timeout=timeout, retries=retries)
    if response.ok:
        LastSnmpError = None
        retValue = []
        for binding in response.vars:
            retValue.append(binding.val)
            debug("snmpGet response {} = {}".format(binding.var, binding.val))
        if len(retValue) == 1:
            retValue = retValue[0]
        if debugVal:
            debug("snmpGet response {} = {}".format(debugVal, retValue))
        else:
            debug("snmpGet response retValue = {}".format(retValue))
        return retValue

    # In case of error
    if returnError: # If we asked to return upon SNMP error, then the error message will be held in LastSnmpError
        LastSnmpError = response.error
        return None
    abortError("snmpGet for\n{}".format(requestDict['oid']), response.error)


def snmpWalk(requestDict, timeout=None, retries=None, returnError=False): # v2 - Performs SNMP walk
    # RequestDict oid key can be a single OID, or it can be a list of OIDs
    # Returns a dict with format:
    # {
    #     instance1: {oid1: value, oid2: value, ...},
    #     instance2: {oid1: value, oid2: value, ...},
    #     ...
    # }

    global LastSnmpError

    # Validate and prepare input lists
    oidList, _, _, _ = snmpInputLists("snmpWalk", requestDict)

    # Prepare SNMP varbinds
    varbinds = []
    for inOid in oidList:
        displayOid, oid = separateOid(inOid)
        varbinds.append(SnmpVarbind(oid=oid))
        debug("snmpWalk request {}{}".format(displayOid, oid))
    timeout = timeout if timeout else SnmpTimeout
    retries = retries if retries else SnmpRetries

    # Perform SNMP request
    response = SnmpTarget.snmp_get_next(varbinds, timeout=timeout, retries=retries)
    if response.ok:
        LastSnmpError = None
        if Debug:
            for instance in response.data:
                for oid in response.data[instance]:
                    debug("snmpWalk response {} = {}".format(oid, response.data[instance][oid]))
        return response.data

    # In case of error
    if returnError: # If we asked to return upon SNMP error, then the error message will be held in LastSnmpError
        LastSnmpError = response.error
        return None
    abortError("snmpGetNext for\n{}".format(requestDict['oid']), response.error)


def snmpSet(requestDict, instance=None, value=None, timeout=None, retries=None, returnError=False): # v2 - Performs SNMP set
    # RequestDict oid key can be a single OID, or it can be a list of OIDs
    # If a list of OIDs, then instance, ASN & value can either be a single value or lists
    #    - if single value, then the instance|ASN|value will be applied to all OIDs
    #    - if list of values, then these need to be of same size as the list of OIDs
    # If a single OID, then instance can again either be a single value or a list
    #    - if instance is a list, then values can also be a list, but of same length

    global LastSnmpError
    if Sanity:
        print "SANITY - SNMP Set:"
    else:
        print "SNMP Set:"

    # Validate and prepare input lists
    oidList, instList, asnList, valueList = snmpInputLists("snmpSet", requestDict, instance, value)

    # Prepare SNMP varbinds
    varbinds = []
    for inOid, inst, asn, val in zip(oidList, instList, asnList, valueList):
        displayOid, oid = separateOid(inOid)
        setOid = '.'.join([oid, str(inst)]) if inst != None else oid
        print " - {}{} = {}".format(displayOid, setOid, val)
        varbinds.append(SnmpVarbind(oid=setOid, asn_type=asn, value=str(val)))
        debug("snmpSet request {}{} = {}".format(displayOid, setOid, val))
    if Sanity:
        LastNbiError = None
        return True
    timeout = timeout if timeout else SnmpTimeout
    retries = retries if retries else SnmpRetries

    # Perform SNMP request
    response = SnmpTarget.snmp_set(varbinds, timeout=timeout, retries=retries)
    valueSetFlag = True # Assume all good
    if response.ok:
        for binding, val in zip(response.vars, valueList): # Then check
            debug("snmpSet response {} = {}".format(binding.var, binding.val))
            if binding.val != str(val):
                valueSetFlag = False
        if valueSetFlag: # All good
            LastSnmpError = None
            return True
        # Else fall through

    # In case of error
    LastSnmpError = "Values not set as expected" if not valueSetFlag else response.error
    if returnError: # If we asked to return upon SNMP error, then the error message will be held in LastSnmpError
        return False
    abortError("snmpSet for\n{}".format(requestDict['oid']), LastSnmpError)


def snmpCheckSet(requestDict, instance=None, value=None, timeout=None, retries=None, returnError=False, returnNoSuchObj=True, rollback=False): # v1 - Performs SNMP set based on get value
    # Essentially same as snmpSet(), except that snmpGet() is first called to check whether the OID(s) are writable and if they are already set to same value
    # So an snmpSet() is only performed if the OID is writeable and the OID is not currently set to the desired value
    # Also implements rollback: in case of workflow failure, OID wich were set, are restored to their initial values
    # RequestDict oid key can be a single OID, or it can be a list of OIDs
    # If a list of OIDs, then instance, ASN & value can either be a single value or lists
    #    - if single value, then the instance|ASN|value will be applied to all OIDs
    #    - if list of values, then these need to be of same size as the list of OIDs
    # If a single OID, then instance can again either be a single value or a list
    #    - if instance is a list, then values can also be a list, but of same length

    print "SNMP Check:"

    # Validate and prepare input lists
    oidList, instList, asnList, valueList = snmpInputLists("snmpCheckSet", requestDict, instance, value)

    # Get current value of OID(s)
    currentValue = snmpGet(requestDict, instance=instance, timeout=timeout, retries=retries, returnError=True)

    # In list format
    if isinstance(currentValue, (str, unicode)): # If a string.. i.e. single value
        currValueList = [currentValue] # Make it a 1 element list
    else: # Is a list, make copy
        currValueList = currentValue

    noSuchObjFlag = False
    sameValueFlag = True
    for inOid, inst, currVal, val in zip(oidList, instList, currValueList, valueList):
        displayOid, oid = separateOid(inOid)
        setOid = '.'.join([oid, str(inst)]) if inst != None else oid
        print " - {}{} = {}".format(displayOid, setOid, currVal)
        if re.match(r'No Such Object', currVal): # OID not supported on device
            noSuchObjFlag = True
        elif currVal != str(val): # OID not set to desired value
            sameValueFlag = False
        else: # OID already set to desired value(s); nothing to do
            debug("snmpCheckSet already-set {}{} = {}".format(displayOid, setOid, val))

    if noSuchObjFlag:
        if returnNoSuchObj: # Ignore (note, enough to get No Such object on one OID, and all OIDs will be skipped)
            return False
        else: # Bomb
            abortError("snmpCheckSet for\n{}".format(requestDict['oid']), "No Such Object")

    if sameValueFlag: # Values already set as desired
        return True

    else: # We need to set desired value(s)
        snmpSet(requestDict, instance=instance, value=value, timeout=timeout, retries=retries, returnError=returnError)
        if rollback:
            rollbackSnmp(requestDict, instance, currentValue)










#
# Other Custom Functions
#

def extractVistData(): # v1 - Tricky command to extract from, as it is different across VOSS, VSP8600 and XA
    # Only supported for family = 'VSP Series'
    data = sendCLI_showRegex(CLI_Dict[Family]['get_virtual_ist_data'])
    dataDict = {}
    dataDict['vlan']  = data[0][0] if data else None
    dataDict['state'] = data[0][1] if data else None
    dataDict['role']  = data[1][2] if data else None
    debug("extractVistData() = {}".format(dataDict))
    return dataDict

def compareIsisSysId(selfId, peerId): # v1 - Returns TRUE if selfId < peerId
    selfId = int(selfId.replace('.', ''), 16) # Convert from hex
    peerId = int(peerId.replace('.', ''), 16) # Convert from hex
    if selfId < peerId:
        return True
    return False

def compareMacIsisSysId(chassisMac, isisSysId): # v1 - Determines whether the ISIS System ID was user assigned or is derived from chassis MAC
    chassisMac = chassisMac.replace(':', '')[0:10] #94:9b:2c:b4:74:00 ==> 949b2cb474
    isisSysId  = isisSysId.replace('.', '')[0:10]  #949b.2cb4.7484    ==> 949b2cb474
    result = (chassisMac == isisSysId)
    debug("compareMacIsisSysId() = {}".format(result))
    return result

def determineIstRole(selfId, peerId): # v1 - Determines role of switch in SMLT Cluster
    if compareIsisSysId(selfId, peerId):
        role = 'Primary'
    else:
        role = 'Secondary'
    debug("determineIstRole() = {}".format(role))
    return role

def allocateSmltVirtBmac(role, selfId, peerId, takenBmacs): # v1 - Given the SysId of the primary vIST node, cycles last byte until it finds a BMAC not in the list provided 
    baseId = selfId if role == 'Primary' else peerId
    baseId = baseId.replace('.', '') #949b.2cb4.7484    ==> 949b2cb47484
    baseMac = ':'.join(re.findall(r'[\da-f]{2}', baseId[:-2])) # All but last hex byte ==> 94:9b:2c:b4:74
    initLastByte = int(baseId[-2:], 16) # decimal of hex 84
    lastByte = initLastByte
    direction = 1 # We try and increment it
    while 1: # Until we find a unique Bmac
        if lastByte == 255: # If we reach 0xff, we need to search decrementing
            direction = -1
            lastByte = initLastByte # We go the other way
        elif direction == -1 and lastByte == 0: # Bad sign..
            exitError('allocateSmltVirtBmac(): unable to allocate smlt-virt-bmac in range {}:xx'.format(baseMac))
        byteValue = lastByte + direction
        smltVirtBmac = "{}:{:02x}".format(baseMac, byteValue)
        if smltVirtBmac not in takenBmacs:
            break
        lastByte = byteValue
    debug("allocateSmltVirtBmac() = {}".format(smltVirtBmac))
    return smltVirtBmac

def allocateIstVlan(selfList, peerList): # v1 - Given a list of already used VLANs in 4k range, allocates the vIST VLAN
    step = 1 if IstVLANrange[0] < IstVLANrange[1] else -1
    istVlan = None
    for vlan in range(IstVLANrange[0], IstVLANrange[1], step):
        if str(vlan) not in selfList and str(vlan) not in peerList:
            istVlan = vlan
            break
    if not istVlan:
        exitError('allocateIstVlan(): unable to allocate available vIST VLAN in range {}-{}'.format(IstVLANrange[0], IstVLANrange[1]))
    debug("allocateIstVlan() = {}".format(istVlan))
    return istVlan

def allocateIstMltId(selfList, peerList): # v1 - Given a list of already used MLT ids, allocates the vIST MLT id
    step = 1 if IstMLTrange[0] < IstMLTrange[1] else -1
    istMltId = None
    for mltid in range(IstMLTrange[0], IstMLTrange[1], step):
        if str(mltid) not in selfList and str(mltid) not in peerList:
            istMltId = mltid
            break
    if not istMltId:
        exitError('allocateIstMltId(): unable to allocate available vIST MLT id in range {}-{}'.format(IstMLTrange[0], IstMLTrange[1]))
    debug("allocateIstMltId() = {}".format(istMltId))
    return istMltId

def allocateClusterId(role, selfNickname, peerNickname): # v1 - Allocates a DVR Leaf Cluster Id by taking the last 9 bits of the Primary node's nickname
    nickname = selfNickname if role == 'Primary' else peerNickname
    nicknumber = int(nickname.replace('.', ''), 16)
    clusterId = nicknumber & 0x1ff # Cluster-id 1-1000 = last 9bits of primary nickname
    debug("allocateClusterId() = {}".format(clusterId))
    return clusterId

def allocateIstIsid(role, selfNickname, peerNickname): # v1 - Allocates a vIST I-SID by taking the last 19 bits of the Primary node's nickname
    nickname = selfNickname if role == 'Primary' else peerNickname
    nicknumber = int(nickname.replace('.', ''), 16)
    vistIsid = VistIsidOffset + (nicknumber & 0x7ffff) # IST I-SID (15000000 + last 19bits of Primary Nickname)  
    debug("allocateIstIsid() = {}".format(vistIsid))
    return vistIsid

def allocateIstIP(role, selfNickname, peerNickname): # v3 - Allocates the vIST IP by taking 192.168.255.X/30 with last 6bits of Secondary's nickname
    nickname = peerNickname if role == 'Primary' else selfNickname
    nicknumber = int(nickname.replace('.', ''), 16)
    ipSubnet = ipToNumber(VistIPbase[0]) + ((nicknumber & 0x3f) << 2)
    ipNumber1 = ipSubnet + 1
    ipNumber2 = ipSubnet + 2
    istIp1 = numberToIp(ipNumber1)
    istIp2 = numberToIp(ipNumber2)
    istSubnet = (numberToIp(ipSubnet), VistIPbase[1]) # IP/Mask
    istIPself = istIp2 if role == 'Primary' else istIp1 # Here we ensure Master = Primary
    istIPpeer = istIp1 if role == 'Primary' else istIp2 # Here we ensure Master = Primary
    debug("allocateIstIP() subnet = {} / self = {} / peer = {}".format(istSubnet, istIPself, istIPpeer))
    return istSubnet, istIPself, istIPpeer

def allocateMltIds(offsetId, numberOfMlts, inUseList1, inUseList2=[]): # v1 - Given the list of in use MLTs from both vIST peers, provides a list of free MLT ids to use
    mltList = []
    mltid = offsetId
    while 1:
        if str(mltid) not in inUseList1 and str(mltid) not in inUseList2:
            mltList.append(str(mltid))
        if len(mltList) == numberOfMlts:
            break
        mltid += 1
    debug("allocateMltIds() = {}".format(mltList))
    return mltList

def allocateMltId(offsetId, inUseList1, inUseList2=[]): # v1 - Given the list of in use MLTs from both vIST peers, provides a list of free MLT ids to use
    allocatedMltid = None
    mltid = offsetId
    while 1:
        if str(mltid) not in inUseList1 and str(mltid) not in inUseList2:
            allocatedMltid = mltid
            break
        mltid += 1
    debug("allocateMltId() = {}".format(allocatedMltid))
    return allocatedMltid

def extractMltData(include=[]): # v2 - Extract MLT data: optionally include = ['fa', 'vlacp', 'lacp-extra']
    # Only supported for family = 'VSP Series'
    data = sendCLI_showRegex(CLI_Dict[Family]['get_mlt_data'])
    mltDict = {}
    mltPortDict = {}
    for tpl in data:
        if tpl[0]:
            mltDict[tpl[0]] = {'type': tpl[1], 'ports': tpl[2]}
        elif tpl[3]:
            mltDict[tpl[3]]['lacp'] = tpl[4]
        elif tpl[5]:
            mltDict[tpl[5]]['flex'] = tpl[6]
    for mltid in mltDict:
        for port in generatePortList(mltDict[mltid]['ports']):
            mltPortDict[port] = mltid

    if mltDict:
        if 'fa' in include:
            data = sendCLI_showRegex(CLI_Dict[Family]['list_fa_mlts'])
            for mltid in mltDict:
                mltDict[mltid]['fa'] = bool(mltid in data)
        if 'vlacp' in include:
            for mltid in mltDict:
                mltDict[mltid]['vlacp'] = False
            data = sendCLI_showRegex(CLI_Dict[Family]['list_vlacp_ports'].format(generatePortRange(mltPortDict.keys())))
            for port in data:
                if data[port] == 'true' and port in mltPortDict:
                    mltDict[mltPortDict[port]]['vlacp'] = True
        if 'lacp-extra' in include:
            for mltid in mltDict:
                mltDict[mltid]['key'] = None
            mltKey = sendCLI_showRegex(CLI_Dict[Family]['list_mlt_lacp_key'])
            portKey = sendCLI_showRegex(CLI_Dict[Family]['list_port_lacp_key'])
            for mltid in mltKey:
                mltDict[mltid]['key'] = mltKey[mltid]
                matchingKeyPortList = [x for x in portKey if portKey[x] == mltKey[mltid]]
                # This overwrites the ports, but at least we get in there all ports configured with matching LACP key (not just ports active in MLT LAG)
                mltDict[mltid]['ports'] = generatePortRange(matchingKeyPortList)

    debug("extractMltData() = {}".format(mltDict))
    return mltDict, mltPortDict

def findUnusedPorts(mltPortDict={}): # v1 - This functions returns a list of "default" ports, i.e. unconfigured ports
    # Only supported for family = 'VSP Series'
    # A port is considered here to be default if it is untagged and only member of VLAN 1 or no VLAN at all (this already excludes ISIS ports)
    # The up/down state of the port is intentionally not considered here (a default port can be already enabled)
    # Checks are also made to ensure that the returned port list does not contain any:
    # - Brouter ports
    # - MLT ports:  In some scripts MLT data needs extracting in greater depth than what needed here; in which case
    #               an already populated mltPortDict can be supplied; see function extractMltData()
    vlanDefaultPorts = sendCLI_showRegex(CLI_Dict[Family]['list_vlan_default_ports'], 'vlanDefaultPorts')
    brouterPorts = sendCLI_showRegex(CLI_Dict[Family]['list_brouter_ports'], 'brouterPorts')
    if not mltPortDict:
        mltPortDict = extractMltData(['lacp-extra'])[1] # We just fetch the basic MLT data + lacp enabled ports
    defaultPorts = [x for x in vlanDefaultPorts if x not in brouterPorts and x not in mltPortDict]
    debug("findUnusedPorts() = {}".format(defaultPorts))
    return defaultPorts

def extractFAelements(newPortList): # v1 - Extracts data from show fa elements
    # Dump FA element tables
    data = sendCLI_showRegex(CLI_Dict[Family]['list_fa_elements'])
    dataDict = {}
    for tpl in data:
        if Family in ['VSP Series', 'ERS Series']:
            if tpl[0]:
                elType = re.sub(r'NoAuth$', '', tpl[1]).lower()
                elAuth = None
                dataDict[tpl[0]] = {'type': elType, 'auth': None, 'macid': tpl[2], 'portid': tpl[3], 'lacp': False}
            elif tpl[5] and tpl[5] in dataDict:
                dataDict[tpl[5]]['auth'] = False if re.search(r'NoAuth$', tpl[6]) else True
        else: # Summit Series
            macid = re.sub(r'-', ':', tpl[0])
            portid = re.sub(r'-', ':', tpl[1])
            typeMatch = re.match(r'(Server|Proxy)( \(No Auth\))?', tpl[3])
            if typeMatch:
                elType = typeMatch.group(1).lower()
                elAuth = False if typeMatch.group(2) else True
            else:
                elType = 'client'
                elAuth = None
            dataDict[tpl[2]] = {'type': elType, 'auth': elAuth, 'macid': macid, 'portid': portid, 'lacp': False}

    if Family == 'VSP Series': # On VSP only, dump LLDP neighbour tables
        data = sendCLI_showRegex(CLI_Dict[Family]['list_lldp_neighbours'].format(generatePortRange(dataDict.keys())))
        for port in dataDict:
            if port in data:
                if re.match(r'Ethernet Routing Switch', data[port]):
                    dataDict[port]['neigh'] = 'ERS'
                elif re.match(r'ExtremeXOS', data[port]):
                    dataDict[port]['neigh'] = 'XOS'
                else:
                    dataDict[port]['neigh'] = None

    if newPortList: # These are default ports enabled with FA & LACP by this script (only VSP Series will execute this part)
        testPortList = [x for x in dataDict if x in newPortList] # Of ports above, these are the ones where an FA neighbour is seen
        debug("extractFAelements() testPortList = {}".format(testPortList))
        if testPortList:
            testPortRange = generatePortRange(testPortList, 'testPortRange')
            lacpDetectedPorts = sendCLI_showRegex(CLI_Dict[Family]['list_lacp_up_ports'].format(testPortRange))
            for port in testPortList:
                if port in lacpDetectedPorts:
                    dataDict[port]['lacp'] = True

    # {u'1/5': {'portid': u'00:01:00:18', 'type': u'proxy', 'auth': False, 'macid': u'02:04:96:af:0e:ea', 'lacp': True, 'neigh': ERS|XOS}}
    debug("extractFAelements() = {}".format(dataDict))
    return dataDict

def extractChassisMac(): # v1 - Extract chassis MAC and return a sanitized MAC (lowercase hex and ':' byte separator)
    family = emc_vars["family"]
    data = sendCLI_showRegex(CLI_Dict[family]['get_chassis_mac'])
    chassisMac = data.replace('-', ':').lower()
    debug("extractChassisMac() = {}".format(chassisMac))
    return chassisMac

def xosExtractMltAndPortData(faAuthSupport=None): # v1 - Extract MLT data and Port data from XOS device
    # Only supported for family = 'Summit Series'
    mltDict = {}
    portDict = {}
    mltData = sendCLI_showRegex(CLI_Dict[Family]['get_mlt_data'])
    if faAuthSupport:
        faData = sendCLI_showRegex(CLI_Dict[Family]['list_fa_auth_ports'])
        for port in faData:
            faAuth = True if faData[port] == 'Enabled' else False
            portDict[port] = {'faAuth': faAuth, 'mlt': None}
    masterPort = None
    for tpl in mltData:
        if tpl[0]:
            masterPort = tpl[0]
            lacpEnabled = True if tpl[1] == 'LACP' else False
            mltDict[masterPort] = {'lacp': lacpEnabled, 'ports': [tpl[2]]}
        else:
            mltDict[masterPort]['ports'].append(tpl[2])
    for mltid in mltDict:
        for port in mltDict[mltid]['ports']:
            if port not in portDict:
                portDict[port] = {'faAuth': None, 'mlt': mltid}
            else:
                portDict[port]['mlt'] = mltid
        mltDict[mltid]['ports'] = generatePortRange(mltDict[mltid]['ports'])

    debug("xosExtractMltAndPortData() mltDict = {}".format(mltDict))
    debug("xosExtractMltAndPortData() portDict = {}".format(portDict))
    # mltDict: will include info of all MLTs
    # {"id" {'lacp': True|False, 'ports': "port-range"}}
    # portDict: will include info of all ports
    # {"port": {'faAuth': None|True|False, 'mlt': None|"id"}}
    return mltDict, portDict

def ersExtractMltAndPortData(include=[]): # v1 - Extract MLT data and Port data from ERS device (include = ['vlacp'])
    # Only supported for family = 'ERS Series'
    mltDict = {}
    portDict = {}
    mltData = sendCLI_showRegex(CLI_Dict[Family]['get_mlt_data'])
    for tpl in mltData:
        ports = None if tpl[1] == 'NONE' else tpl[1]
        mltEnabled = True if tpl[2] == 'Enabled' else False
        lacpKey = None if tpl[3] == 'NONE' else tpl[3]
        if not ports and not lacpKey:
            continue
        lacpEnabled = True if lacpKey else False
        mltDict[tpl[0]] = {'enable': mltEnabled, 'key': lacpKey, 'lacp': lacpEnabled, 'ports': ports, 'vlacp': False}
    for mltid in mltDict:
        if mltDict[mltid]['ports']: # If not None
            for port in generatePortList(mltDict[mltid]['ports']):
                portDict[port] = {'mlt': mltid}
    if 'vlacp' in include:
        vlacpData = sendCLI_showRegex(CLI_Dict[Family]['list_vlacp_ports'].format(generatePortRange(portDict.keys()))) # Only MLT ports
        for mltid in mltDict:
            mltDict[mltid]['vlacp'] = False
        for port in vlacpData:
            if vlacpData[port] == 'true' and port in portDict and portDict[port][mlt]:
                mltDict[portDict[port][mlt]]['vlacp'] = True

    debug("ersExtractMltAndPortData() mltDict = {}".format(mltDict))
    debug("ersExtractMltAndPortData() portDict = {}".format(portDict))
    # mltDict: will include info of all MLTs
    # {"id" {'enable': True|False, 'key': None|"key", 'lacp': True|False, 'ports': "port-range", 'vlacp': True|False}}
    # portDict: will include info of all ports which are assigned to an MLT [so not all ports]; we don't care about fa,faAuth as these are always enabeld on ERS
    # {"port": {'mlt': None|"id"}}
    return mltDict, portDict

def extractSpbmGlobal(): # v1 - Tricky command to extract from, as it is different across VOSS, VSP8600 and XA
    # Only supported for family = 'VSP Series'
    cmd = 'list://show isis spbm||(?:(B-VID) +PRIMARY +(NICK) +LSDB +(IP)(?: +(IPV6))?(?: +(MULTICAST))?|^\d+ +(?:(\d+)-(\d+) +\d+ +)?(?:([\da-f]\.[\da-f]{2}\.[\da-f]{2}) +)?(?:disable|enable) +(disable|enable)(?: +(disable|enable))?(?: +(disable|enable))?|^\d+ +(?:primary|secondary) +([\da-f:]+)(?: +([\da-f\.]+))?)'
    data = sendCLI_showRegex(cmd)
    # VOSS:[(u'B-VID', u'NICK', u'IP', u'IPV6', u'MULTICAST', u'', u'', u'', u'', u'', u'', u'', u''), (u'', u'', u'', u'', u'', u'4051', u'4052', u'0.00.75', u'enable', u'disable', u'disable', u'', u''),           (u'', u'', u'', u'', u'', u'', u'', u'', u'', u'', u'', u'00:00:00:00:00:00', u'')]
    # V86: [(u'B-VID', u'NICK', u'IP', u'', u'MULTICAST', u'', u'', u'', u'', u'', u'', u'', u''),     (u'', u'', u'', u'', u'', u'4051', u'4052', u'0.00.11', u'enable',             u'disable', u'', u'', u''),      (u'', u'', u'', u'', u'', u'', u'', u'', u'', u'', u'', u'82:bb:00:00:11:ff', u'82bb.0000.1200')]
    # XA:  [(u'B-VID', u'NICK', u'IP', u'', u'', u'', u'', u'', u'', u'', u'', u'', u''),              (u'', u'', u'', u'', u'', u'4051', u'4052', u'0.00.46', u'enable',                         u'', u'', u'', u'')]
    dataDict = {
        'SpbmInstance' : False,
        'BVIDs'        : [],
        'Nickname'     : None,
        'IP'           : None,
        'IPV6'         : None,
        'Multicast'    : None,
        'SmltVirtBmac' : None,
        'SmltPeerBmac' : None,
    }
    if len(data) > 1: # If we did not just match the banner line
        dataDict['SpbmInstance'] = True
        if data[1][5] and data[1][6]:
            dataDict['BVIDs'] = [data[1][5],data[1][6]]
        else:
            dataDict['BVIDs'] = []
        dataDict['Nickname'] = data[1][7]
        dataDict['IP'] = data[1][8]
        if data[0][3] == 'IPV6':
            dataDict['IPV6'] = data[1][9]
            if data[0][4] == 'MULTICAST':
                dataDict['Multicast'] = data[1][10]
        else:
            if data[0][4] == 'MULTICAST':
                dataDict['Multicast'] = data[1][9]
    if len(data) == 3: # We got SMLT data (on XA we don't have the line)
        if data[2][11] and data[2][11] != '00:00:00:00:00:00':
            dataDict['SmltVirtBmac'] = data[2][11]
            dataDict['SmltPeerBmac'] = data[2][12]
    debug("extractSpbmGlobal() = {}".format(dataDict))
    return dataDict

def extractExosVmData(): # v1 - Extract EXOS VM data
    # Only supported for family = 'Summit Series'
    data = sendCLI_showRegex(CLI_Dict[Family]['get_vm_data'])
    slotVmDict = {}
    if data:
        for tpl in data:
            if tpl[0]:
                slotVmDict['0'] = {'Memory': tpl[0]}
            elif tpl[1]:
               slotVmDict['0']['Cores'] = tpl[1]
            elif tpl[2]:
                slotVmDict[tpl[2]] = slotVmDict['0']
                del slotVmDict['0']
        debug("extractExosVmData() = {}".format(slotVmDict))
    # On Stack returns: {u'1': {'Memory': u'5728', 'Cores': u'1'}, u'2': {'Memory': u'4096', 'Cores': u'1'}}
    # On Standalone   : {'0': {'Memory': u'4096', 'Cores': u'1'}}
    # If no VMs       : {}
    return slotVmDict

def extractPortVlanData(portListStr): # v1 - Extract VLAN config on provided ports
    portVlanData = sendCLI_showRegex(CLI_Dict[Family]['list_port_vlans'].format(portListStr))
    portVlanDict = {}
    for tpl in portVlanData:
        portVlanDict[tpl[0]] = {
            'untagged': None,
            'tagged'  : tpl[2].split(','),
        }
        if tpl[3] == 'enable' and int(tpl[1]) > 0: 
            portVlanDict[tpl[0]]['untagged'] = tpl[1]
    debug("extractPortVlanData() = {}".format(portVlanDict))
    return portVlanDict

def extractFabricIds(): # v1 - Extracts all the BMACs (including SMLT Virt bmacs) and nicknames in fabric areas
    # Only supported for family = 'VSP Series'
    isisAreaDict = sendCLI_showRegex(CLI_Dict[Family]['get_isis_area'], 'isisAreaDict') # Get the ISIS areas
    fabricIdDict = {}
    for area in isisAreaDict:
        # Get the fabric IDs in current area
        fabricIdList = sendCLI_showRegex(CLI_Dict[Family]['get_in_use_fabric_ids'].format(isisAreaDict[area].lower()), 'fabricIdList')

        bmacHash = {}
        nicknameHash = {}
        for row in fabricIdList:
            bmacHash[numberToMacAddr(idToNumber(row[0]))] = 1
            nicknameHash[row[1]] = 1
            if row[2] != '00:00:00:00:00:00':
                bmacHash[row[2]] = 1
        fabricIdDict[area] = {'bmacs': list(bmacHash.keys()), 'nicknames': list(nicknameHash.keys())}

    debug("extractFabricIds() = {}".format(fabricIdDict))
    return fabricIdDict

def extractIsisInterfaces(): # v1 - Extract all the ISIS interfaces, in the 3 possible types: Port, MLT, Logical-intf
    # Only supported for family = 'VSP Series'
    isisIntfList = sendCLI_showRegex(CLI_Dict[Family]['get_isis_interfaces'], 'isisIntfList') # Get the ISIS areas
    isisIntfPortList = []
    isisIntfMltList = []
    isisLogicalIntfNameList = []
    isisLogicalIntfIdList = []
    for intf in isisIntfList:
        portMatch = re.match(r'^Port(\d+/\d+(?:/\d+)?)', intf)
        mltMatch  = re.match(r'^Mlt(\d+)', intf)
        if portMatch:
            isisIntfPortList.append(portMatch.group(1))
        elif mltMatch:
            isisIntfMltList.append(mltMatch.group(1))
        else:
            isisLogicalIntfNameList.append(intf)
    debug("extractIsisInterfaces() isisIntfPortList = {}".format(isisIntfPortList))
    debug("extractIsisInterfaces() isisIntfMltList = {}".format(isisIntfMltList))
    debug("extractIsisInterfaces() isisLogicalIntfNameList = {}".format(isisLogicalIntfNameList))

    if isisLogicalIntfNameList: # We have some Fabric Extend interfaces..
        feTunnelNameDict = sendCLI_showRegex(CLI_Dict[Family]['list_fe_tunnels_name'], 'feTunnelNameDict')
        for tunName in isisLogicalIntfNameList:
            isisLogicalIntfIdList.append(feTunnelNameDict[tunName])
        debug("extractIsisInterfaces() isisLogicalIntfIdList = {}".format(isisLogicalIntfIdList))

    isisIntfMltList.sort(key=int)
    isisLogicalIntfIdList.sort(key=int)
    isisIntfDict = {
        'port'    : generatePortRange(isisIntfPortList),
        'mlt'     : isisIntfMltList,
        'logical' : isisLogicalIntfIdList,
    }
    debug("extractIsisInterfaces() isisIntfDict = {}".format(isisIntfDict))
    return isisIntfDict

def getIsidUniStruct(isid): # v1 - Extract all port members of an I-SID
    # Only supported for family = 'VSP Series'
    # the "show i-sid" command is too fiddly to scrape...
    # the "show interfaces gigabitEthernet i-sid" command does not show I-SIDs with no ports assigned...
    # so we use "show run module i-sid" instead...
    cliOutput = sendCLI_showCommand(CLI_Dict[Family]['get_isid_uni_data'].format(isid))
    isidPorts = {}
    foundIsidData = False
    for line in cliOutput.splitlines():
        if foundIsidData:
            matchObj = re.match(r'c-vid (\d+) (port|mlt) (\S+)', line)
            if matchObj:
                tagging = 'tag'
                cvlan = matchObj.group(1)
                btype = matchObj.group(2)
                if btype == 'port':
                    ports = matchObj.group(3)
                    mlt = None
                else:
                    ports = None
                    mlt = matchObj.group(3)
            else:
                matchObj = re.match(r'untagged-traffic (port|mlt) (\S+)', line)
                if matchObj:
                    tagging = 'untag'
                    cvlan = None
                    btype = matchObj.group(1)
                    if btype == 'port':
                        ports = matchObj.group(2)
                        mlt = None
                    else:
                        ports = None
                        mlt = matchObj.group(2)
                else:
                    matchObj = re.match(r'(port|mlt) (\S+)', line)
                    if matchObj:
                        tagging = 'transparent'
                        cvlan = None
                        btype = matchObj.group(1)
                        if btype == 'port':
                            ports = matchObj.group(2)
                            mlt = None
                        else:
                            ports = None
                            mlt = matchObj.group(2)
                    elif re.match(r'exit', line):
                        break # We come out!
                    else:
                        continue
            if ports:
                portList = generatePortList(ports)
                debug("portList = {}".format(portList))
                for port in portList:
                    isidPorts[port] = {'type': tagging, 'vlan': cvlan}
            if mlt:
                isidPorts[mlt] = {'type': tagging, 'vlan': cvlan}

        elif re.match(r'^i-sid {} '.format(isid), line):
            isidPorts['exists'] = True
            foundIsidData = True
            continue
        else: # Other line, skip
            continue

    debug("getIsidUniStruct OUT = {}".format(isidPorts))
    return isidPorts


def idToNumber(idString): # v1 - Convert the sys-id or nickname or mac to a number
    return int(re.sub(r'[\.:]', '', idString), base=16)

def numberToHexStr(number, nibbleSize=''): # v1 - Convert a number to hex string
    template = "{:0" + str(nibbleSize) + "x}"
    return template.format(number)

def numberToBinStr(number, bitSize=''): # v1 - Convert a number to binary string
    template = "{:0" + str(bitSize) + "b}"
    return template.format(number)

def numberToNickname(idNumber): # v1 - Convert number to nickname string
    hexStr = numberToHexStr(idNumber, 5)
    return hexStr[0] + '.' + '.'.join(hexStr[i:i+2] for i in range(1, len(hexStr), 2))

def numberToSystemId(idNumber): # v1 - Convert number to System ID
    hexStr = numberToHexStr(idNumber, 12)
    return '.'.join(hexStr[i:i+4] for i in range(0, len(hexStr), 4))

def numberToMacAddr(idNumber):  # v1 - Convert number to MAC address
    hexStr = numberToHexStr(idNumber, 12)
    return ':'.join(hexStr[i:i+2] for i in range(0, len(hexStr), 2))

def nicknameXorMask(nickname, mask): # v1 - Perform XOR of nickname with mask
    return numberToNickname(idToNumber(nickname) ^ idToNumber(mask))

def systemIdXorMask(sysId, mask): # v1 - Perform XOR of system-id with mask
    return numberToSystemId(idToNumber(sysId) ^ idToNumber(mask))

def macXorMask(mac, mask): # v1 - Perform XOR of MAC address with mask
    return numberToMacAddr(idToNumber(mac) ^ idToNumber(mask))

def idReplMask(inId, mask, value, nibbles=12): # v1 - Replaces masked bits with value provided; nibbles = 12 (MAC/SysId) / 5 (nickname)
    bits = nibbles * 4
    inIdNumber = idToNumber(inId)
    maskNumber = idToNumber(mask)
    notMaskNumber = maskNumber ^ ((1 << bits) - 1)
    valueNumber = idToNumber(value)
    maskBinStr = numberToBinStr(maskNumber, bits)
    valueBinStr = numberToBinStr(valueNumber)
    debug("inId     = {} / {}".format(numberToHexStr(inIdNumber, nibbles), numberToBinStr(inIdNumber, bits)))
    debug("mask     = {} / {}".format(numberToHexStr(maskNumber, nibbles), maskBinStr))
    debug("!mask    = {} / {}".format(numberToHexStr(notMaskNumber, nibbles), numberToBinStr(notMaskNumber, bits)))
    debug("value    = {} / {}".format(numberToHexStr(valueNumber), valueBinStr))

    valueMaskStr = ''
    for b in reversed(maskBinStr):
        if b == '1' and len(valueBinStr):
            valueMaskStr = valueBinStr[-1] + valueMaskStr
            valueBinStr = valueBinStr[:-1] # chop last bit off
        else:
            valueMaskStr = '0' + valueMaskStr
    if len(valueBinStr):
        print "idReplMask() remaining value bits {} not inserted !!".format(len(valueBinStr))
    valueMaskNumber = int(valueMaskStr, base=2)
    debug("vmask    = {} / {}".format(numberToHexStr(valueMaskNumber, nibbles), valueMaskStr))
    maskedIdNumber = inIdNumber & notMaskNumber
    debug("maskedId = {} / {}".format(numberToHexStr(maskedIdNumber, nibbles), numberToBinStr(maskedIdNumber, bits)))
    finalIdNumber = maskedIdNumber | valueMaskNumber
    debug("finalId  = {} / {}".format(numberToHexStr(finalIdNumber, nibbles), numberToBinStr(finalIdNumber, bits)))
    return finalIdNumber

def nicknameReplMask(nickname, mask, value): # v1 - Replaces nickname masked bits with value provided
    return numberToNickname(idReplMask(nickname, mask, value, 5))

def systemIdReplMask(sysId, mask, value): # v1 - Replaces system-id masked bits with value provided
    return numberToSystemId(idReplMask(sysId, mask, value))

def macReplMask(mac, mask, value): # v1 - Replaces MAC address masked bits with value provided
    return numberToMacAddr(idReplMask(mac, mask, value))

def parseCliCommands(chainStr): # v1 - Parses the CLI commands string and filters out empty lines and comment lines
    cmdList = map(str.strip, str(chainStr).splitlines())
    cmdList = filter(None, cmdList) # Filter out empty lines, if any
    cmdList = [x for x in cmdList if x[0] != "#"] # Strip commented lines out
    return "\n".join(cmdList)

def parseCyphers(chainStr): # v1 - Parses the SSH Cyphers input and filters out empty lines and comment lines
    cypherList = map(str.strip, str(chainStr).splitlines())
    cypherList = filter(None, cypherList) # Filter out empty lines, if any
    cypherList = [x for x in cypherList if x[0] != "#"] # Strip commented lines out
    return cypherList

def takePolicyDomainLock(policyDomain, waitTime=10, retries=6): # v1 - Take lock on opened policy domain
    # If we fail to get a lock initially, this could be due to a user holding a lock on the same policy domain
    # Or, it could be another instance of this same workflow running for another switch, doing the same thing
    # We allow 1 waitTime only for the former (no retries), then we take the lock forcibly
    # In the latter case, we retry as many times as retries, before failing, but never forcing

    def myClonesRunning(): # Return true if more then 1 instance of myself running
        runningWorkflowsList = nbiQuery(NBI_Query['listRunningWorkflows'], debugKey='runningWorkflowsList')
        myselfCount = 0
        for workflow in runningWorkflowsList:
            if workflow['workflowName'] == scriptName():
                myselfCount += 1
        if myselfCount == 0:
            exitError("Unexpected result while checking for clones of this workflow running\n{}".format(LastNbiError))
        if myselfCount > 1:
            return True
        return False

    forceFlag = False
    retriesCount = 0
    while not nbiMutation(NBI_Query['lockOpenedPolicyDomain'], FORCEFLAG=forceFlag): # Try take lock
        if LastNbiError == "Conflict":
            print "Unable to acquire lock on Policy Domain '{}'; re-trying in {} secs".format(policyDomain, waitTime)
            time.sleep(waitTime)
            if not myClonesRunning():
                print "No other clones of myself running, forcing lock on next try"
                forceFlag = True
            retriesCount += 1
            if retriesCount > retries:
                exitError("Failed to place lock on Policy Domain '{}' after {} retries\n{}".format(policyDomain, retries, LastNbiError))
        else:
            exitError("Failed to place lock on Policy Domain '{}'\n{}".format(policyDomain, LastNbiError))
    print "Placed lock on Policy Domain '{}'".format(policyDomain)

def parseCyphers(chainStr): # v1 - Parses the SSH Cyphers input and filters out empty lines and comment lines
    cypherList = map(str.strip, str(chainStr).splitlines())
    cypherList = filter(None, cypherList) # Filter out empty lines, if any
    cypherList = [x for x in cypherList if x[0] != "#"] # Strip commented lines out
    return cypherList






#
# Variables:
#
# Regexes:
# Port (VOSS):\d+/\d+(?:/\d+)?
# Port (EXOS):\d+(?::\d+)?
# MAC :[\da-f:]+
# IPv4:\d+\.\d+\.\d+\.\d+

BVLANs = [str(4051), str(4052)]
IstVLANrange = [4050, 4000] # Try for VLAN 4050, and decrement to 4000 if not available
IstMLTrange = [512,500]
VistIPbase = ('192.168.255.0', '255.255.255.252') #/30
CLI_Dict = {
    'FIGW': {
        'check_vm_running'           : 'bool://show version||[\d\.]+$',
        'create_ipsec_respdr_tunnel' : # {0} = Tunnel id, {1} = Tunnel name, {2} = FE Tunnel dest IP, {3} = IPsec auth key
                                       '''
                                       set ipsec {0} tunnel-name {1}
                                       set ipsec {0} responder-only true
                                       set ipsec {0} fe-tunnel-dest-ip {2}
                                       set ipsec {0} auth-key {3}
                                       set ipsec {0} fragment-before-encrypt enable
                                       set ipsec {0} esp aes256gcm16-sha256
                                       set ipsec {0} admin-state enable
                                       ''',
        'create_ipsec_tunnel'        : # {0} = Tunnel id, {1} = Tunnel name, {2} = IPsec Tunnel dest IP, {3} = FE Tunnel dest IP, {4} = IPsec auth key
                                       '''
                                       set ipsec {0} tunnel-name {1}
                                       set ipsec {0} ipsec-dest-ip {2}
                                       set ipsec {0} fe-tunnel-dest-ip {3}
                                       set ipsec {0} auth-key {4}
                                       set ipsec {0} fragment-before-encrypt enable
                                       set ipsec {0} esp aes256gcm16-sha256
                                       set ipsec {0} admin-state enable
                                       ''',
        'disable_fe_tunnel'          : 'delete ipsec {} admin-state enable', # Tunnel id
        'get_figw_config'            : 'str-nwlnjoin://show running-config||^(set.+)$',
        'get_ip_interfaces'          : 'dict://show running-config||set global (lan-intf-ip|ipsec-tunnel-src-ip|fe-tunnel-src-ip) (\d+\.\d+\.\d+\.\d+)',
        'get_version'                : 'str://show version||([\d\.]+)$',
        'global_config'              : # {0} = FIGW internal VLAN, {2} = FIGW Internal IP, {4} = VSP Internal IP, {6} = Internal VLAN Mask
                                       # {1} = FIGW external VLAN, {3} = FIGW External IP, {5} = WAN External IP, {7} = Internal VLAN Mask, {8} = FE Tunnel Src Ip
                                       '''
                                       set global lan-intf-vlan {0}
                                       set global lan-intf-ip {2}/{6}
                                       set global lan-intf-gw-ip {4}
                                       set global ipsec-tunnel-src-vlan {1}
                                       set global ipsec-tunnel-src-ip {3}/{7}
                                       set global wan-intf-gw-ip {5}
                                       set global fe-tunnel-src-ip {8}
                                       set global mtu 1500
                                       ''',
        'list_fe_tunnels'            : 'list://show running-config||set (?:ipsec|logical-intf-tunnel) (\d+) (?:fe-tunnel-dest-ip (\d+\.\d+\.\d+\.\d+)|tunnel-name (\S+))',
        'save_config'                : 'save config -y',
        'show_version'               : 'show version',
        'show_version_bad'           : 'show bersion', # for testing error message detection
    },
    'VSP Series': {
        'disable_more_paging'        : 'terminal more disable',
        'enable_context'             : 'enable',
        'config_context'             : 'config term',
        'vrf_config_context'         : 'router vrf {}', # VRF name
        'port_config_context'        : 'interface gigabitEthernet {}', # Port list
        'mlt_config_context'         : 'interface mlt {}', # MLT id
        'vlan_config_context'        : 'interface vlan {}', # VLAN id
        'isis_config_context'        : 'router isis',
        'exit_config_context'        : 'exit',
        'end_config'                 : 'end',
        'end_save_config'            : 'end; save config',
        'save_config'                : 'save config',
        'software_commit'            : 'software commit',
        'figw_cli'                   : 'virtual-service figw figw-cli "{}"', # FIGW command (requires config context)

        'apply_ipvpn_unicast'        : 'isis apply redistribute direct vrf {}', # VRF name
        'apply_isis_accept'          : 'isis apply accept vrf {}', # VRF name
        'apply_ist_routemap'         : 'isis apply redistribute direct',

        'disable_ftp'                : 'no boot config flags ftpd',
        'enable_ftp'                 : 'boot config flags ftpd',

        'change_isis_system_id'      : 'system-id {}', # system-id
        'change_lacp_smlt_mac'       : 'lacp smlt-sys-id {}', # mac
        'change_smlt_virt_peer_id'   : 'spbm 1 smlt-peer-system-id {}; spbm 1 smlt-virtual-bmac {}', # SMLT Peer sys-id, SMLT Virt BMAC
        'change_spbm_nickname'       : 'spbm 1 nick-name {}', # nickname
        'change_sys_name'            : # Sys-name
                                       '''
                                       snmp-server name {0}
                                       router isis
                                          sys-name {0}
                                       exit
                                       ''',

        'check_autosense'            : 'bool://show vlan basic||^4048  onboarding-vlan  private',
        'check_autosense_enabled'    : 'bool://show auto-sense onboarding||^15999999 +4048',
        'check_cvlan_exists'         : 'bool://show vlan basic {0}||^{0}\s', # VLAN id
        'check_fe_tunnel_exists'     : 'bool://show isis logical-interface|| {} ',
        'check_figw_dir_exists'      : 'bool://ls {}||^Listing Directory', # Path
        'check_ftp_daemon'           : 'bool://show boot config flags||^flags ftpd true',
        'check_iah_insight_port'     : 'bool://show interfaces gigabitEthernet interface {0}||^{0} ', # Insight port
        'check_isis_adjacencies'     : 'bool://show isis adjacencies||^\S+ +1 UP',
        'check_mgmt_clip_exists'     : 'bool://show mgmt interface||^\d +Mgmt-clip +CLIP', # VRF name
        'check_redist_exists'        : 'bool://show ip isis redistribute vrf {}||^LOC',
        'check_software_commit'      : 'bool://show software||Remaining time until software auto-commit',
        'check_ssd_module_present'   : 'bool://show sys-info ssd||Serial Num',
        'check_vrf_exists'           : 'bool://show ip vrf||^{} ', # VRF name
        'check_users_connected'      : 'bool://show users||^(?:Telnet|SSH).+\d *$',

        'clear_autosense_voice'      : 'no auto-sense voice',
        'clear_autosense_data'       : 'no auto-sense data i-sid',
        'clear_autosense_wap'        : 'no auto-sense fa wap-type1 i-sid',
        'clear_cvlan_isid'           : 'no vlan i-sid {}', # VLAN id
        'clear_lacp_smlt_mac'        : 'lacp smlt-sys-id 00:00:00:00:00:00',
        'clear_spbm_bvids'           : 'no spbm 1 b-vid {0}-{1}', # Bvid#1, Bvid#2
        'clear_spbm_smlt_peer'       : 'no spbm 1 smlt-peer-system-id',
        'clear_spbm_smlt_virt_bmac'  : 'no spbm 1 smlt-virtual-bmac',

        'convert_mgmt_isid'          : # I-SID, IP, Mask, Gateway, Rollback secs
                                       '''
                                       mgmt vlan
                                       convert i-sid {} ip {} {} gateway {} rollback {}\ny
                                       ''',
        'convert_mgmt_vlan'          : # VLAN id, IP, Mask, Gateway, Rollback secs
                                       '''
                                       mgmt vlan
                                       convert vlan {} ip {} {} gateway {} rollback {}\ny
                                       ''',
        'convert_mgmt_vlan_isid'     : # VLAN id, I-SID, IP, Mask, Gateway, Rollback secs
                                       '''
                                       mgmt vlan
                                       convert vlan {} i-sid {} ip {} {} gateway {} rollback {}\ny
                                       ''',
        'convert_mgmt_commit'        : 'mgmt convert-commit',

        'copy_file_from_vm'          : 'virtual-service copy-file {0}:{1}/{2} {3}/{2}', # VM name, VM path, Filename, Local path
        'copy_file_to_vm'            : 'virtual-service copy-file {3}/{2} {0}:{1}/{2}', # VM name, VM path, Filename, Local path

        'create_cvlan'               : 'vlan create {} type port-mstprstp 0', # VLAN id
        'create_cvlan_dhcp_server'   : # {0} = DHCP IP
                                       '''
                                       ip dhcp-relay fwd-path {0} mode dhcp
                                       ip dhcp-relay fwd-path {0} enable
                                       ''',
        'create_cvlan_dvr'           : # {0} = DVR-GW IP
                                       '''
                                       dvr gw-ipv4 {0}
                                       dvr enable
                                       ''',
        'create_cvlan_ip'            : 'vrf {0}; ip address {1}/{2}', # {0} = VRF name, {1} = VLAN IP, {2} = IP Mask
        'create_cvlan_isid'          : 'vlan i-sid {0} {1}', # {0} = VLAN id, {1} = L2 I-SID
        'create_cvlan_mlt_uni'       : 'vlan mlt {} {}', # VLAN id, MLT id
        'create_cvlan_uni'           : { # {0} = VLAN id; {1} = port-list
            'tag'                    : 'interface gigabitEthernet {1}; encapsulation dot1q; exit; vlan members add {0} {1}',
            'untag'                  : 'interface gigabitEthernet {1}; no encapsulation dot1q; exit; vlan members add {0} {1}',
                                       },
        'create_cvlan_rsmlt'         : 'ip rsmlt; ip rsmlt holdup-timer 9999',
        'create_cvlan_vrrp'          : # {0} = VRRP VRID, {1} = VRRP IP, {2} = VRRP Priority
                                       '''
                                       ip vrrp version 3
                                       ip vrrp address {0} {1}
                                       ip vrrp {0} priority {2}
                                       ip vrrp {0} backup-master enable
                                       ip vrrp {0} enable
                                       ''',
        'create_directory'           : 'mkdir {}', # Path
        'create_dvr_inband_mgmt'     : 'router isis; inband-mgmt-ip {}; exit', # IP address
        'create_dvr_leaf'            : 'dvr leaf {}', # DVR domain
        'create_dvr_leaf_vist'       : 'dvr leaf virtual-ist {0}/30 peer-ip {1} cluster-id {2}', # {0} = IST IP, {1} = IST Peer IP, {3} = Cluster id
        'create_fe_global_config'    : # {0} = VRF Name, {1} = VRF id, {2} VLAN id, {3} = VLAN Name, {4} = FE Source IP, {5} = FE IP Mask, {6} = Default Gateway
                                       '''
                                       ip vrf {0} vrfid {1}
                                       vlan create {2} name {3} type port-mstprstp 0
                                       interface vlan {2}
                                          vrf {0}
                                          ip address {4}/{5}
                                       exit
                                       router vrf {0}
                                          ip route 0.0.0.0 0.0.0.0 {6} weight 10
                                       exit
                                       router isis
                                          ip-tunnel-source-address {4} vrf {0}
                                       exit
                                       ''',
        'create_fe_isis'             : # Tunnel metric
                                       '''
                                          isis
                                          isis spbm 1
                                          isis spbm 1 l1-metric {}
                                          isis enable
                                       ''',
        'create_fe_isis_remote'      : # Tunnel metric
                                       '''
                                          isis remote
                                          isis remote spbm 1
                                          isis remote spbm 1 l1-metric {}
                                          isis remote enable
                                       ''',
        'create_fe_src_vrf_clip'     : # {0} = VRF name, {1} = VRF id, {2} = Loopback id, {3} = IP address
                                       '''
                                       ip vrf {0} vrfid {1}
                                       interface loopback {2}
                                          ip address {3}/32 vrf {0}
                                       exit
                                       ''',
        'create_fe_tunnel'           : # {0} = FE Tunnel id, {1} = FE Tunnel dest IP, {2} = FE Tunnel name
                                       '''
                                       logical-intf isis {0} dest-ip {1} name {2}
                                          isis
                                          isis spbm 1
                                          isis enable
                                       exit
                                       ''',
        'create_fe_tunnel'           : # {0} = FE Tunnel id, {1} = FE Tunnel dest IP, {2} = FE Tunnel name, {3} = Tunnel metric
                                       '''
                                       logical-intf isis {0} dest-ip {1} name {2}
                                          isis
                                          isis spbm 1
                                          isis spbm 1 l1-metric {3}
                                          isis enable
                                       exit
                                       ''',
        'create_fe_tunnel'           : # {0} = FE Tunnel id, {1} = FE Tunnel dest IP, {2} = FE Tunnel name, {3} = Tunnel metric, {4} = VSP FE VRF, {5} = FIGW Internal IP
                                       '''
                                       logical-intf isis {0} dest-ip {1} name {2}
                                          isis
                                          isis spbm 1
                                          isis spbm 1 l1-metric {3}
                                          isis enable
                                       exit
                                       router vrf {4}
                                          ip route {1} 255.255.255.255 {5} weight 1
                                       exit
                                       ''',
        'create_fe_tunnel'           : # {0} = FE Tunnel id, {1} = FE Tunnel dest IP, {2} = FE Tunnel name
                                       '''
                                       logical-intf isis {0} dest-ip {1} name {2}
                                       ''',
        'create_fe_tunnel_src_vrf'   : # {0} = FE Tunnel id, {1} = FE Tunnel dest IP, {2} = FE Tunnel name, {3} = FE Tunnel src IP, (4) = FE Tunnel src VRF
                                       '''
                                       logical-intf isis {0} dest-ip {1} src-ip {3} vrf {4} name {2}
                                       ''',
        'create_fe_tunnel_src_vrf'   : # {0} = FE Tunnel id, {1} = FE Tunnel dest IP, {2} = FE Tunnel name, {3} = Tunnel metric, {4} = VSP FE VRF, {5} = FIGW Internal IP
                                       # {6} = FE Tunnel src IP, (8) = FE Tunnel src VRF
                                       '''
                                       logical-intf isis {0} dest-ip {1} src-ip {6} vrf {7} name {2}
                                          isis
                                          isis spbm 1
                                          isis spbm 1 l1-metric {3}
                                          isis enable
                                       exit
                                       router vrf {4}
                                          ip route {1} 255.255.255.255 {5} weight 1
                                       exit
                                       ''',
        'create_fe_tunnel_remote'    : # {0} = FE Tunnel id, {1} = FE Tunnel dest IP, {2} = FE Tunnel name, {3} = Tunnel metric
                                       '''
                                       logical-intf isis {0} dest-ip {1} name {2}
                                          isis remote
                                          isis remote spbm 1
                                          isis remote spbm 1 l1-metric {3}
                                          isis remote enable
                                       exit
                                       ''',
        'create_fe_static_route'     : 'ip route {} 255.255.255.255 {} weight 1', # FE Tunnel dest IP, FIGW Internal IP
        'create_fe_tnl_static_route' : 'ip route {} 255.255.255.255 {} weight 1', # FE Tunnel dest IP, FE Tunnel nexthop IP
        'create_figw_vlans'          : # {0} = FIGW internal VLAN, {2} = Insight port,  {4} = VSP FE VRF,      {6} = Internal VLAN Mask
                                       # {1} = FIGW external VLAN, {3} = Internet port, {5} = VSP Internal IP
                                       '''
                                       vlan create {0} name FIGW-internal type port-mstprstp 0
                                       vlan members {0} {2}
                                       interface vlan {0}
                                          vrf {4}
                                          ip address {5}/{6}
                                       exit
                                       vlan create {1} name FIGW-external type port-mstprstp 0
                                       interface gigabitEthernet {3}
                                          no auto-sense enable
                                       exit
                                       vlan members {1} {2},{3}
                                       interface gigabitEthernet {3}
                                          no encapsulation dot1q
                                          no spanning-tree mstp\ny
                                          no shutdown
                                       exit
                                       ''',
        'create_flex_uni'            : 'vlan members remove 1 {0}; interface gigabitEthernet {0}; flex-uni enable; no shutdown; exit', # Port
        'create_grt_redistribution'  : '''
                                       router isis
                                          redistribute direct
                                       exit
                                       ''',
        'create_ip_loopback'         : 'interface loopback {0}; ip address {1}/32; exit', # Loopback id, IP address
        'create_ipvpn'               : # {0} = L3 I-SID
                                       '''
                                       ipvpn
                                       i-sid {0}
                                       ipvpn enable
                                       ''',
        'create_isis_accept'         : 'isis accept i-sid {} enable', # shared I-SID
        'create_isis_area'           : 'manual-area {}', # Area
        'create_isis_interface'      : 'isis; isis spbm 1; isis enable',
        'create_isis_manual_area'    : # Area
                                       '''
                                       router isis
                                          manual-area {}
                                       exit
                                       ''',
        'create_ist_routemap'        : # {0} = IST subnet
                                       '''
                                       ip prefix-list "IST" {0}/30
                                       route-map "Suppress-IST" 1
                                          no permit
                                          enable
                                          match network "IST"
                                       exit
                                       route-map "Suppress-IST" 2
                                          permit
                                          enable
                                       exit
                                       router isis
                                          redistribute direct route-map "Suppress-IST"
                                       exit
                                       ''',
        'create_mgmt_clip'           : # VRF name, IP address
                                       '''
                                       mgmt clip vrf {0}
                                          ip address {1}/32
                                          enable
                                       exit
                                       ''',
        'create_mlt'                 : 'mlt {0}; mlt {0} member {1}', # MLT id, Port list
        'create_mlt'                 : 'mlt {} enable {}', # MLT id, 'name "name"'
        'create_mlt_flex_uni'        : 'interface mlt {0}; flex-uni enable; exit', # MLT id
        'create_mlt_switched_uni'    : { # {0} = i-sid; {1} = VLAN id; {2} = MLT-id
            'tag'                    : 'i-sid {0}; c-vid {1} mlt {2}; exit',
            'untag'                  : 'i-sid {0}; untagged-traffic mlt {2}; exit',
                                       },
        'create_ntp_server'          : 'ntp server {} enable', # IP
        'create_radius_server'       : # {0} = Radius Server IP, {1} = Radius secret, {2} = Source IP
                                       '''
                                       radius server host {0} key "{1}" used-by endpoint-tracking source-ip {2}
                                       radius sourceip-flag
                                       radius dynamic-server client {0} secret {1} enable
                                       ''',
        'create_radius_server_lns'   : # {0} = Radius Server IP, {1} = Radius secret
                                       '''
                                       radius server host {0} key {1} used-by endpoint-tracking
                                       radius dynamic-server client {0} secret {1} enable
                                       ''',
        'create_radius_server'       : 'radius server host {} key "{}" used-by {} priority {} acct-enable', # Radius Server IP, Radius secret, Use, Priority
        'create_dyn_radius_server'   : 'radius dynamic-server client {} secret "{}" enable', # Radius Server IP, Radius secret
        'create_spbm'                : 'spbm 1',
        'create_spbm_platform_bvlans': 'vlan create {0} name "Primary-BVLAN" type spbm-bvlan; vlan create {1} name "Secondary-BVLAN" type spbm-bvlan', # Bvid#1, Bvid#2
        'create_switched_uni'        : { # {0} = i-sid; {1} = VLAN id; {2} = port-list
            'tag'                    : 'i-sid {0}; c-vid {1} port {2}; exit',
            'untag'                  : 'i-sid {0}; untagged-traffic port {2}; exit',
                                       },
        'create_switched_isid'       : 'i-sid {0}; exit', # {0} = i-sid
        'create_vist'                : # {0} = IST VLAN, {1} = IST ISID, {2} = IST IP, {3} = IST Peer IP
                                       '''
                                       vlan create {0} name "IST-VLAN" type port-mstprstp 0
                                       vlan i-sid {0} {1}
                                       interface Vlan {0}
                                          ip address {2}/30
                                       exit
                                       virtual-ist peer-ip {3} vlan {0}
                                       ''',
        'create_vlan'                : 'vlan create {0} type port-mstprstp 0', # {0} = VLAN id
        'create_vlan_ip'             : # {0} = VLAN id, {1} = VRF Name, {2} = IP addr, {3} = Mask
                                       '''
                                       interface vlan {0}
                                          vrf {1}
                                          ip address {2}/{3}
                                          ip rsmlt
                                          ip rsmlt holdup-timer 9999 
                                       exit
                                       ''',
        'create_vlan_isid'           : 'vlan i-sid {0} {1}', # {0} = VLAN id; {1} = i-sid '
        'create_vrf'                 : 'ip vrf {}', # VRF name
        'create_vrf_with_id'         : 'ip vrf {0} vrfid {1}', # VRF name, VRF id

        'default_vlan_name'          : 'vlan name {0} VLAN-{0}', # VLAN id

        'delete_as_isis_key_file'    : 'delete /intflash/.auto_sense_key.txt -y',
        'delete_cvlan'               : 'vlan delete {}', # VLAN id
        'delete_cvlan_uni'           : 'vlan members remove {0} {1}', # {0} = VLAN id; {1} = port-list
        'delete_dvr_leaf'            : 'no dvr leaf',
        'delete_dvr_leaf_vist'       : 'no dvr leaf virtual-ist',
        'delete_dvr_controller'      : 'no dvr controller',
        'delete_ept'                 : 'no endpoint-tracking',
        'delete_fe_static_route'     : 'no ip route {} 255.255.255.255 {}', # FE Tunnel dest IP, Next hop
        'delete_fe_tunnel'           : 'no logical-intf isis {0}', # FE Tunnel id
        'delete_file'                : 'delete {}/{} -y', # Path, Filename
        'delete_isis_area'           : 'no manual-area {}', # Area
        'delete_isis_source_ip'      : 'router isis; no spbm 1 ip enable; no ip-source-address; exit; interface loopback {}; no ip address {}; exit', # Clip-id, IP address
        'delete_ist_routemap'        : '''
                                       no route-map "Suppress-IST" 1
                                       no route-map "Suppress-IST" 2
                                       no ip prefix-list "IST"
                                       ''',
        'delete_ist_vlan'            : 'vlan delete {0}', # IST VLAN
        'delete_mgmt_clip'           : 'no mgmt clip\ny',
        'delete_mgmt_vlan'           : 'no mgmt vlan\ny',
        'delete_mlt'                 : 'no mlt {}', # MLT id
        'delete_mlt_switched_uni'    : { # {0} = i-sid; {1} = VLAN id; {2} = MLT id
            'tag'                    : 'i-sid {0}; no c-vid {1} mlt {2}; exit',
            'untag'                  : 'i-sid {0}; no untagged-traffic mlt {2}; exit',
            'transparent'            : 'i-sid {0}; no mlt {2}; exit'
                                       },
        'delete_ntp_server'          : 'no ntp server {}', # IP
        'delete_radius_client'       : 'no radius dynamic-server client {}', # IP
        'delete_radius_server'       : 'no radius server host {} used-by endpoint-tracking', # IP
        'delete_spbm_platform_bvlans': 'vlan delete {0}; vlan delete {1}', # Bvid#1, Bvid#2
        'delete_switched_isid'       : 'no i-sid {}', # Isid
        'delete_switched_uni'        : { # {0} = i-sid; {1} = VLAN id; {2} = port-list
            'tag'                    : 'i-sid {0}; no c-vid {1} port {2}; exit',
            'untag'                  : 'i-sid {0}; no untagged-traffic port {2}; exit',
            'transparent'            : 'i-sid {0}; no port {2}; exit'
                                       },
        'delete_vist'                : 'no virtual-ist peer-ip',
        'delete_vrf'                 : 'no ip vrf {}\ny', # VRF name

        'disable_autosense'          : 'interface gigabitEthernet {0}; no auto-sense enable; exit', # Port
        'disable_autosense_conv2cfg' : 'interface gigabitEthernet {0}; no auto-sense enable convert-to-config; exit', # Port
        'disable_cfm_spbm'           : 'no cfm spbm enable',
        'disable_dvr_leaf_boot_flag' : 'no boot config flags dvr-leaf-mode',
        'disable_ept'                : 'no endpoint-tracking enable',
        'disable_fa_message_auth'    : 'no fa message-authentication',
        'disable_ip_shortcuts'       : 'router isis; no spbm 1 ip enable; exit',
        'disable_ipvpn_multicast'    : 'no mvpn enable',
        'disable_ipvpn_unicast'      : 'no isis redistribute direct',
        'disable_isis'               : 'no router isis enable\ny',
        'disable_isis_hello_padding' : 'router isis; no hello-padding; exit',
        'disable_lacp'               : 'no lacp enable',
        'disable_radius_accounting'  : 'no radius accounting enable',
        'disable_slpp_packet_rx'     : 'no slpp packet-rx; default slpp packet-rx-threshold',
        'disable_vlan_slpp'           : 'no slpp vid {}', # VLAN id

        'empty_directory'            : 'delete {}* -y\ny', # Path

        'enable_cvlan_dhcp_relay'    : 'ip dhcp-relay',
        'enable_cfm_spbm'            : 'cfm spbm enable',
        'enable_dvr_leaf_boot_flag'  : 'boot config flags dvr-leaf-mode\ny',
        'enable_ept'                 : 'endpoint-tracking enable',
        'enable_endpoint_tracking'   : 'endpoint-tracking enable',
        'enable_fabric_attach'       : 'fa; fa enable',
        'enable_ipvpn_multicast'     : 'mvpn enable',
        'enable_ipvpn_unicast'       : '''
                                       isis redistribute direct
                                       isis redistribute direct enable
                                       ''',
        'enable_ip_shortcuts'        : 'router isis; spbm 1 ip enable; exit',
        'enable_isis'                : 'router isis enable',
        'enable_lacp'                : 'lacp enable',
        'enable_mlt_flex_uni'        : 'flex-uni enable',
        'enable_mlt_tagging'         : 'mlt {} encapsulation dot1q', # MLT id
        'enable_ntp'                 : 'ntp',
        'enable_radius'              : 'radius enable',
        'enable_radius_accounting'   : 'radius accounting enable',
        'enable_rsmlt_edge'          : 'ip rsmlt edge-support',
        'enable_slpp_packet_rx'      : 'slpp packet-rx; slpp packet-rx-threshold {}', # SLPP threshold
        'enable_smlt'                : 'smlt',
        'enable_spb_multicast'       : 'ip spb-multicast enable',
        'enable_spbm'                : 'spbm',
        'enable_vlacp'               : 'vlacp enable',
        'enable_vlan_slpp'           : 'slpp vid {}', # VLAN id

        'get_auto_sense_state'       : 'str://show interfaces gigabitEthernet auto-sense {0}||^{0} +\S+ +(\S+)', # Port
        'get_auto_sense_states'      : 'dict://show interfaces gigabitEthernet auto-sense {}||^(\d+/\d+(?:/\d+)?) +\S+ +(\S+)', # Port(s)
        'get_autosense_data_isid'    : 'str://show auto-sense data||^(\d+)',
        'get_autosense_voice_isid'   : 'str://show auto-sense voice||(?:^|E +)(\d+) +[\du]',
        'get_autosense_wap_isid'     : 'str://show auto-sense fa||^wap-type1 +\S+ +(\d+)',
        'get_cfm_settings'           : 'tuple://show cfm spbm||^\d +(enable|disable) +(\d+)',
        'get_chassis_mac'            : 'str://show sys-info||BaseMacAddr +: +(\S+)',
        'get_cvlan_isid'             : 'str://show vlan {0} fabric attach assignments & show fabric attach vlan {0} assignments||^\s+{0}\s+\S+\s+(?:Static|Dynamic)\s+(\d+)', # VLAN id
        'get_cvlan_ip_data'          : 'tuple://show interfaces vlan ip {0}||^{0} +(\S+) +([\d\.]+) +([\d\.]+)',
        'get_cvlan_name'             : 'str://show vlan basic {0}||^{0} +(\S+)\s', # VLAN id
        'get_directory_file_sizes'   : 'dict-reverse://ls {}||(\d\d\d\d\d+) +\S+ +\S+ +\S+ +(\S+) *$', # Path
        'get_dvr_type'               : 'str-lower://show dvr||^Role +: +(Leaf|Controller)',
        'get_fe_tunnel_src_ip_vrf'   : 'dict-diagonal://show isis||(?:ip tunnel (source)-address : (\d+\.\d+\.\d+\.\d+)|Tunnel (vrf) :(?: +(\w+))?)',
        'get_figw_image_file_size'   : 'str://ls {1}{0}||(\d\d\d\d\d+) +\S+ +\S+ +\S+ +{0} *$', # Filename, Path
        'get_figw_save_files'        : 'list://virtual-service {} exec-command "ls {}"||^(\S+)$', # FIGW VM name, FIGW local file system path
        'get_flex_uni'               : 'dict://show interfaces gigabitEthernet config {}||^(\d+/\d+(?:/\d+)?) +\S+ +\S+ +\S+ +\S+ +\S+ +(Enable|Disable)', # Port
        'get_mgmt_ip_mask'           : 'int://show mgmt ip||{}/(\d\d?) ', # IP address
        'get_mgmt_default_gateway'   : 'str://show mgmt ip route||^0\.0\.0\.0/0 +(\d+\.\d+\.\d+\.\d+) ',
        'get_mgmt_gateway_mac'       : 'str://show mgmt ip arp||^{} +\S+ +([\da-f:]+) ', # Gateway IP
        'get_mgmt_gateway_port'      : 'str://show vlan mac-address-entry {0} mac {1}||{0} +\S+ +{1} +(?:u:|Port-)(\d+/\d+(?:/\d+)?) ', # VLAN id, MAC addr
        'get_mgmt_vlan'              : 'str://show mgmt interface||^\d +Mgmt-vlan +VLAN +enable +(\d+)',
        'get_mlt_data'               : 'list://show mlt||^(?:(\d+) +\d+.+?(?:access|trunk) +(norm|smlt) +(?:norm|smlt) *(\S+)?|(\d+) +\d+ +(?:[\d\/]+|null) +(enable|disable)|(\d+) +\d+ +\S+ +\S+ +\S+ +\S+ +\S+ +(enable|disable))',
        'get_mlt_tagging'            : 'dict://show mlt||^(\d+) +\d+.+?(access|trunk)',
        'get_mlt_type'               : 'dict://show mlt||^(\d+) +\d+.+?(?:access|trunk) +(norm|smlt)',
        'get_mlt_flex_uni'           : 'dict://show mlt||^(\d+) +\d+ +\S+ +\S+ +\S+ +\S+ +\S+ +(enable|disable)',
        'get_iah_cpu_mem_resources'  : 'dict-diagonal://show virtual-service statistics||(?:Number of (Cores) Remaining: +(\d+)|Total (Memory) Remaining\(M\): +(\d+))',
        'get_in_use_spbm_nicknames'  : 'list://show isis spbm nick-name||^\w+\.\w+\.\w+\.\d\d-\d\d +\d+ +({}[0-9a-f]\.[0-9a-f][0-9a-f]) ', # seems wrong..
        'get_in_use_fabric_ids'      : 'list://show isis spbm nick-name {}||^(\w+\.\w+\.\w+)\.\d\d-\d\d +\d+ +(\w\.\w\w\.\w\w) +(\w\w:\w\w:\w\w:\w\w:\w\w:\w\w) ', # home|remote
        'get_isid_cvlan'             : 'str://show vlan i-sid||^(\d+) +{0}', # Isid
        'get_isid_type'              : 'str://show i-sid {0}||^{0} +(\S+)\s', # Isid
        'get_isid_uni_data'          : 'show running-config module i-sid',
        'get_isis_directs_redist'    : 'tuple://show ip isis redistribute||^(LOC) +\d+ +\S+ +\S+ +\S+ +\S+\s*(\S+)?',
        'get_isis_global_settings'   : 'dict-diagonal://show isis||(?:(AdminState) : (enabled|disabled)|(System ID) : ?([\da-f]{4}\.[\da-f]{4}\.[\da-f]{4})?|(Router Name) : ?(\S+)?|ip (source-address) : ?(\d+\.\d+\.\d+\.\d+)?|(inband-mgmt-ip) : ?(\d+\.\d+\.\d+\.\d+)?)',
        'get_isis_interfaces'        : 'list://show isis interface||^(\S+) +pt-pt',
        'get_isis_manual_area'       : 'str://show isis manual-area||^([\da-fA-F\.]+)',
#        'get_isis_area'              : 'str://show isis area||^([\da-fA-F\.]+)',
        'get_isis_area'              : 'dict://show isis area||^([\da-fA-F\.]+) +(?:\S+ +(HOME|REMOTE))?',
        'get_isis_ip_clip'           : 'str://show interfaces loopback||^(\d+) +{}\s', # ISIS Source IP
        'get_l3vsn_vrf_name_pre83'   : 'str://show ip ipvpn||^\s+VRF Name\s+: (\S+)\n(?:\s+(?:Ipv[46] )?Ipvpn-state\s+: \w+\n)*\s+I-sid\s+: {}', # L3 I-SID
        'get_l3vsn_vrf_name'         : 'str://show ip ipvpn||^(\S+) +\d+ +\S+ +(?:\S+ +)?{}', # L3 I-SID
        'get_lacp_smlt_mac'          : 'str://show lacp||SmltSystemId: +(\w\w:\w\w:\w\w:\w\w:\w\w:\w\w)',
        'get_mac_address'            : 'str://show sys-info||BaseMacAddr +: +(\S+)',
        'get_4k_brouter_vlans'       : 'list://show brouter||^\s*\d+/\d+(?:/\d+)? +(4\d{3})',
        'get_4k_platform_vlans'      : 'list://show vlan basic||^(4\d{3})\s',
        'get_platform_vlans'         : 'list://show vlan basic||^(\d+) ',
        'get_platform_vlans_names'   : 'dict://show vlan basic||^(\d+) +(\S.+\S) +\S+ +\d+ +\S',
        'get_platform_vlan_types'    : 'dict://show vlan basic||^(\d+) +.+? +(\S+) +\d+ ',
        'get_smlt_role'              : 'str://show virtual-ist||(Slave|Master)',
        'get_spbm_platform_bvlans'   : 'list://show vlan basic||^(\d+) +.+? +spbm-bvlan',
        'get_spbm_global_settings'   : 'list://show isis spbm||(?:(B-VID) +PRIMARY +(NICK) +LSDB +(IP)(?: +(IPV6))?(?: +(MULTICAST))?|^\d+ +(?:(\d+)-(\d+) +\d+ +)?(?:([\da-f]\.[\da-f]{2}\.[\da-f]{2}) +)?(?:disable|enable) +(disable|enable)(?: +(disable|enable))?(?: +(disable|enable))?|^\d+ +(?:primary|secondary) +([\da-f:]+)(?: +([\da-f\.]+))?)',
        'get_static_route_next_hop'  : 'str://show ip route vrf {}||^{} +255.255.255.255 +(\d+\.\d+\.\d+\.\d+) ', # VRF name, Host Route
        'get_virtual_ist_data'       : 'list://show virtual-ist||^(?:\d+\.\d+\.\d+\.\d+ +(\d+) +\S+ +(up|down)|\S+ +\S+ +(Master|Slave))',
        'get_vlan_isids'             : 'dict://show vlan i-sid||^(\d+)(?: +(\d+)| +$)',
        'get_vlan_mac_table'         : 'dict://show vlan mac-address-entry {0}||^{0} +learned +([\da-f:]+) +(?:u:|Port-)(\d+/\d+(?:/\d+)?) ', #VLAN id
        'get_vlan_names'             : 'dict-reverse://show vlan name||^(\d+) +\d+ +(\S.*?) *$',
        'get_vlan_port_members'      : 'str-join://show vlan members {0}||^(?:{0})? +[\d\/,-]+ +([\d\/,-]+)', # VLAN id
        'get_vm_config'              : 'list://show running-config | include "virtual-service|in progress"||(?: (try the command later)|^(virtual-service {} .+$))', # VM name
        'get_vm_install_status'      : 'str://show virtual-service install {}||Status: *(\S.+\S) *$', # VM name
        'get_vm_names'               : 'dict-sequence://show virtual-service config||(?:Package: +(\S+) *$|Package App Name: +(\S+))',
        'get_vrf_name_by_id'         : 'str://show ip vrf vrfids {0}||(\S+) +{0} +(?:FALSE|TRUE)', # VRF id

        'install_vm_package'         : 'virtual-service {} install package {}{}', # VM name, VM image file path, VM image file name (run from privExec)

        'list_accept_l3isids'        : 'list://show ip isis accept vrf {0}||^- +(\d+) +- +TRUE', # VRF name
        'list_brouter_ips'           : 'list://show ip interface||^Port\S+ +(\d+\.\d+\.\d+\.\d+)',
        'list_brouter_ports'         : 'list://show brouter||^\s*(\d+/\d+(?:/\d+)?) +\d+',
        'list_cli_sessions'          : 'list://show users||^(Telnet|SSH)(\d+) +\S+ +\S+ +[\d\.\:]+ *$',
        'list_disabled_ports'        : 'list://show interfaces gigabitEthernet interface||^(\d+/\d+(?:/\d+)?).+?down +down',
        'list_fa_elements'           : 'list://show fa elements||^(?:(\d+/\d+(?:/\d+)?) +(\S+) +\d+ +\w / \w +((?:[\da-f]{2}:){5}[\da-f]{2}):((?:[\da-f]{2}:){3}[\da-f]{2}) +(\S+)|(\d+/\d+(?:/\d+)?) +(\S+) +\D)',
        'list_fa_interfaces'         : 'list://show fa interface||^(?:Mlt|Port)(\d+(?:/\d+(?:/\d+)?)?) +(enabled|disabled) +(\d+) +(\d+) +(enabled|disabled)',
        'list_fa_mlts'               : 'list://show fa interface||^Mlt(\d+)',
        'list_fabric_bmacs'          : 'list://show isis spbm unicast-fib vlan {0}||^(\S+) +{0}'.format(BVLANs[0]),
        'list_fe_tunnels_dest'       : 'dict://show isis logical-interface||^(\d+) +\S.*\S +IP +-- +-- +(\d+\.\d+\.\d+\.\d+) ',
#        'list_fe_tunnels_name'       : 'dict://show isis logical-interface name||^(\d+) +(\S.*\S)',
        'list_fe_tunnels_name'       : 'dict-reverse://show isis logical-interface name||^(\d+) +(\S.*\S)',
        'list_isis_areas'            : 'dict-reverse://show isis area||^([\da-f]+(?:\.[\da-f]+)+) +\S+ +(HOME|REMOTE)',
        'list_l3vsn_vrf_names_pre83' : 'dict-both://show ip ipvpn||^\s+VRF Name\s+: (\S+)\n(?:\s+(?:Ipv[46] )?Ipvpn-state\s+: \w+\n)*\s+I-sid\s+: (\S+)',
        'list_l3vsn_vrf_names'       : 'dict-both://show ip ipvpn||^(\S+) +\d+ +\S+ +(?:\S+ +)?(\d+)',
        'list_lacp_up_ports'         : 'list://show lacp actor-oper interface gigabitethernet {}||^(\d+/\d+(?:/\d+)?) +\d+ +\d+ +\d+ +\S+ +\S+ +short +indi +sync +col +dis', # Port list
        'list_link_up_ports'         : 'list://show interfaces gigabitEthernet interface {}||^(\d+/\d+(?:/\d+)?).+?up +up', # Ports
        'list_lldp_neighbours'       : 'dict://show lldp neighbor summary||^(\d+/\d+(?:/\d+)?) +LLDP +\S+ +\S+ +\S+ +\S+ +(.+)$',
        'list_loopbacks'             : 'dict://show interfaces loopback||^(\d+) +(\d+\.\d+\.\d+\.\d+)',
        'list_mgmt_arp_cache_macs'   : 'str://show mgmt ip arp||^\d+\.\d+\.\d+\.\d+ +\S+ +([\da-f:]+) ',
        'list_mgmt_interfaces'       : 'list://show mgmt interface||^\d +\S+ +([A-Z]+) ',
        'list_mgmt_ips'              : 'dict://show mgmt ip||^\d +(\S+) +(\d+\.\d+\.\d+\.\d+)/\d',
        'list_mlt_lacp_key'          : 'dict://show lacp interface mlt||^(\d+) +\d+ +\d+ +\S+ +\d+ +(\d+)',
        'list_ntp_servers'           : 'list://show ntp server ||^(\d+\.\d+\.\d+\.\d+)',
        'list_oob_mgmt_ips'          : 'list://show ip interface vrfids 512||^(?:Portmgm\d?|MgmtVirtIp|mgmt-oob) +(\d+\.\d+\.\d+\.\d+)',
        'list_port_lacp_key'         : 'dict://show lacp actor-oper interface||^(\d+/\d+(?:/\d+)?) +(\d+)',
        'list_port_up_speed'         : 'dict://show interfaces gigabitEthernet name {}||^(\d+/\d+(?:/\d+)?).+?up +full +(\d+) +\S+$', # Port list
        'list_port_voss_neighbours'  : 'dict://show lldp neighbor summary port {}||^(\d+/\d+(?:/\d+)?) +LLDP +\S+ +(\S+) +\S+ +\S+ +(?:VSP|XA)', # Port list
        'list_radius_ept_servers'    : 'list://show radius-server ||^(\d+\.\d+\.\d+\.\d+) +endpoint-tracking',
        'list_slpp_ports'            : 'list://show slpp interface gigabitEthernet||^(\d+/\d+(?:/\d+)?) +enabled',
        'list_software'              : 'dict://show software ||^(\w\S+)(?: +\((Primary|Backup|Next Boot) \S+\))?(?: +\((?:Signed|Unsigned) \S+\))? *$',
        'list_vlacp_ports'           : 'dict://show vlacp interface gigabitethernet {}||^(\d+/\d+(?:/\d+)?) +(true|false) +(?:true|false)', # Port list
        'list_vlan_default_ports'    : 'list://show interfaces gigabitEthernet vlan||^(\d+/\d+(?:/\d+)?) +disable +false +false +(?:1 +1|0 +0) +normal +disable',
        'list_port_vlans'            : 'list://show interfaces gigabitEthernet vlan {}||^(\d+/\d+(?:/\d+)?) +enable +false +\S+ +(\d+) +([\d,]+) +normal +(enable|disable)', # Ports
        'list_vlans'                 : 'list://show vlan basic||^(\d+) ',
        'list_vms'                   : 'list://show virtual-service config||Package: +(\S+) *$',
        'list_voss_neighbour_macs'   : 'dict-reverse://show lldp neighbor summary||^(\d+/\d+(?:/\d+)?) +LLDP +\S+ +([\da-f:]+)',
        'list_vrf_ip_interfaces'     : 'dict://show ip interface {}||^\S+ +(\d+\.\d+\.\d+\.\d+) +(\d+\.\d+\.\d+\.\d+)', # 'vrf <VRF-name>'
        'list_vrf_vlans'             : 'list://show ip interface vrf {}||^Vlan(\d+)\s', # VRF name
        'list_vrf_clip_ips'          : 'list://show ip interface vrf {}||^Clip\d+ +(\d+\.\d+\.\d+\.\d+)', # VRF name
        'list_vrfs'                  : 'dict-reverse://show ip vrf||(\S+) +(\d+) +\d+ +\d+ +[TF]',

        'log_message'                : 'logging write "{}"', # Message

        'measure_l2ping_rtt'         : 'tuple://l2 ping vlan {} routernodename {} burst-count {}||min/max/ave/stdv = +\d+/\d+/(\d+\.\d+)/ *(\d+\.\d+)', # BVLAN, Sysname, Burst

        'port_disable'               : 'shutdown',
        'port_disable_lacp'          : 'no lacp enable; no lacp aggregation enable; default lacp',
        'port_disable_poe'           : 'interface gigabitEthernet {}; poe poe-shutdown', # Port list
        'port_disable_slpp_guard'    : 'no slpp-guard enable',
        'port_disable_spoof_detect'  : 'no spoof-detect',
        'port_disable_tagging'       : 'no encapsulation dot1q',
        'port_disable_vlacp'         : 'default vlacp',
        'port_disable_with_stp'      : 'interface gigabitEthernet {}; shutdown; spanning-tree mstp force-port-state enable; exit', # Port list
        'port_enable'                : 'no shutdown',
        'port_enable_lacp'           : 'lacp key {} aggregation enable timeout-time short; lacp enable', # LACP key
        'port_enable_lacp_indi'      : 'lacp timeout-time short; lacp enable',
        'port_enable_no_stp'         : 'interface gigabitEthernet {}; no spanning-tree mstp\ny; no shutdown; exit', # Port list
        'port_enable_poe'            : 'interface gigabitEthernet {}; no poe-shutdown', # Port list
        'port_enable_slpp_guard'     : 'slpp-guard enable',
        'port_enable_spoof_detect'   : 'spoof-detect',
        'port_enable_vlacp'          : 'vlacp fast-periodic-time 500 timeout short timeout-scale 5 funcmac-addr 01:80:c2:00:00:0f; vlacp enable',
        'port_enable_tagging'        : 'encapsulation dot1q',
        'port_fa_detection_enable'   : # Port list
                                       '''
                                       interface gigabitEthernet {}
                                          no spanning-tree mstp\ny
                                          fa
                                          fa enable
                                          lacp enable timeout-time short
                                          vlacp fast-periodic-time 500 timeout short funcmac-addr 01:80:c2:00:00:0f
                                          vlacp enable
                                          no shutdown
                                       exit
                                       ''',
        'port_fa_detection_disable'  : # Port list
                                       '''
                                       interface gigabitEthernet {}
                                          shutdown
                                          no fa
                                          no lacp enable
                                          lacp timeout-time long
                                          no encapsulation dot1q
                                          spanning-tree mstp force-port-state enable
                                       exit
                                       ''',
        'port_remove_vlan1'          : 'vlan members remove 1 {}', # Port list
        'port_readd_vlan1'           : 'vlan members add 1 {}', # Port list
        'port_config_isis'           : 'isis; isis spbm 1; isis enable',
        'port_config_isis_auth'      : { # ISIS Auth key
            'HMAC-MD5'               : 'isis hello-auth type hmac-md5 key {}',
            'HMAC-SHA2'              : 'isis hello-auth type hmac-sha-256 key {}',
                                       },
        'port_config_isis_metric'    : 'interface gigabitEthernet {0}; isis spbm 1 l1-metric {1}', # Port list, Metric

        'ports_delete_ept'           : 'interface gigabitEthernet {0}; no endpoint-tracking; exit', # Port
        'ports_disable_ept'          : 'interface gigabitEthernet {0}; no endpoint-tracking enable; exit', # Port
        'ports_enable'               : 'interface gigabitEthernet {0}; no shutdown; exit', # Port
        'ports_enable_ept'           : 'interface gigabitEthernet {0}; endpoint-tracking enable; exit', # Port

        'reboot_switch'              : 'reset -y',

        'relocate_mgmt_vlan_ip'      : # {0} = VLAN id, {1} = Mgmt IP, {2} = Mgmt Mask, {3} = Gateway IP, {4} = Port
                                       '''
                                       no mgmt vlan\ny
                                       mgmt vlan {0}
                                          ip address {1}/{2}
                                          ip route 0.0.0.0/0 next-hop {3} weight 200
                                          enable
                                       exit
                                       vlan members add {0} {4}
                                       ''',

        'rename_fe_tunnel'           : # {0} = FE Tunnel id, {1} = FE Tunnel dest IP, {2} = FE Tunnel name
                                       '''
                                       logical-intf isis {0} dest-ip {1} name {2}
                                       exit
                                       ''',

        'set_autosense_data'         : # {0} = I-SID
                                       '''
                                       auto-sense data i-sid {0}
                                       i-sid name {0} "Auto-sense Data"
                                       ''',
        'set_autosense_wap'          : # {0} = I-SID
                                       '''
                                       auto-sense fa wap-type1 i-sid {0}
                                       i-sid name {0} "Auto-sense WapType1"
                                       ''',
        'set_autosense_fa_auth'      : 'auto-sense fa message-authentication; auto-sense fa authentication-key {}', # Auth key
        'set_autosense_isis_auth'    : 'auto-sense isis hello-auth type hmac-sha-256 key {}', # Auth key
        'set_autosense_voice_tag'    : # {0} = I-SID, {1} = VLAN id
                                       '''
                                       auto-sense voice i-sid {0} c-vid {1}
                                       i-sid name {0} "Auto-sense Voice"
                                       ''',
        'set_autosense_voice_untag'  : # {0} = I-SID
                                       '''
                                       auto-sense voice i-sid {0} untagged
                                       i-sid name {0} "Auto-sense Voice"
                                       ''',
        'set_autosense_wait_interval': 'auto-sense wait-interval {}', # Wait Interval
        'set_cfm_spbm_mepid'         : 'cfm spbm mepid {}', # Mep id
        'set_cvlan_isid'             : 'vlan i-sid {0} {1}', # {0} = VLAN id; {1} = i-sid 
        'set_cvlan_name'             : 'vlan name {0} {1}', # {0} = VLAN id; {1} = Name
        'set_fa_mgmt_vlan_isid'      : 'fa management i-sid {} c-vid {}', # I-SID, VLAN
        'set_isid_name'              : 'i-sid name {} "{}"', # I-SID, Name
        'set_isis_if_auth'           : { # ISIS Auth key
            'HMAC-MD5'               : 'isis hello-auth type hmac-md5 key {}',
            'HMAC-SHA2'              : 'isis hello-auth type hmac-sha-256 key {}',
                                       },
        'set_lacp_smlt_sys_id'       : 'lacp smlt-sys-id {}', # SmltVirtBmac
        'set_mlt_ports'              : 'mlt {} member {}', # MLT id, Port list
        'set_isis_if_metric'         : 'isis spbm 1 l1-metric {}', # Metric
        'set_isis_spbm_ip_enable'    : 'ip-source-address {}; spbm 1 ip enable', # IP address
        'set_isis_sys_name'          : 'sys-name {}', # SysName
        'set_isis_system_id'         : 'system-id {}', # System id
        'set_mlt_lacp_key'           : 'lacp enable key {}', # LACP key
        'set_radius_reachability'    : 'radius reachability mode status-server',
        'set_spbm_bvids'             : 'spbm 1 b-vid {0}-{1} primary {0}', # Bvid#1, Bvid#2
        'set_spbm_nickname'          : 'spbm 1 nick-name {}', # Nickname
        'set_spbm_smlt_peer'         : 'spbm 1 smlt-peer-system-id {}', # SysId
        'set_spbm_smlt_virt_bmac'    : 'spbm 1 smlt-virtual-bmac {}', # Bmac
        'set_sys_name'               : 'prompt {}', # SysName
        'set_timezone'               : 'clock time-zone {} {}', # Zone
        'set_vlan_name'              : 'vlan name {0} "{1}"', # {0} = VLAN id; {1} = Name

        'start_vm'                   : # {0} = VM name, {1} = CPUs, {2} = Memory, {3} = Vport name, {4} = Vport type, {5} = Insight port
                                       '''
                                       virtual-service {0}
                                       virtual-service {0} num-cores {1}
                                       virtual-service {0} mem-size {2}
                                       virtual-service {0} vport {3} connect-type {4}
                                       virtual-service {0} vport {3} port {5}
                                       virtual-service {0} enable
                                       vlan members remove 1 {5}
                                       interface gigabitEthernet {5}
                                           encapsulation dot1q
                                           no spanning-tree mstp\ny
                                           no shutdown
                                       exit
                                       ''',
    },
    'Summit Series': {
        'disable_more_paging'        : 'disable cli paging',
        'disable_cli_prompting'      : 'disable cli prompting',
        'save_config'                : 'save configuration',

        'check_cvlan_exists'         : 'bool://show vlan||^\S+ +{0}\s', # VLAN id

        'clear_cvlan_isid'           : 'configure vlan {0} delete isid {1}', # {0} = VLAN id; {1} = i-sid 

        'create_cvlan'               : 'create vlan {}', # VLAN id
        'create_cvlan_uni'           : { # {0} = VLAN id; {1} = port-list
            'tag'                    : 'configure vlan {0} add ports {1} tagged',
            'untag'                  : 'configure vlan {0} add ports {1} untagged',
                                       },
        'create_lacp_lag'            : 'enable sharing {} grouping {} algorithm address-based L3_L4 lacp', # Port1, Port list
        'create_static_mlt'          : 'enable sharing {} grouping {} algorithm address-based L3_L4', # Port1, Port list
        'create_syslog_server'       : # {0} = IP; {1} = VR; {2} = facility
                                       '''
                                       configure syslog add {0}:514 vr {1} {2}
                                       enable log target syslog {0}:514 vr {1} {2}
                                       configure log target syslog {0}:514 vr {1} {2} filter DefaultFilter severity Debug-Data
                                       configure log target syslog {0}:514 vr {1} {2} match Any
                                       configure log target syslog {0}:514 vr {1} {2} format timestamp seconds date Mmm-dd event-name condition priority host-name tag-name
                                       ''',

        'delete_all_syslog_servers'  : 'configure syslog delete all',
        'delete_cvlan'               : 'delete vlan {}', # VLAN id
        'delete_cvlan_uni'           : 'configure vlan {0} delete ports {1}', # {0} = VLAN id; {1} = port-list
        'delete_vm_files'            : 'rm /usr/local/vm/packages/*\ny',

        'enable_igmp_on_vlan'        : 'enable igmp vlan {} IGMPv{}', # VLAN name, IGMP Version 1/2/3

        'get_chassis_mac'            : 'str://show switch | include "System MAC"||^System MAC: +(\S+)',
        'get_cvlan_isid'             : 'str://show vlan {0} fabric attach assignments||^ +{0} +\S+ +(?:Static|Dynamic) +(\d+)', # VLAN id
        'get_cvlan_name'             : 'str://show vlan||^(\S+) +{0}\s', # VLAN id
        'get_ip_vr'                  : 'str://show vlan|| {}[ /].+? (\S+) *$', # IP
        'get_isid_cvlan'             : 'str://show vlan fabric attach assignments||^ +(\d+) +\S+ +Static +{0}', # Isid
        'get_mac_address'            : 'show switch||^System MAC: +(\S+)',
        'get_mlt_data'               : 'list://show sharing||^ +(?:((?:\d+:)?\d+)(?: +(?:\d+:)?\d+)? +(LACP|Static) +\d+ +)?\w+(?: +\w+)? +((?:\d+:)?\d+)',
        'get_vm_data'                : 'list://show vm detail | include Memory|CPUs|Slot||(?:Memory size: +(\d+) MB|CPUs: +(\d)|Slot: +(\d))',

        'list_all_vlans'             : 'dict-reverse://show vlan ||^(\S+) +(\d+) ',
        'list_fa_elements'           : 'list://show fabric attach elements||^((?:[\da-f]{2}-){5}[\da-f]{2})-((?:[\da-f]{2}-){3}[\da-f]{2}) +((?:\d+:)?\d+) +(.+?) +(?:\d+|None)\s\S',

        'port_disable_poe'           : 'disable inline-power ports {}', # Port list
        'port_enable_poe'            : 'enable inline-power ports {}', # Port list

        'set_cvlan_isid'             : 'configure vlan {0} add isid {1}', # {0} = VLAN id; {1} = i-sid 
        'set_cvlan_name'             : 'configure vlan {0} name {1}', # {0} = VLAN id; {1} = Name

    },
    'ERS Series': {
        'disable_more_paging'        : 'terminal length 0',
        'enable_context'             : 'enable',
        'config_context'             : 'config term',
        'port_config_context'        : 'interface Ethernet {}', # List of ports
        'exit_config_context'        : 'exit',
        'end_config'                 : 'end',
        'save_config'                : 'copy config nvram',

        'check_cvlan_exists'         : 'bool://show vlan id {0}||^{0}\s', # VLAN id
        'check_ntp_support'          : 'show ntp', # Used to check if NTP is supported; on ERS models which do not support NTP we expect to get an error

        'clear_cvlan_isid'           : 'no i-sid {1} vlan {0}', # {0} = VLAN id; {1} = i-sid 
        'clear_fa_auth_key'          : 'configure fabric attach ports {} authentication key default', # Port list

        'config_eapol_global'        : # (do not config multihost allow-non-eap-enable; it is for switch local MAC based authentication without RADIUS)
                                       '''
                                       eapol multihost radius-non-eap-enable
                                       eapol multihost use-radius-assigned-vlan
                                       eapol multihost non-eap-use-radius-assigned-vlan
                                       eapol multihost eap-packet-mode unicast
                                       eapol multihost non-eap-reauthentication-enable
                                       no eapol multihost non-eap-pwd-fmt ip-addr
                                       no eapol multihost non-eap-pwd-fmt port-number
                                       eapol enable
                                       fa extended-logging
                                       ''',
        'config_eapol_mhsa'          : 'eapol multihost auto-non-eap-mhsa-enable',
        'config_eapol_mirroring'     : {
            'enable'                 : 'eapol allow-port-mirroring',
            'disable'                : 'no eapol allow-port-mirroring',
                                       },
        'config_eapol_multivlan'     : 'eapol multihost multivlan enable', # This command may be obsolete on recent ERS models/software
        'config_failopen_vlan'       : 'eapol multihost fail-open-vlan vid {}', # VLAN id
        'config_radius_coa_reauth'   : 'radius dynamic-server client {0} process-reauthentication-requests', # Radius server; not implemented on all ERS models
        'config_radius_primary'      : # {0} = Primary Radius Server IP, {1} = Radius secret, {2} = 'acct-enable' or ''
                                       '''
                                       no radius use-management-ip
                                       radius server host {0} key {1} {2}
                                       radius accounting interim-updates enable
                                       radius dynamic-server client {0} secret {1}
                                       radius dynamic-server client {0} process-change-of-auth-requests
                                       radius dynamic-server client {0} process-disconnect-requests
                                       radius dynamic-server client {0} enable
                                       ''',
        'config_radius_reachability' : { # {0} = Dummy username, {1} = Dummy password
            'use-icmp'               : 'radius reachability mode use-icmp',
            'use-radius'             : 'radius reachability mode use-radius username {0} password {1}',
                                       },
        'config_radius_secondary'    : # {0} = Secondary Radius Server IP, {1} = Radius secret, {2} = 'acct-enable' or ''
                                       '''
                                       radius server host {0} secondary key {1} {2}
                                       radius dynamic-server client {0} secret {1}
                                       radius dynamic-server client {0} process-change-of-auth-requests
                                       radius dynamic-server client {0} process-disconnect-requests
                                       radius dynamic-server client {0} enable
                                       ''',

        'create_cvlan'               : 'vlan create {} type port', # VLAN id
        'create_cvlan_uni'           : { # {0} = VLAN id; {1} = port-list
            'tag'                    : 'vlan ports {1} tagging tagAll; vlan members add {0} {1}',
            'untag'                  : 'vlan ports {1} tagging untagAll; vlan members add {0} {1}',
                                       },
        'create_lacp_lag'            : '''
                                       lacp key {2} mlt-id {0}
                                       mlt 1 loadbalance advance
                                       mlt 1 learning disable
                                       interface fastEthernet {1}
                                          lacp key {2}
                                          lacp aggregation enable
                                          lacp mode passive
                                       exit
                                       ''', # MLT id, Port list, Key
        'create_ntp_server'          : 'ntp server {} enable', # IP
        'create_sntp_server1'        : 'sntp server primary address {}', # IP
        'create_sntp_server2'        : 'sntp server secondary address {}', # IP
        'create_static_mlt'          : '''
                                       mlt {0} member {1} learning disable
                                       mlt {0} loadbalance advance
                                       ''', # MLT id, Port list
        'create_vlacp_mlt'           : '''
                                       mlt {0} member {1} learning disable
                                       mlt {0} loadbalance advance
                                       vlacp macaddress 01:80:c2:00:00:0f
                                       interface fastEthernet {1}
                                          vlacp timeout short
                                          vlacp timeout-scale 5
                                          vlacp enable
                                       exit
                                       ''', # MLT id, Port list

        'delete_cvlan'               : 'vlan delete {0}', # {0} = VLAN id
        'delete_cvlan_uni'           : 'vlan members remove {0} {1}', # {0} = VLAN id; {1} = port-list
        'delete_ntp_server'          : 'no ntp server {}', # IP
        'delete_radius_coa_client'   : 'no radius dynamic-server client {}', # Client IP
        'delete_sntp_servers'        : 'no sntp enable; no sntp server primary; no sntp server secondary',

        'disable_more_paging'        : 'terminal length 0',
        'disable_password_security'  : 'no password security',
        'disable_coa_replay_protect' : 'no radius dynamic-server replay-protection',
        'disable_dhcp_relay'         : 'no ip dhcp-relay', # We only do this on ERS3500, to free up resources to enable eapol
        'disable_eapol_global'       : 'eapol disable',

        'enable_coa_replay_protect'  : 'radius dynamic-server replay-protection',
        'enable_fa_auth_key'         : 'configure fabric attach ports {} authentication enable', # Port list
        'enable_failopen'            : 'eapol multihost fail-open-vlan enable',
        'enable_failopen_continuity' : 'eapol multihost fail-open-vlan continuity-mode enable',
        'enable_more_paging'         : 'terminal length {}', # Terminal length, usually 23
        'enable_ntp'                 : 'ntp; clock source ntp',
        'enable_password_security'   : 'password security',
        'enable_sntp'                : 'sntp enable; clock source sntp',

        'get_autosave'               : 'str-lower://show autosave ||(Enabled|Disabled)',
        'get_chassis_mac'            : 'str://show sys-info||^MAC Address: +(\S+)',
        'get_clock_source'           : 'str://show clock detail ||System Clock Source +: +(\S+)',
        'get_cvlan_isid'             : 'str://show vlan i-sid {0}||^{0} +(\d+)', # VLAN id
        'get_cvlan_name'             : 'str://show vlan||^{0} +(\S.+\S) +Port', # VLAN id
        'get_fabric_mode'            : 'list://show fa agent ||(?:Fabric Attach Element Type: (Server|Proxy)|Fabric Attach Provision Mode: VLAN \((Standalone)\))',
        'get_isid_cvlan'             : 'str://show vlan i-sid||^(\d+) +{0}', # Isid
        'get_mac_address'            : 'show sys-info||^MAC Address: +(\S+)',
        'get_mlt_data'               : 'list://show mlt||^(\d+) +.+?[^#]([\d\/,-]+|NONE) +(?:Single|All) +\S+ +(Enabled|Disabled)(?: +(?:Trunk|Access))? +(NONE|\d+)',
        'get_password_security'      : 'str://show password security ||(enabled|disabled)',
        'get_spanning_tree_mode'     : 'str://show spanning-tree mode ||^Current STP Operation Mode: (\w+)',
        'get_stacking_mode'          : 'str://show sys-info ||^Operation Mode: +(Switch|Stack)',
        'get_terminal_length'        : 'int://show terminal ||Terminal length: (\d+)',

        'list_faclient_ports'        : {
            'Switch'                 : 'list://show fa elements ||^1\/(\d+) +Client',
            'Stack'                  : 'list://show fa elements ||^(\d\/\d+) +Client',
                                       },
        'list_fa_elements'           : 'list://show fa elements||^(?:(\d+/\d+|MLT\d+) +(\S+) +\d+ +\w / \w +((?:[\da-f]{2}:){5}[\da-f]{2}):((?:[\da-f]{2}:){3}[\da-f]{2}) +(\S+)|(\d+/\d+|MLT\d+) +.+?((?:success|fail)\S+)\s)',
        'list_faproxy_ports'         : {
            'Switch'                 : 'list://show fa elements ||^1\/(\d+) +Proxy',
            'Stack'                  : 'list://show fa elements ||^(\d\/\d+) +Proxy',
                                       },
        'list_mirror_monitor_ports'  : 'list://show port-mirroring||^Monitor Port: +((?:\d\/)?\d+)',
        'list_mlt_ports'             : 'list://show mlt ||^\d[\d ] .{16} ([\d\/,-]+)',
        'list_no_vlan_ports'         : 'list://show vlan interface vids||^((?:\d\/)?\d+)\s*$',
        'list_ntp_servers'           : 'list://show ntp server ||^(\d+\.\d+\.\d+\.\d+)',
        'list_radius_coa_clients'    : 'list://show radius dynamic-server ||^(\d+\.\d+\.\d+\.\d+)',
        'list_sntp_servers'          : 'list://show sntp ||server address: +([1-9]\d*\.\d+\.\d+\.\d+)',
        'list_uplink_ports'          : {
            'Server'                 : 'show isis interface ||^Port: ((?:\d\/)?\d+)',
            'Proxy'                  : 'show fa elements ||^(\d\/(\d+)) +Server',
            'StandaloneProxy'        : 'show fa uplink ||^  Port - ((?:\d\/)?\d+)',
                                       },

        'port_config_eap_common'     : '''
                                       default eapol multihost
                                       eapol multihost use-radius-assigned-vlan
                                       eapol multihost eap-packet-mode unicast
                                       eapol status auto re-authentication enable
                                       eapol radius-dynamic-server enable
                                       fa port-enable
                                       ''',
        'port_config_eap_mode'       : {
            'SHSA'                   : 'eapol multihost mac-max 1',
            'MHMA'                   : '', # port_config_eap_common above covers for MHMA already
            'MHSA'                   : 'eapol multihost auto-non-eap-mhsa-enable mhsa-no-limit',
                                       },
        'port_config_eap_type'       : {
            'Both'                   : # (do not config multihost allow-non-eap-enable; it is for switch local MAC based authentication without RADIUS)
                                       '''
                                       eapol multihost radius-non-eap-enable
                                       eapol multihost non-eap-use-radius-assigned-vlan
                                       ''',
            '802X'                   : '', # port_config_eap_common above covers for 802X already
            'NEAP'                   : # (do not config multihost allow-non-eap-enable; it is for switch local MAC based authentication without RADIUS)
                                       '''
                                       eapol multihost radius-non-eap-enable
                                       eapol multihost non-eap-use-radius-assigned-vlan
                                       no eapol multihost eap-protocol-enable
                                       ''',
                                       },
        'port_config_failopen_vlan'  : 'eapol multihost fail-open-vlan enable',
        'port_config_failopen_pvid'  : 'eapol multihost fail-open-vlan enable vid port-pvid',
        'port_config_faststart'      : {
            'STPG'                   : 'spanning-tree learning fast',
            'RSTP'                   : 'spanning-tree rstp learning enable; spanning-tree rstp edge-port true',
            'MSTP'                   : 'spanning-tree mstp learning enable; spanning-tree mstp edge-port true',
                                       },
        'port_config_multihost'      : 'eapol multihost enable', # This command may be obsolete on recent ERS models/software
        'port_config_reauth_timer'   : 'eapol re-authentication-period {}', # Value
        'port_config_traffic_control': 'eapol traffic-control {}', # 'in', 'in-out'

        'port_disable_eap'           : 'default eapol; default eapol multihost fail-open-vlan',
        'port_disable_fa'            : 'no fa port-enable',
        'port_disable_poe'           : 'interface fastEthernet {}; poe poe-shutdown', # Port list
        'port_enable_fa'             : 'fa port-enable',
        'port_enable_poe'            : 'interface fastEthernet {}; no poe-shutdown', # Port list
        'port_readd_vlan1'           : 'vlan members add 1 {}', # Port list

        'set_cvlan_isid'             : 'i-sid {1} vlan {0}', # {0} = VLAN id; {1} = i-sid
        'set_cvlan_name'             : 'vlan name {0} {1}', # {0} = VLAN id; {1} = Name
        'set_fa_auth_key'            : 'configure fabric attach ports {} authentication key {}', # Port list, Auth key
        'set_radius_encap'           : 'radius-server encapsulation {}', # pap|ms-chap-v2 ; this command does not exist on lower end ERS models (3600,3500)
        'set_timezone'               : 'clock time-zone {} {} {}', # Zone, hours-offset, minutes
        'set_vlan_cfgctrl_automatic' : 'vlan configcontrol automatic',
    },
    'ISW-Series': {
        'disable_more_paging'        : 'terminal length 0',
        'config_context'             : 'config term',
        'get_mgmt_ip_vlan_and_mask'  : 'tuple://show ip interface brief ||^VLAN (\d+) +{}/(\d+) +DHCP', # IP address; returns mask bits
        'get_mgmt_ip_gateway'        : 'str://show ip route ||^0\.0\.0\.0\/0 via (\d+\.\d+\.\d+\.\d+)',
        'set_mgmt_ip_gateway'        : 'ip route 0.0.0.0 0.0.0.0 {}', # Default Gateway IP
        'set_mgmt_ip'                : 'interface vlan {}; ip address {} {}; exit', # Mgmt VLAN, IP address, IP Mask
        'modify_admin_user'          : 'username admin privilege 15 password unencrypted {}', # Admin Password
        'default_admin_user'         : 'username admin privilege 15 password none',
        'delete_admin_user'          : 'no username admin',
        'create_cli_user'            : 'username {0} privilege 15 password unencrypted {1}; enable password {1}', # Username, Password
        'delete_cli_user'            : 'no username {}', # Username
        'set_snmp_version'           : 'snmp-server version v{}', # Version
        'set_snmp_read_community'    : 'snmp-server community v2c {} ro', # Community
        'set_snmp_write_community'   : 'snmp-server community v2c {} rw', # Community
        'create_snmp_v3_user'        : { # {0} = User; {1} = AuthType; {2} = AuthPassword; {3} = PrivType; {4} = PrivPassword; {5} = ro/rw
            'NoAuthNoPriv'           : '''
                                       snmp-server user {0} engine-id 800007e5017f000001
                                       snmp-server security-to-group model v3 name {0} group default_{5}_group
                                       ''',
            'AuthNoPriv'             : '''
                                       snmp-server user {0} engine-id 800007e5017f000001 {1} {2}
                                       snmp-server security-to-group model v3 name {0} group default_{5}_group
                                       ''',
            'AuthPriv'               : '''
                                       snmp-server user {0} engine-id 800007e5017f000001 {1} {2} priv {3} {4}
                                       snmp-server security-to-group model v3 name {0} group default_{5}_group
                                       ''',
                                       },
        'delete_snmp_communities'    : 'no snmp community v3 public; no snmp community v3 private',
        'delete_snmp_v3_default_user': 'no snmp-server user default_user engine-id 800007e5017f000001',
        'port_disable_poe'           : 'interface * 1/{}; poe mode disable', # Port list
        'port_enable_poe'            : 'poe mode enable', # Port list
        'end_config'                 : 'end',
    },
    'ISW-Series-Marvell': {
        'enable_context'             : 'enable',
        'config_context'             : 'configure',
        'disable_more_paging_cfg'    : 'setenv pagefilter 0',
#        'disable_more_paging_cfg'    : 'configure; setenv pagefilter 0; exit',
        'get_mgmt_ip_vlan'           : 'str://show fa elements ||^\S+ +FA Server +(\d+)',
        'get_mgmt_ip_mask_and_gw'    : 'list-diagonal://show ip dhcp client {} ||^ +(?:IP Address +: {}\/(\d+\.\d+\.\d+\.\d+)|Default Gateway: (\d+\.\d+\.\d+\.\d+))', #Mgmt VLAN, IP Address; returns dotted mask
        'set_mgmt_ip_gateway'        : 'default-gateway {}', # Default Gateway IP
        'set_mgmt_ip'                : 'interface vlan {}; ip address {} {}; exit', # Mgmt VLAN, IP address, IP Mask
        'modify_admin_user'          : 'account modify admin password {}', # Admin Password
        'default_admin_user'         : 'account modify admin password ""',
        'delete_admin_user'          : 'account delete admin',
        'create_cli_user'            : 'account add {} password {} level superuser', # Username, Password
        'delete_cli_user'            : 'account delete {}', # Username
        'set_snmp_version'           : 'snmp version v{}', # Version / Does not support v1
        'set_snmp_read_community'    : 'snmp delete-community name public; snmp create-community ro {}', # Community
        'set_snmp_write_community'   : 'snmp create-community rw {}', # Community
        'create_snmp_v3_user'        : { # {0} = User; {1} = AuthType; {2} = AuthPassword; {3} = PrivType; {4} = PrivPassword; {5} = ro/rw
            'NoAuthNoPriv'           : 'snmp create-user {0} access {5}',
            'AuthNoPriv'             : 'snmp create-user {0} access {5} {1} {2}',
            'AuthPriv'               : 'snmp create-user {0} access {5} {1} {2} {3} {4}', # Does not support aes
                                       },
        'delete_snmp_communities'    : 'snmp delete-community name public',
        'delete_snmp_v3_default_user': 'no snmp-server user default_user engine-id 800007e5017f000001',
        'end_config'                 : 'exit',
    },
}

Shell_Dict = { # Dictionary of all Linux shell commands used by this script
    'list_ntp_servers'           : 'list://ntpq -pn ||^[*+](\d+\.\d+\.\d+\.\d+)',
#    'get_time_zone'              : 'tuple://date +%Z%z ||^(\w+)([-+]\d\d)(\d\d)',
    'get_time_zone'              : 'tuple:// timedatectl ||Time zone: (\S+?)(?:/(\S+?))? \((\w+?), ([-+]\d\d)(\d\d)\)',
    'check_file_exists'          : 'bool://ls {1}{0}||^{1}{0}$', # Filename, Path
    'get_file_size'              : 'str://ls -l {1}{0}||(\d\d\d\d\d+) +\S+ +\S+ +\S+ +{1}{0} *$', # Filename, Path
    'grep_syslog_to_file'        : 'grep "{}" {} > {}', # Match string, File list (space separated), Output file
}

NBI_Query = { # GraphQl query / outValue = nbiQuery(NBI_Query['getDeviceUserData'], IP=deviceIp)
# QUERIES (General):
    'nbiAccess': {
        'json': '''
                {
                  administration {
                    serverInfo {
                      version
                    }
                  }
                }
                ''',  
        'key': 'version'
    },
    'get_peer_nickname': {
        'json': '''
                {
                  network {
                    device(ip: "<IP>") {
                      deviceData {
                        userData1
                      }
                    }
                  }
                }
                ''',
        'key': ''
    },
    'getDeviceSiteVariables': {
        'json': '''
                {
                  network {
                    device(ip: "<IP>") {
                      sitePath
                      customVariables {
                        globalAttribute
                        name
                        scopeCategory
                        value
                        valueType
                      } 
                    }
                  }
                }
                ''',
        'key': 'device'   
    },
    'getDeviceUserData': {
        'json': '''
                {
                  network {
                    device(ip: "<IP>") {
                      userData1
                      userData2
                      userData3
                      userData4
                    }
                  }
                }
                ''',
        'key': 'device'
    },
    'getSiteVariables': {
        'json': '''
                {
                  network {
                    siteByLocation(location: "<SITE>") {
                      customVariables {
                        globalAttribute
                        name
                        scopeCategory
                        value
                        valueType
                      } 
                    }
                  }
                }
                ''',
        'key': 'siteByLocation'
    },
    'getSiteList': {
        'json': '''
                {
                  network {
                    sites {
                      location
                    }
                  }
                }
                ''',
        'key': 'sites'
    },
    'getSitePath': {
        'json': '''
                {
                  network {
                    device(ip: "<IP>") {
                      sitePath
                    }
                  }
                }
                ''',
        'key': 'sitePath'
    },
    'getSiteDvrDomain': {
        'json': '''
                {
                  network {
                    siteByLocation(location: "<SITE>") {
                      fabricDvrDomainId
                    } 
                  }
                }
                ''',
        'key': 'fabricDvrDomainId'
    },
    'getDeviceAdminProfile': {
        'json': '''
                {
                  network {
                    device(ip:"<IP>") {
                      deviceData {
                        profileName
                      }
                    }
                  }
                }
                ''',
        'key': 'profileName'
    },
    'getAdminProfileCreds': {
        'json': '''
                {
                  administration {
                    profileByName(name:"<PROFILE>") {
                      authCred {
                        userName
                        loginPassword
                      }
                    }
                  }
                }
                ''',
        'key': 'authCred'
    },
    'getWorkflowList': {
        'json': '''
                {
                  workflows {
                    allWorkflows{
                      name
                      category
                      path
                    }
                  }
                }
                ''',
        'key': 'allWorkflows'
    },
    'checkSwitchXmcDb': {
        'json': '''
                {
                  network {
                    device(ip:"<IP>") {
                      id
                    }
                  }
                }
                ''',
        'key': 'device'
    },
    'check_device': {
        'json': '''
                {
                  network {
                    device(ip: "<IP>") {
                      down
                    }
                  }
                }
                ''',
        'key': 'device'
    },
    'getProfileCredentials': {
        'json': '''
                {
                  administration {
                    profileByName(name: "<PROFILE>") {
                      authCred {
                        userName
                        loginPassword
                      }
                    }
                  }
                }
                ''',
        'key': 'authCred'
    },
    'getDeviceFirmware': {
        'json': '''
                {
                  network {
                    device(ip: "<IP>") {
                      firmware
                    }
                  }
                }
                ''',
        'key': 'firmware'
    },
    'getWorkflowIds': {
        'json': '''
                {
                  workflows {
                    allWorkflows {
                      name
                      category
                      path
                      id
                    }
                  }
                }
                ''',
        'key': 'allWorkflows'
    },
    'getDevicesIpAndSerialData': {
        'json': '''
                {
                  network {
                    devices {
                      deviceData {
                        ipAddress
                        serialNumber
                      }
                    }
                  }
                }
                ''',
        'key': 'devices' # [{"deviceData": {"ipAddress": <IP>, "serialNumber": <SN>},...]
    },
    'getDeviceSerialNumber': {
        'json': '''
                {
                  network {
                    device(ip: "<IP>") {
                      deviceData {
                        serialNumber
                      }
                    }
                  }
                }
                ''',
        'key': 'serialNumber'
    },
    'getDeviceSerialAndMac': {
        'json': '''
                {
                  network {
                    device(ip: "<IP>") {
                      deviceData {
                        serialNumber
                        macAddress
                      }
                    }
                  }
                }
                ''',
        'key': 'deviceData'
    },
    'getDeviceData': {
        'json': '''
                {
                  network {
                    device(ip: "<IP>") {
                      firmware
                      sysName
                    }
                  }
                }
                ''',
        'key': 'device'
    },
    'checkSiteExists': {
        'json': '''
                {
                  network {
                    siteByLocation(location: "<SITE>") {
                      siteId
                    }
                  }
                }
                ''',
        'key': 'siteId'
    },
    'getAdminProfileCredentials': {
        'json': '''
                {
                  administration {
                    profileByName(name: "<PROFILENAME>") {      # null OR {                               
                      authCred {                                #           "authCred": {                 
                        loginPassword                           #             "loginPassword": "rwa",     
                        type                                    #             "type": "SSH",              
                        userName                                #             "userName": "rwa"           
                      }                                         #           },                            
                      readSecLevel                              #           "readSecLevel": "AuthNoPriv", 
                      readCredential {                          #           "readCredential": {           
                        authPassword                            #             "authPassword": "passwdvbn",
                        authType                                #             "authType": "SHA",          
                        communityName                           #             "communityName": "",        
                        privPassword                            #             "privPassword": "",         
                        privType                                #             "privType": "None",         
                        snmpType                                #             "snmpType": 3,              
                        userName                                #             "userName": "admin"         
                      }                                         #           },                            
                      writeSecLevel                             #           "writeSecLevel": "AuthNoPriv",
                      writeCredential {                         #           "writeCredential": {          
                        authPassword                            #             "authPassword": "passwdvbn",
                        authType                                #             "authType": "SHA",          
                        communityName                           #             "communityName": "",        
                        privPassword                            #             "privPassword": "",         
                        privType                                #             "privType": "None",         
                        snmpType                                #             "snmpType": 3,              
                        userName                                #             "userName": "admin"         
                      }                                         #           }                             
                    }                                           #         }                               
                  }
                }
                ''',
        'key': 'profileByName'
    },
    'listRunningWorkflows': {
        'json': '''
                {
                  workflows {
                    activeExecutions {     # [] OR [{
                      workflowName         #          "workflowName": "Onboard VSP"
                    }                      #       }]
                  }
                }
                ''',
        'key': 'activeExecutions'
    },


# QUERIES (Access Control):
    'nacConfig': {
        'json': '''
                {
                  accessControl {
                    switch(ipAddress: "<IP>") {
                      primaryGateway
                      secondaryGateway
                      sharedSecret
                      radiusAccountingEnabled
                    }
                  }
                }
                ''',
        'key': 'switch'
    },
    'checkSwitchNacConfig': {
        'json': '''
                {
                  accessControl {
                    switch(ipAddress: "<IP>") {
                      ipAddress
                    }
                  }
                }
                ''',
        'key': 'switch'
    },
    'getNacRules': {
        'json': '''
                {
                  accessControl {
                    configuration(name: "<CONFIGNAME>") {
                      aaaConfiguration
                      name
                      portalConfiguration
                      customRules {
                        enabled
                        nacProfile
                        name
                      }
                    }
                  }
                }
                ''',
        'key': 'customRules'
    },
    'getNacGroup': {
        'json': '''
                {
                  accessControl {
                    groupInfoByName(name: "<PROFILENAME>") {
                      description
                      dynamic
                      name
                      type
                    }
                  }
                }
                ''',
        'key': 'groupInfoByName'
    },
    'getNacEngineGroups': {
        'json': '''
                {
                  accessControl {
                    allEngineGroups {
                      nacConfiguration
                      name
                    }
                  }
                }
                ''',
        'key': 'allEngineGroups'
    },
    'getNacGroupEngineIPs': {
        'json': '''
                {
                  accessControl {
                    enginesForGroup(name: "<NACGROUP>") {
                      ipAddress
                    }
                  }
                }
                ''',
        'key': 'enginesForGroup'
    },
    'getNacLocationGroups': {
        'json': '''
                {
                  accessControl {
                    groupNamesByType(typeString: "LOCATION")
                  }
                }
                ''',
        'key': 'groupNamesByType'
    },
    'getNacEngineLoadBalancing': {
        'json': '''
                {
                  accessControl {
                    engineGroup(name: "<NACGROUP>") {
                      loadBalancingEnabled
                    }
                  }
                }
                ''',
        'key': 'loadBalancingEnabled'
    },
    'getNacEngineLoadBalancingIPs': {
        'json': '''
                {
                  accessControl {
                    engineGroup(name: "<NACGROUP>") {
                      loadBalancerIps
                    }
                  }
                }
                ''',
        'key': 'loadBalancerIps'
    },
    'getNacEngineLoadBalancing': {
        'json': '''
                {
                  accessControl {
                    engineGroup(name: "<NACGROUP>") {
                      loadBalancingEnabled
                      loadBalancerIps
                    }
                  }
                }
                ''',
        'key': 'engineGroup'
    },


# QUERIES (Policy):
    'getPolicyDomains': {
        'json': '''
                {
                  policy {
                    domainNames
                  }
                }
                ''',
        'key': 'domainNames'
    },
    'getDevicePolicyDomain': {
        'json': '''
                {
                  policy{
                    domainNameByIp(ip:"<IP>")   # null or "name"
                  }
                }
                ''',
        'key': 'domainNameByIp'
    },
    'getPolicyVlanIslands': {
        'json': '''
                {
                  policy {
                    pviIslands(input: {
                      domainName: <POLICYDOMAIN>
                    }) {
                      data {                          # null OR [{
                        defaultIsland                 #             "defaultIsland": true|false,
                        name                          #             "name": "Default Island"
                      }                               #         }]
                    }
                  }
                }
                ''',
        'key': 'data'
    },
    'getPolicyVlanIslandDevices': {
        'json': '''
                {
                  policy{
                    pviIsland(input:{
                      domainName: "<POLICYDOMAIN>"
                      name: "<TOPOLOGY>"
                    }) {
                      data {
                        devices {       # [] OR [{
                          name          #          "name": "10.9.193.20"
                        }               #       }]
                      }
                      message
                      status
                    }
                  }
                }
                ''',
        'key': 'devices'
    },


# MUTATIONS (General):
    'customActionTask': ''' # This is not a mutation in itself; its json which gets replaced into addSiteCustomActionTaskList below as <TASKLIST>
        {
          enabled: true
          vendor: "<VENDOR>"
          family: "<FAMILY>"
          topology: "<TOPOLOGY>"
          task: "<TASKPATH>"
        }
    ''',
    'addSiteCustomActionTaskList': {
        'json': '''
                mutation{
                  network{
                    modifySite(input:{
                      siteLocation: "<SITEPATH>"
                      siteConfig:{
                        customActionsConfig:{
                          mutationType: ADD
                          customActionConfig: [
                            <TASKLIST>
                          ]
                        }
                      }
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'rediscover_device': {
        'json': '''
                mutation {
                  network {
                    rediscoverDevices(input: {devices: {ipAddress: "<IP>"}}) {
                      status
                      message
                    }
                  }
                }
                ''',
    },
    'delete_device': {
        'json': '''
                mutation {
                  network {
                    deleteDevices(input:{
                      removeData: true
                      devices: {
                        ipAddress:"<IP>"
                      }
                    }) {
                      status
                      message
                    }
                  }
                }
                ''',
    },
    'create_device': {
        'json': '''
                mutation {
                  network {
                    createDevices(input:{
                      devices: {
                        ipAddress:"<IP>"
                        siteLocation:"<SITE>"
                        profileName:"<PROFILE>"
                      }
                    }) {
                      status
                      message
                    }
                  }
                }
                ''',
    },
    'createSitePath': {
        'json': '''
                mutation {
                  network {
                    createSite(input: {
                      siteLocation: "<SITEPATH>"
                      siteConfig: {
                        customActionsConfig: {
                          mutationType: REMOVE_ALL
                        }
                        actionsConfig: {
                          addSyslogReceiver: true
                          addTrapReceiver: true
                          autoAddDevices: true
                          addToArchive: true
                        }
                      }
                    })
                    {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'executeWorkflow': {
        'json': '''
                mutation {
                  workflows {
                    startWorkflow(input: {
                      id: <ID>,
                      variables: <JSONINPUTS>
                    })
                    {
                      message
                      status
                      executionId
                      errorCode
                    }
                  }
                }
                ''',
        'key': 'executionId'
    },
   'setDeviceUserData': {
        'json': '''
                mutation {
                  network {
                    configureDevice(input: {
                      deviceConfig:{
                        ipAddress: "<IP>",
                        deviceAnnotationConfig: {
                          userData1: "<UD1>",
                          userData2: "<UD2>",
                          userData3: "<UD3>",
                          userData4: "<UD4>"
                        }
                      }
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
   'setDeviceNickName': {
        'json': '''
                mutation {
                  network {
                    configureDevice(input: {
                      deviceConfig:{
                        ipAddress: "<IP>"
                        deviceAnnotationConfig: {
                          nickName: "<NICKNAME>"
                        }
                      }
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
   'setDeviceTopoRole': {
        'json': '''
                mutation {
                  network {
                    configureDevice(input: {
                      deviceConfig:{
                        ipAddress: "<IP>"
                        generalConfig: {
                          topologyRole: <ROLE> # ANY,APPLIANCE,FIREWALL,GATEWAY,Hypervisor,L2_ACCESS,L2_LEAF,L3_ACCESS,L3_CORE,L3_DISTRIBUTION,L3_LEAF,L3_SPINE,LOAD_BALANCER,Server,WAN
                        }
                      }
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
   'setDeviceNickNameAndTopoRole': {
        'json': '''
                mutation {
                  network {
                    configureDevice(input: {
                      deviceConfig:{
                        ipAddress: "<IP>"
                        generalConfig: {
                          topologyRole: <ROLE> # ANY,APPLIANCE,FIREWALL,GATEWAY,Hypervisor,L2_ACCESS,L2_LEAF,L3_ACCESS,L3_CORE,L3_DISTRIBUTION,L3_LEAF,L3_SPINE,LOAD_BALANCER,Server,WAN
                        }
                        deviceAnnotationConfig: {
                          nickName: "<NICKNAME>"
                        }
                      }
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
   'enforceDeviceConfiguration': {
        'json': '''
                mutation {
                  network {
                    configureDevice(input: {
                      enforceAll:        false
                      enforceSystem:     false
                      enforceTopology:   false
                      enforceVlan:       true
                      enforceVrf:        false
                      enforceClip:       false
                      enforceServices:   false
                      enforceLag:        false
                      enforcePortAlias:  false
                      enforcePortVlan:   true
                      enforcePortFabric: false
                      timeout: 30
                      deviceConfig: {
                        ipAddress:"<IP>"
                      }
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
   },
   'setDeviceWebHttps': {
        'json': '''
                mutation {
                  network {
                    configureDevice (input:{
                      deviceConfig:{
                        ipAddress: "<IP>"
                        generalConfig:{
                          deviceWebViewUrl: "https://%IP"
                        }
                      }
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'changeDeviceAdminProfile': {
        'json': '''
                mutation {
                  network {
                    configureDevice(input:{
                      deviceConfig: {
                        ipAddress: "<IP>"
                        generalConfig: {
                          adminProfile: "<PROFILE>"
                        }
                      }
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'deleteDiscoveredDevice': { # Always succeeds, even if IP does not exist under Discovered devices
        'json': '''
                mutation{
                  network{
                    deleteDiscoveredDevices(input:{
                      devices:[{
                        ipAddress: "<IP>"
                      }]
                      removeData:true
                    }
                    ) {
                      message
                      status
                    }
                  }
                }
                ''',
    },


# MUTATIONS (Access Control):
    'cloneNacProfile': {
        'json': '''
                mutation {
                  accessControl {
                    createDCMVirtualAndPhysicalNetwork(input: {
                      vlanName: "untagged"
                      primaryVlanId: 0
                      name: "<NAME>"
                      nacConfig: "<CONFIGNAME>"
                    }) {
                      status
                      message
                    }
                  }
                }
                ''',
    },
    'accessControlCreateSwitch': {
        'json': '''
                mutation {
                  accessControl {
                    createSwitch(input: {
                      nacApplianceGroup: "<NACGROUP>",
                      ipAddress: "<IP>",
                      switchType: L2_OUT_OF_BAND,
                      primaryGateway: "<ENGINE1>",
                      secondaryGateway: "<ENGINE2>",
                      authType: NONE,
                      attrsToSend: "<RADIUSTEMPLATE>",
                      radiusAccountingEnabled: true,
                      overrideSharedSecret: true,
                      sharedSecret: "<SHAREDSECRET>"
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'accessControlDeleteSwitch': {
        'json': '''
                mutation {
                  accessControl {
                    deleteSwitch(input: {
                      searchKey: "<IP>"
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'createNacProfile': {
        'json': '''
                mutation {
                  accessControl {
                    createDCMVirtualAndPhysicalNetwork(input: {
                      vlanName: "<NAME>"
                      primaryVlanId: <VID>
                      name: "<NAME>"
                      nacConfig: "<CONFIGNAME>"
                    }) {
                      status
                      message
                    }
                  }
                }
                ''',
    },
    'removeNacProfile': {
        'json': '''
                mutation {
                  accessControl {
                    removeDCMVirtualAndPhysicalNetwork(input: {
                      primaryVlanId: <VID>
                      name: "<NAME>"
                      nacConfig: "<CONFIGNAME>"
                      removeEndSystemGroup: true
                    }) {
                      status
                      message
                    }
                  }
                }
                ''',
    },
    'accessControlEnforceEngines': {
        'json': '''
                mutation {
                  accessControl {
                    enforceAccessControlEngines(input: {
                      engineGroup: "<NACGROUP>",
                      ignoreWarnings: true
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'accessControlCreateLocationGroup': {
        'json': '''
                mutation {
                  accessControl {
                    createGroup(input: {
                      name: "<LOCATIONGROUP>"
                      type: LOCATION
                    }) {
                      status
                      message
                    }
                  }
                }
                ''',
    },
    'accessControlAddSwitchToLocation': {
        'json': '''
                mutation {
                  accessControl {
                    addEntryToGroup(input: {
                      description: "<DESCRIPTION>"
                      group: "<LOCATIONGROUP>"
                      value: "<IP>:*"
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'accessControlRemoveSwitchFromLocation': {
        'json': '''
                mutation {
                  accessControl {
                    removeEntryFromGroup(input: {
                      group: "<LOCATIONGROUP>"
                      value: "<IP>"
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },


# MUTATIONS (Policy):
    'openPolicyDomain': {
        'json': '''
                {
                  policy {
                    openDomain(input: {
                      name: "<POLICYDOMAIN>"
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'lockOpenedPolicyDomain': {
        'json': '''
                mutation{
                  policy{
                    lockDomain(input:{
                      revoke: <FORCEFLAG>   # true|false
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'unlockOpenedPolicyDomain': {
        'json': '''
                mutation{
                  policy{
                    unlockDomain(input:{}) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'closePolicyDomain': {
        'json': '''
                {
                  policy {
                    closeDomain(input: {
                      name: "<POLICYDOMAIN>"
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'savePolicyDomain': {
        'json': '''
                mutation{
                  policy{
                    saveDomain(input:{
                      name: "<POLICYDOMAIN>"
                      closeDomain: <CLOSEFLAG>   # true|false
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'removeDeviceFromPolicyDomain': {
        'json': '''
                mutation{
                  policy{
                    mutateDeviceList(input:{
                      domainName: "<POLICYDOMAIN>"
                      mutationType: REMOVE
                      devices: ["<IP>"]
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'addDeviceToPolicyDomain': {
        'json': '''
                mutation{
                  policy{
                    mutateDeviceList(input:{
                      domainName: "<POLICYDOMAIN>"
                      mutationType: ADD
                      devices: ["<IP>"]
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'addDeviceToPolicyVlanIsland': {
        'json': '''
                mutation{
                  policy{
                    mutatePviIsland(input:{
                      domainName: "<POLICYDOMAIN>"
                      dataIdentifier: "<TOPOLOGY>"
                      mutationType: MODIFY
                      mutationData:{
                        addIps:["<IP>"]
                      }
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'enforcePolicyDomain': {
        'json': '''
                mutation{
                  policy{
                    enforceDomain(input:{
                      name:"<POLICYDOMAIN>"
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
}


RESTCONF = { # RESTCONF call / outValue = restconfCall(RESTCONF["createVlan"], NAME="test", VID="666")
    'listVlans': {
        'http' : 'GET',
        'uri'  : 'openconfig-vlan:vlans',
        'query': 'depth=3',
        'key'  : 'vlan',
    },
    'getVlanConfig': {
        'http' : 'GET',
        'uri'  : 'openconfig-vlan:vlans/vlan=<VID>/config',
        'key'  : 'openconfig-vlan:config',
    },
    'createVlan': {
        'http' : 'POST',
        'uri'  : 'openconfig-vlan:vlans',
        'body' : '''
                {
                    "openconfig-vlan:vlans": [
                        {
                            "config": {
                                "name": "<NAME>", 
                                "vlan-id": <VID>
                            }
                        }
                    ]
                }
                ''',
    },
    'deleteVlan': {
        'http' : 'DELETE',
        'uri'  : 'openconfig-vlan:vlans/vlan=<VID>',
    },
}


SNMP_Request = { # outValue = snmpGet|snmpSet|snmpWalk(SNMP_Request['<name>'], [instance=<instance>], [value=<value>])
# SAMPLE Syntax:
#   'queryName|mibName': {
#       'oid': [<oidName>:]<singleOid> | [<listOf>], # For get & set; no leading dot; optional "oidName:" prepended
#       'asn': <ASN_?> | [<listOf>],                 # Only for set, mandatory
#       'set': <value> | [<listOf>],                 # Only for set, optional
#       'map': {'key1': <val1>, 'key2': <val2> }     # Mapping ASCII values to int values
#   },
    'ifName': { # Walk as is; Get supply instance
        'oid': 'ifName',
        'asn': ASN_OCTET_STR, #DisplayString
    },
    'ifAdminStatus': { # Walk as is; Get|Set supply instance
        'oid': 'ifAdminStatus',
        'asn': ASN_INTEGER, #INTEGER {up(1), down(2), testing(3)
    },
    'ifAlias': { # Walk as is; Get|Set supply instance
        'oid': 'ifAlias',
        'asn': ASN_OCTET_STR_PRINTABLE, #DisplayString (SIZE(0..64))
    },
    'ifName_ifAlias': { # Walk as is; Get supply instance
        'oid': ['ifName', 'ifAlias'],
    },
    'disableIqAgent': { # Get|Set only; supply no instance
        'oid': 'rcCloudIqAgentEnable: 1.3.6.1.4.1.2272.1.230.1.1.1.0',
        'asn': ASN_INTEGER, #TruthValue = INTEGER { true(1), false(2) }
        'set': 2,
    },
    'enableIqAgent': { # Get|Set only; supply no instance
        'oid': 'rcCloudIqAgentEnable: 1.3.6.1.4.1.2272.1.230.1.1.1.0',
        'asn': ASN_INTEGER, #TruthValue = INTEGER { true(1), false(2) }
        'set': 1,
    },
    'rcCloudIqAgentEnable': { # Get|Set only; supply no instance
        'oid': 'rcCloudIqAgentEnable: 1.3.6.1.4.1.2272.1.230.1.1.1.0',
        'asn': ASN_INTEGER, #TruthValue = INTEGER { true(1), false(2) }
    },
    'rcSshGlobalEnable': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalEnable: 1.3.6.1.4.1.2272.1.34.1.11.0',
        'asn': ASN_INTEGER, #INTEGER { false(0), true(1), secure(2) }
    },
    'rcSshGlobalClientEnable': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalClientEnable: 1.3.6.1.4.1.2272.1.34.1.24.0',
        'asn': ASN_INTEGER, #TruthValue = INTEGER { true(1), false(2) }
    },
    'rcSshGlobalSftpEnable': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalSftpEnable: 1.3.6.1.4.1.2272.1.34.1.19.0',
        'asn': ASN_INTEGER, #TruthValue = INTEGER { true(1), false(2) }
    },
    'rcSshGlobalPort': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalPort: 1.3.6.1.4.1.2272.1.34.1.2.0',
        'asn': ASN_INTEGER, #INTEGER (1..49151)
    },
    'rcSshGlobalMaxSession': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalMaxSession: 1.3.6.1.4.1.2272.1.34.1.3.0',
        'asn': ASN_INTEGER, #INTEGER (0..8)
    },
    'rcSshGlobalTimeout': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalTimeout: 1.3.6.1.4.1.2272.1.34.1.4.0',
        'asn': ASN_INTEGER, #INTEGER (1..120)
    },
    'rcSshGlobalRsaAuth': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalRsaAuth: 1.3.6.1.4.1.2272.1.34.1.7.0',
        'asn': ASN_INTEGER, #TruthValue = INTEGER { true(1), false(2) }
    },
    'rcSshGlobalDsaAuth': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalDsaAuth: 1.3.6.1.4.1.2272.1.34.1.8.0',
        'asn': ASN_INTEGER, #TruthValue = INTEGER { true(1), false(2) }
    },
    'rcSshGlobalPassAuth': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalPassAuth: 1.3.6.1.4.1.2272.1.34.1.9.0',
        'asn': ASN_INTEGER, #TruthValue = INTEGER { true(1), false(2) }
    },
    'rcSshGlobalKeyboardInteractiveAuth': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalKeyboardInteractiveAuth: 1.3.6.1.4.1.2272.1.34.1.20.0',
        'asn': ASN_INTEGER, #TruthValue = INTEGER { true(1), false(2) }
    },
    'rcSshGlobalX509AuthEnable': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalX509AuthEnable: 1.3.6.1.4.1.2272.1.34.1.25.0',
        'asn': ASN_INTEGER, #TruthValue = INTEGER { true(1), false(2) }
    },
    'rcSshGlobalX509AuthCertCAName': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalX509AuthCertCAName: 1.3.6.1.4.1.2272.1.34.1.31.0',
        'asn': ASN_OCTET_STR_PRINTABLE, #DisplayString (SIZE(0..45))
    },
    'rcSshGlobalX509AuthCertSubjectName': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalX509AuthCertSubjectName: 1.3.6.1.4.1.2272.1.34.1.30.0',
        'asn': ASN_OCTET_STR_PRINTABLE, #DisplayString (SIZE(0..45))
    },
    'rcSshGlobalX509AuthUsernameOverwrite': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalX509AuthUsernameOverwrite: 1.3.6.1.4.1.2272.1.34.1.27.0',
        'asn': ASN_INTEGER, #TruthValue = INTEGER { true(1), false(2) }
    },
    'rcSshGlobalX509AuthUsernameStripDomain': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalX509AuthUsernameStripDomain: 1.3.6.1.4.1.2272.1.34.1.28.0',
        'asn': ASN_INTEGER, #TruthValue = INTEGER { true(1), false(2) }
    },
    'rcSshGlobalX509AuthUsernameUseDomain': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalX509AuthUsernameUseDomain: 1.3.6.1.4.1.2272.1.34.1.29.0',
        'asn': ASN_OCTET_STR_PRINTABLE, #DisplayString (SIZE(0..255))
    },
    'rcSshGlobalX509AuthRevocationCheckMethod': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalX509AuthRevocationCheckMethod: 1.3.6.1.4.1.2272.1.34.1.26.0',
        'asn': ASN_INTEGER, #INTEGER { ocsp(1), none(2) }
        'map': { 'ocsp': 1, 'none': 2 }
    },
    'rcSshAuthType': { # Get|Set only; supply no instance
        'oid': 'rcSshAuthType: 1.3.6.1.4.1.2272.1.34.1.21.0',
        'asn': ASN_OCTET_STR_HEX, #BITS { hmacSha1(0), aeadAes128GcmSsh(1), aeadAes256GcmSsh(2), hmacSha2256(3) }
    },
    'rcSshEncryptionType': { # Get|Set only; supply no instance
        'oid': 'rcSshEncryptionType: 1.3.6.1.4.1.2272.1.34.1.22.0',
        'asn': ASN_OCTET_STR_HEX, #BITS { aes128Cbc(0), aes256Cbc(1), threeDesCbc(2), aeadAes128GcmSsh(3), aeadAes256GcmSsh(4), aes128Ctr(5),
                            #       rijndael128Cbc(6), aes256Ctr(7), aes192Ctr(8), aes192Cbc(9), rijndael192Cbc(10), blowfishCbc(11) }
    },
    'rcSshKeyExchangeMethod': { # Get|Set only; supply no instance
        'oid': 'rcSshKeyExchangeMethod: 1.3.6.1.4.1.2272.1.34.1.23.0',
        'asn': ASN_OCTET_STR_HEX, #BITS { diffieHellmanGroup14Sha1(0), diffieHellmanGroup1Sha1(1) -- obsolete, diffieHellmanGroupExchangeSha256(2) }
    },
}

SNMP_TruthValue = { # Mapping input enable/disable
    'enable' : 1, # true
    'disable': 2, # false
}








#
# INIT: Init Debug & Sanity flags based on input combos
#
try:
    if emc_vars['userInput_sanity'].lower() == 'enable':
        Sanity = True
    elif emc_vars['userInput_sanity'].lower() == 'disable':
        Sanity = False
except:
    pass
try:
    if emc_vars['userInput_debug'].lower() == 'enable':
        Debug = True
    elif emc_vars['userInput_debug'].lower() == 'disable':
        Debug = False
except:
    pass


# --> Insert Ludo Threads library here if required <--


# --> XMC Python script actually starts here <--


#
# MAIN:
#
def main():
    print "{} version {} on XIQ-SE/XMC version {}".format(scriptName(), __version__, emc_vars["serverVersion"])
    nbiAccess = nbiQuery(NBI_Query['nbiAccess'], returnKeyError=True)
    if nbiAccess == None:
        exitError('This XMC Script requires access to the GraphQl North Bound Interface (NBI). Make sure that XMC is running with an Advanced license and that your user profile is authorized for Northbound API.')

    # Obtain Info on switch and from XMC
    setFamily(CLI_Dict) # Sets global Family variable

    # Disable more paging
    sendCLI_showCommand(CLI_Dict[Family]['disable_more_paging'])

    # Enter privExec
    sendCLI_showCommand(CLI_Dict[Family]['enable_context'])

    # Enter Config context
    sendCLI_configCommand(CLI_Dict[Family]['config_context'])

    # Save config & exit
    sendCLI_configChain(CLI_Dict[Family]['end_save_config'])

    # Print summary of config performed
    printConfigSummary()

    # Make XMC re-discover the switch
    if nbiMutation(NBI_Query['rediscover_device'].replace('<IP>', emc_vars['deviceIP'])):
        print "Initiated XMC rediscovery of switch"
    else:
        print "Failed to trigger XMC rediscovery of switch; perform manually"


#main()
