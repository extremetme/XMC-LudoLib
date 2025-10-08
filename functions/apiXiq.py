#
# XIQ-API functions - (requires apiBase.py)
# apiXiq.py v2
#
# Example (see apiXiqDict.py for XIQAPI[] definitions):
#xiqapiLogin(username='<email>', password='<password>')
#response = xiqapiCall(XIQAPI["listDevices"])
#if LastXiqApiError:
#    printLog("LastXiqApiError = {}".format(LastXiqApiError))
#printLog("response =\n{}".format(json.dumps(response, indent=4, sort_keys=True)))
#
import requests, json
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
XiqApiAuthToken = None
XiqApiUrl = 'https://api.extremecloudiq.com/'
LastXiqApiError = None

def xiqapiSession(authToken=None): # v1 - On XMC we don't seem to be able to re-use a session... so we spin a new one every time...
    session = requests.Session()
    session.verify  = False
    session.timeout = 10
    session.headers.update({'Accept':           'application/json',
                            'Connection':       'keep-alive',
                            'Content-Type':     'application/json',
                           })
    if authToken:
        session.headers.update({ 'Authorization':'Bearer '+ authToken })
    return session


def xiqapiLogin(username=None, password=None): # v2 - Login to XIQ API and obtain the access token
    global XiqApiAuthToken
    loginUrl = XiqApiUrl + 'login'
    jsonBody = {
                'username':username,
                'password':password,
    }
    session = xiqapiSession()
    try:
        response = session.post(loginUrl, json=jsonBody)
        if response.status_code == requests.codes.ok:
            try:
                result    = response.json()
                XiqApiAuthToken = result[u'access_token']
                printLog("XIQ API login successful for user {}".format(username))
                return True
            except:
                abortError("XIQ API response {}".format(response.text), "JSON decoding failed")
        elif response.status_code == requests.codes.unauthorized:
            abortError("XIQ API login response HTTP-{}".format(response.status_code), "XIQ API Authentication failed")
        else:
            abortError("XIQ API login response HTTP-{}".format(response.status_code), "XIQ API Other error")
    except requests.Timeout as error:
        abortError("XIQ API login", "Timeout")
    return False


def xiqapiCall(xiqapiDict, returnKeyError=False, debugKey=None, **kwargs): # v2 - Makes an XIQ-API call
    if not XiqApiAuthToken:
        exitError("xiqapiCall() cannot be called without first obtaining an access token via xiqapiLogin()")
    global LastXiqApiError
    httpCall = xiqapiDict['http']
    xiqUri = replaceKwargs(xiqapiDict['uri'], kwargs)
    queryStr = xiqapiDict['query'] if 'query' in xiqapiDict else None
    jsonStr  = replaceKwargs(xiqapiDict['body'], kwargs) if 'body' in xiqapiDict else None
    if queryStr:
        xiqUri += '?' + queryStr
    jsonBody = json.loads(jsonStr) if jsonStr else None
    returnKey = xiqapiDict['key'] if 'key' in xiqapiDict else None
    if Sanity and httpCall.lower() != 'get':
        printLog("SANITY - XIQAPI call: {}\n{}".format(xiqUri ,json.dumps(jsonBody, indent=4, sort_keys=True)))
        LastXiqApiError = None
        return []

    # Display info about the XIQAPI call we are about to perform
    if jsonBody:
        printLog("\XIQAPI call: {} {}{}\n{}".format(httpCall, XiqApiUrl, xiqUri ,json.dumps(jsonBody, indent=4, sort_keys=True)))
    else:
        printLog("\XIQAPI call: {} {}{}".format(httpCall, XiqApiUrl, xiqUri))

    # Implement loop to fetch all pages of data, if XIQ returns data in pages
    returnData = [] # Init as a list, in case we fall into multiple pages of output data
    pageQuery = ''
    done = False
    while not done:

        # Make the XIQAPI call
        session = xiqapiSession(XiqApiAuthToken)
        sessionHttpMethod = getattr(session, httpCall.lower())
        response = sessionHttpMethod(XiqApiUrl + xiqUri + pageQuery, json=jsonBody)

        debug("XIQAPI response = {}".format(response))
        debug("XIQAPI response reason = {}".format(response.reason))
        debug("XIQAPI response data = {}".format(response.text))

        if response.status_code != HTTP_RESONSE_OK[httpCall.upper()]: # Error case
            LastXiqApiError = response.reason + ":" + response.text
            return None

        # Load response json into dict
        responseDict = json.loads(response.text) if response.text else True
        if all(keys in responseDict for keys in ('page','total_pages', 'data')) and 'page' not in xiqUri:
            returnData += responseDict['data'] # Append
            if responseDict['page'] == responseDict['total_pages']:
                done = True
            else: # Fetch next page
                pageQuery = "&page={}".format(responseDict['page'] + 1)
        else:
            returnData = responseDict
            done = True

    # If we get here, we got data without any error
    LastXiqApiError = None

    if returnKey: # If a specific key requested, we find it
        foundKey, returnValue = recursionKeySearch(returnData, returnKey)
        if foundKey:
            if Debug:
                if debugKey: debug("XIQAPI returnKey {} = {}".format(debugKey, returnValue))
                else: debug("XIQAPI returnKey {} = {}".format(returnKey, returnValue))
            return returnValue
        if returnKeyError:
            return None
        # If requested key not found, raise error
        abortError("XIQAPI {} for {}".format(xiqapiDict['http'], xiqUri), 'Key "{}" was not found in response data'.format(returnKey))

    # Else, return the full response
    if Debug:
        if debugKey: debug("XIQAPI return {} = {}".format(debugKey, returnData))
        else: debug("XIQAPI return data = {}".format(returnData))
    return returnData
