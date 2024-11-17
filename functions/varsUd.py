#
# Device UserData1-4 input (requires apiXmc.py and apiXmcDict.py call getDeviceUserData)
# varsUd.py v2
#

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
