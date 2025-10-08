#
# RESTCONF functions for VOSS/EXOS - (requires apiBase.py)
# apiRestconf.py v2
#
# Example (see apiRestconfDict.py for RESTCONF[] definitions):
#restconfStart(protocol='http')
#vlanDict = restconfCall(RESTCONF["listVlans"])
#restconfCall(RESTCONF["createVlan"], NAME="test", VID="666")
#vlanCfgDict = restconfCall(RESTCONF["getVlanConfig"], VID="666")
#restconfCall(RESTCONF["deleteVlan"], VID="666")
#if LastRestconfError:
#    printLog("LastRestconfError = {}".format(LastRestconfError))

import requests, json, re
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
RestconfAuthToken = None
RestconfAuthType = None
RestconfUrl = None
LastRestconfError = None
RestConfFamilyDefaults = {
    'VSP Series'    : {
        'tcpPort'   : 8080,
        'protocol'  : 'http',
        'authType'  : 'basic',
        'loginUri'  : '/auth/token',
        'loginBody' : '{"username": "%s", "password" : "%s" }',
        'restPath'  : '/rest/restconf/data',
        'username'  : 'rwa',
        'password'  : 'rwa',
        'headers'   : None
    },
    'Summit Series' : {
        'tcpPort'   : None,
        'protocol'  : 'http',
        'authType'  : 'basic',
        'loginUri'  : '/auth/token',
        'loginBody' : '{"username": "%s", "password" : "%s" }',
        'restPath'  : '/rest/restconf/data',
        'username'  : 'admin',
        'password'  : '',
        'headers'   : None
    },
    'XIQ Controller': {
        'tcpPort'   : 5825,
        'protocol'  : 'https',
        'authType'  : 'oath2',
        'loginUri'  : '/management/v1/oauth2/token',
        'loginBody' : '{"grantType": "password", "userId": "%s", "password" : "%s" }',
        'restPath'  : '/management',
        'username'  : 'admin',
        'password'  : '',
        'headers'   : None
    },
}


def restconfSession(authToken=None, body=False, authType=None): # v2 - On XMC we don't seem to be able to re-use a session... so we spin a new one every time...
    session = requests.Session()
    session.verify  = False
    session.timeout = 2
    session.headers.update({'Accept':           'application/json',
                            'Connection':       'keep-alive',
                            'Cache-Control':    'no-cache',
                            'Pragma':           'no-cache',
                            'Accept-encoding':  'None',  # XIQ-SE's Jython requests won't work properly otherwise
                           })
    if authToken:
        if authType and authType == "oath2":
            session.headers.update({ 'Authorization':'Bearer '+ authToken })
        else:
            session.headers.update({ 'X-Auth-Token': authToken })
    if body:
        session.headers.update({ 'Content-Type': 'application/json' })
    if Family and "headers" in RestConfFamilyDefaults:
        session.headers.update(RestConfFamilyDefaults[Family]["headers"])
    debug("RESTCONF session headers:\n{}".format(session.headers))
    return session


def restconfStart(host=None, tcpPort=None, protocol=None, username=None, password=None, restPath=None, authType=None, loginUri=None, loginBody=None): # v2 - Set up RESTCONF session
    global RestconfAuthToken
    global RestconfAuthType
    global RestconfUrl

    if not host:
        if not emc_vars['deviceIP']:
            exitError("restconfStart() no host provided and emc_vars['deviceIP'] is not set either")
        host = emc_vars['deviceIP']

    if Family:
        if not tcpPort:
            tcpPort = RestConfFamilyDefaults[Family]['tcpPort']
        if not protocol:
            protocol = RestConfFamilyDefaults[Family]['protocol']
        if not restPath:
            restPath = RestConfFamilyDefaults[Family]['restPath']
        if not authType:
            authType = RestConfFamilyDefaults[Family]['authType']
        if not loginUri:
            loginUri = RestConfFamilyDefaults[Family]['loginUri']
        if not loginBody:
            loginBody = RestConfFamilyDefaults[Family]['loginBody']

    if not username:
        try:
            profileName = nbiQuery(NBI_Query['getDeviceAdminProfile'], debugKey='profileName', IP=host)
            authCred = nbiQuery(NBI_Query['getAdminProfileCreds'], debugKey='authCred', PROFILE=profileName)
            username = authCred['userName']
            password = authCred['loginPassword']
        except:
            if Family and Family in RestConfFamilyDefaults:
                username = RestConfFamilyDefaults[Family]['username']
                password = RestConfFamilyDefaults[Family]['password']
            else:
                exitError("restconfStart() need to be able to execute nbiQuery() to derive device credentials")

    # Create the HTTP session
    if not restPath:
        restPath = '/rest/restconf/data' # Default path, normally provided from /.well-known/host-meta
    if not loginUri:
        loginUri = '/auth/token' # Default login path for basic auth
    if not loginBody:
        loginBody = '{"username": "%s", "password" : "%s" }' # Default login path for basic auth
    if tcpPort and tcpPort != 80:
        loginUrl = "{}://{}:{}{}".format(protocol, host, tcpPort, loginUri)
    else:
        loginUrl = "{}://{}{}".format(protocol, host, loginUri)
    if password:
        body     = loginBody % (username, password)
    else: # EXOS with default admin account only...
        body     = loginBody % (username, "")
    session = restconfSession(body=True)
    try:
        response = session.post(loginUrl, body)
        response.connection.close()
        printLog("RESTCONF call: POST {}".format(loginUrl))
        debug("{}".format(body))
        response.raise_for_status()
    except requests.exceptions.RequestException as error:
        abortError(u"RESTCONF {}: ".format(loginUrl), str(error))

    # Extract the token and store it in global variable
    debug(u"RESTCONF response data = {}".format(response.text)) # This data is typically unicode
    if authType == "oath2":
        RestconfAuthToken = json.loads(response.text, encoding='utf-8')['access_token']
    else:
        RestconfAuthToken = json.loads(response.text, encoding='utf-8')['token']
    debug("restconfSetSession(): extracted token {}".format(RestconfAuthToken))
    RestconfAuthType = authType
    debug("restconfSetSession(): setting auth type '{}'".format(RestconfAuthType))
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
        printLog("SANITY - RESTCONF call: {} {}{}\n{}".format(httpCall, RestconfUrl, restUri ,json.dumps(jsonBody, indent=4, sort_keys=True)))
        LastRestconfError = None
        return []

    # Display info about the RESTCONF call we are about to perform
    if jsonBody:
        printLog("\nRESTCONF call: {} {}{}\n{}".format(httpCall, RestconfUrl, restUri ,json.dumps(jsonBody, indent=4, sort_keys=True)))
    else:
        printLog("\nRESTCONF call: {} {}{}".format(httpCall, RestconfUrl, restUri))

    # Make the RESTCONF call
    session = restconfSession(authType=RestconfAuthType, authToken=RestconfAuthToken, body=jsonBody)
    sessionHttpMethod = getattr(session, httpCall.lower())
    response = sessionHttpMethod(RestconfUrl + restUri, json=jsonBody)
    response.connection.close()

    debug("RESTCONF response = {}".format(response))
    debug("RESTCONF response reason = {}".format(response.reason))
    debug(u"RESTCONF response data = {}".format(response.text)) # This data is typically unicode

    if response.status_code in HTTP_RESONSE_OK[httpCall.upper()]:
        LastRestconfError = None
        responseDict = json.loads(response.text, encoding='utf-8') if response.text else True
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
            abortError(u"RESTCONF {} for {}".format(restconfDict['http'], restUri), 'Key "{}" was not found in response data'.format(returnKey))

        # Else, return the full response
        if Debug:
            if debugKey: debug("RESTCONF return {} = {}".format(debugKey, responseDict))
            else: debug("RESTCONF return data = {}".format(responseDict))
        return responseDict
    elif returnKeyError:
        LastRestconfError = response.reason + ":" + response.text
        return None
    else:
        abortError(u"RESTCONF {} for {}".format(restconfDict['http'], restUri), response.reason + ":" + response.text) # This data is typically unicode
