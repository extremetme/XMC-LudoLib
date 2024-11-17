#
# RESTCONF functions - (requires apiBase.py)
# apiRestconf.py v1
#
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
        'username' : 'rwa',
        'password' : 'rwa',
    },
    'Summit Series': {
        'tcpPort'  : None,
        'protocol' : 'http',
        'restPath' : '/rest/restconf/data',
        'username' : 'admin',
        'password' : '',
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
