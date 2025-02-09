#
# Read Custom Site Variables (requires apiXmc.py and apiXmcDict.py calls: getDeviceSiteVariables + getSiteVariables)
# varsSite.py v8
# 
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
