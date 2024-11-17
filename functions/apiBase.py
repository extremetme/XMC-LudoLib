#
# XMC GraphQl & RESTCONF & XIQ API required functions
# apiBase.py v5
#
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

def recursionStatusSearch(nestedDict): # v3 - Used by nbiMutation()
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
