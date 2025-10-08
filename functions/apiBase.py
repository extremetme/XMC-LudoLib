#
# XMC GraphQl & RESTCONF & XIQ API required functions
# apiBase.py v7
#
from java.util import LinkedHashMap
HTTP_RESONSE_OK = {
    'GET':      [200],
    'PUT':      [200,201],
    'POST':     [201],
    'PATCH':    [200],
    'DELETE':   [200,204],
}

def recursionKeySearch(nestedDict, returnKey): # v2 - Used by both nbiQuery() and nbiMutation() and restconfCall()
    for key, value in nestedDict.iteritems():
        if key == returnKey:
            return True, value
    for key, value in nestedDict.iteritems():
        if isinstance(value, (dict, LinkedHashMap)): # XMC Python is Jython where a dict is in fact a java.util.LinkedHashMap
            foundKey, foundValue = recursionKeySearch(value, returnKey)
            if foundKey:
                return True, foundValue
    return [None, None] # If we find nothing

def recursionStatusSearch(nestedDict): # v4 - Used by nbiMutation(), seeks the status key and returned message
    for key, value in nestedDict.iteritems():
        if key == 'status':
            if 'message' in nestedDict and nestedDict['message']:
                return True, value, nestedDict['message']
            elif 'result' in nestedDict and nestedDict['result'] and 'msg' in nestedDict['result']: # For Policy mutations..
                return True, value, nestedDict['result']['msg']
            else:
                return True, value, None
    for key, value in nestedDict.iteritems():
        if isinstance(value, (dict, LinkedHashMap)): # XMC Python is Jython where a dict is in fact a java.util.LinkedHashMap
            foundKey, foundValue, foundMsg = recursionStatusSearch(value)
            if foundKey:
                return True, foundValue, foundMsg
    return [None, None, None] # If we find nothing

def replaceKwargs(queryString, kwargs): # v2 - Used by both nbiQuery() and nbiMutation() and restconfCall()
    for key in kwargs:
        if type(kwargs[key]) == bool:
            replaceValue = str(kwargs[key]).lower()
        elif type(kwargs[key]) == unicode:
            replaceValue = kwargs[key] # Keep as is
        else:
            replaceValue = str(kwargs[key]) # Make string
        queryString = queryString.replace('<'+key+'>', replaceValue)
    return queryString # Note, might return unicode
