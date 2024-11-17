#
# RESTCONF dictionary
# apiRestconfDict.py
#

RESTCONF = { # RESTCONF call / outValue = restconfCall(RESTCONF["createVlan"], NAME="test", VID="666")
    'listVlans': {
        'http' : 'GET',
        'uri'  : 'openconfig-vlan:vlans',
        'query': 'depth=3',
        'key'  : 'vlan',
    },
    'getVlanConfig': {
        'http' : 'GET',
        'uri'  : 'openconfig-vlan:vlans/vlan=<VID>/config',
        'key'  : 'openconfig-vlan:config',
    },
    'createVlan': {
        'http' : 'POST',
        'uri'  : 'openconfig-vlan:vlans',
        'body' : '''
                {
                    "openconfig-vlan:vlans": [
                        {
                            "config": {
                                "name": "<NAME>", 
                                "vlan-id": <VID>
                            }
                        }
                    ]
                }
                ''',
    },
    'deleteVlan': {
        'http' : 'DELETE',
        'uri'  : 'openconfig-vlan:vlans/vlan=<VID>',
    },
}
