#
# XIQ API dictionary
# apiXiqDict.py

XIQAPI = { # XIQAPI call / outValue = xiqapiCall(XIQAPI["createVlan"], NAME="test", VID="666")
    'listDevices': {
        'http' : 'GET',
        'uri'  : 'devices',
        'query': 'limit=100',
    },
    'onboardDevicesVoss': {
        'http' : 'POST',
        'uri'  : 'devices/:onboard',
        'body' : '''
                 {
                   "voss": {
                     "sns": [
                       "<SERIALNUMBLIST>"
                     ]
                   },
                 }
                ''',
    },
#    'sample': {
#        'http' : 'GET|POST|etc..',
#        'uri'  : 'path without preceding /',
#        'key'  : 'key to extract',
#    },
}
