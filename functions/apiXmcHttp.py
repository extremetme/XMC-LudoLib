#
# XMC GraphQl NBI functions via HTTP requests - (requires apiBase.py)
# apiXmcHttp.py v2
#
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
