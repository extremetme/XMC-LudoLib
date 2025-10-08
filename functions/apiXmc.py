#
# XMC GraphQl NBI functions - (requires apiBase.py)
# apiXmc.py v16
#
LastNbiError = None
NbiUrl = None

def nbiQuery(jsonQueryDict, debugKey=None, returnKeyError=False, **kwargs): # v8 - Makes a GraphQl query of XMC NBI; if returnKey provided returns that key value, else return whole response
    global LastNbiError
    jsonQuery = replaceKwargs(jsonQueryDict['json'], kwargs) # Might be unicode
    returnKey = jsonQueryDict['key'] if 'key' in jsonQueryDict else None
    debug(u"NBI Query:\n{}\n".format(jsonQuery))
    response = nbiSessionPost(jsonQuery, returnKeyError) if NbiUrl else emc_nbi.query(jsonQuery)
    debug("nbiQuery response = {}".format(response))
    if response == None: # Should only happen from nbiSessionPost if returnKeyError=True
        return None
    if 'errors' in response: # Query response contains errors
        if returnKeyError: # If we asked to return upon NBI error, then the error message will be held in LastNbiError
            LastNbiError = response['errors'][0].message
            return None
        abortError(u"nbiQuery for\n{}".format(jsonQuery), response['errors'][0].message)
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
        abortError(u"nbiQuery for\n{}".format(jsonQuery), 'Key "{}" was not found in query response'.format(returnKey))

    # Else, return the full response
    if Debug:
        if debugKey: debug("{} = {}".format(debugKey, response))
        else: debug("nbiQuery response = {}".format(response))
    return response

def nbiMutation(jsonQueryDict, returnKeyError=False, debugKey=None, **kwargs): # v9 - Makes a GraphQl mutation query of XMC NBI; returns true on success
    global LastNbiError
    jsonQuery = replaceKwargs(jsonQueryDict['json'], kwargs) # Might be unicode
    returnKey = jsonQueryDict['key'] if 'key' in jsonQueryDict else None
    if Sanity:
        printLog(u"SANITY - NBI Mutation:\n{}\n".format(jsonQuery))
        LastNbiError = None
        return True
    printLog(u"NBI Mutation Query:\n{}\n".format(jsonQuery))
    response = nbiSessionPost(jsonQuery, returnKeyError) if NbiUrl else emc_nbi.query(jsonQuery)
    debug("nbiQuery response = {}".format(response))
    if 'errors' in response: # Query response contains errors
        if returnKeyError: # If we asked to return upon NBI error, then the error message will be held in LastNbiError
            LastNbiError = response['errors'][0].message
            return None
        abortError(u"nbiQuery for\n{}".format(jsonQuery), response['errors'][0].message)

    foundKey, returnStatus, returnMessage = recursionStatusSearch(response)
    if foundKey:
        debug("nbiMutation status = {} / message = {}".format(returnStatus, returnMessage))
    elif not returnKeyError:
        # If status key not found, raise error
        abortError(u"nbiMutation for\n{}".format(jsonQuery), 'Key "status" was not found in query response')

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
            abortError(u"nbiMutation for\n{}".format(jsonQuery), 'Key "{}" was not found in mutation response'.format(returnKey))
        return True
    else:
        LastNbiError = returnMessage
        return False
