#
# CLI functions - (use of rollback requires rollback.py)
# cli.py v28
#
import re
import time                         # Used by sendCLI_configChain & sendCLI_configChain2 with 'sleep' & 'block directives
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
RegexEmbeddedErrMode = re.compile('^#error +(fail|stop|continue) *$')
RegexEmbeddedSleep = re.compile('^#sleep  +(\d+) *$')
RegexEmbeddedWarpBlock = re.compile('^#block +(start|execute)(?: +(\d+))? *$')
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

def sendCLI_configCommand(cmd, returnCliError=False, msgOnError=None, waitForPrompt=True, historyAppend=True): # v5 - Send a CLI config command
    global LastError
    cmd = re.sub(r':\/\/', ':' + chr(0) + chr(0), cmd) # Mask any https:// type string
    cmd = re.sub(r' *\/\/ *', r'\n', cmd) # Convert "//" to "\n" for embedded // passwords
    cmd = re.sub(r':\x00\x00', r'://', cmd) # Unmask after // replacemt
    cmdStore = re.sub(r'\n.+$', '', cmd, flags=re.DOTALL) # Strip added "\n"+[yn] or // passwords
    if Sanity:
        print "SANITY> {}".format(cmd)
        if historyAppend:
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
        if historyAppend:
            ConfigHistory.append(cmdStore)
        LastError = None
        return True
    else:
        exitError(resultObj.getError())

def sendCLI_configChain(chainStr, returnCliError=False, msgOnError=None, waitForPrompt=True, historyAppend=True, abortOnError=True): # v6 - Send a list of config commands
    # Syntax: chainStr can be a multi-line string where individual commands are on new lines or separated by the semi-colon ";" character
    # Some embedded directive commands are allowed, these must always begin with the hash "#" character:
    # #error fail       : If a subsequent command generates an error, make the entire script fail
    # #error stop       : If a subsequent command generates an error, do not fail the script but stop processing firther commands
    # #error continue   : If a subsequent command generates an error, ignore it and continue executing remaining commands
    # #sleep <secs>     : Sleep for specified seconds
    cmdList = configChain(chainStr)

    # Check if last command is a directive, as we have special processing for the last line and don't want directives there
    while RegexEmbeddedWarpBlock.match(cmdList[-1]) or RegexEmbeddedErrMode.match(cmdList[-1]) or RegexEmbeddedSleep.match(cmdList[-1]):
        cmdList.pop() # We just pop it off, they serve no purpose as last line anyway

    successStatus = True
    for cmd in cmdList[:-1]: # All but last
        embeddedErrMode = RegexEmbeddedErrMode.match(cmd)
        embeddedSleep = RegexEmbeddedSleep.match(cmd)
        if embeddedErrMode:
            errorMode = embeddedErrMode.group(1)
            returnCliError = False if errorMode == 'fail' else True
            abortOnError = True if errorMode == 'stop' else False
            continue # After setting the above, we skip the embedded command
        elif embeddedSleep:
            time.sleep(embeddedSleep.group(1))
            continue # Next command
        success = sendCLI_configCommand(cmd, returnCliError, msgOnError, historyAppend=historyAppend)
        if not success:
            successStatus = False
            if abortOnError:
                return False
    # Last now
    success = sendCLI_configCommand(cmdList[-1], returnCliError, msgOnError, waitForPrompt, historyAppend)
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
