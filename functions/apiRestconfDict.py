#
# RESTCONF dictionary
# apiRestconfDict.py
#

RESTCONF = { # RESTCONF call / outValue = restconfCall(RESTCONF["createVlan"], NAME="test", VID="666")

# VOSS & EXOS

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


# XIQ-C  -  https://documentation.extremenetworks.com/ExtremeCloud_IQ_Controller_10.14.01_API/index_gateway_api.html

    'getSites': {
        'http' : 'GET',
        'uri'  : 'v3/sites',
    },
    'getRoles': {
        'http' : 'GET',
        'uri'  : 'v3/roles',
    },
    'getVlanTopologies': {
        'http' : 'GET',
        'uri'  : 'v1/topologies',
    },
    'deleteVlanTopology': {
        'http' : 'DELETE',
        'uri'  : 'v1/topologies/<TOPOLOGYID>',
    },
    'createVlanTopology': {
        'http' : 'POST',
        'uri'  : 'v1/topologies',
        'body' : '''
                {
                  "name": "<NAME>",
                  "mode": "FabricAttach",
                  "vlanid": <VID>,
                  "isid": <ISID>,
                  "profiles": <UUIDLIST>
                }
                ''',
    },
    'updateRoleProfiles': {
        'http' : 'PUT',
        'uri'  : 'v3/roles/<ROLEID>',
        'body' : '''
                {
                  "name": "<NAME>",
                  "profiles": <UUIDLIST>
                }
                ''',
    },

    # This is not a mutation in itself; it's json which gets replaced into l3Filter below
    "l3FilterMapping": { # Mapping keys for l3Filter
        "direction": [
            { # 0=Default
                "intoNetwork": "destAddr",      # <INTONETWORK>
                "outFromNetwork": "none",       # <OUTFROMNETWORK>
            },
            { # 1=If src set
                "intoNetwork": "none",          # <INTONETWORK>
                "outFromNetwork": "sourceAddr", # <OUTFROMNETWORK>
            },
        ],
        "subnetType": [ # <SUBNETTYPE>
            "anyIpAddress", # 0=Default
            "userDefined",  # 1=For IP address input
            "hostName",     # 2=For FQDN
        ],
        "protocol": [ # <PROTOCOL>
            "any", # 0=Default
        ],
        "port": [ # <PORTENUM>
            "any",         # 0
            "userDefined", # 1
        ],
        "action": [ # <ACTION>
            "FILTERACTION_ALLOW",    # 0=Permit
            "FILTERACTION_DENY",     # 1=Deny
            "FILTERACTION_REDIRECT", # 2=Redirect
        ],
    },
    # This is not a mutation in itself; it's json which gets replaced into updateEndpointLocations below as <ENDPOINTLIST>
    'l3Filter': '''
        {
            "name": "<NAME>",
            "intoNetwork": "<INTONETWORK>",
            "outFromNetwork": "<OUTFROMNETWORK>",
            "subnetType": "<SUBNETTYPE>",
            "ipAddressRange": "<IPADDRESSRANGE>",
            "protocol": "<PROTOCOL>",
            "port": "<PORTENUM>",
            "portLow": <PORT>, 
            "action": "<ACTION>"
        },
    ''',
    'updateRoleL3Rules': {
        'http' : 'PUT',
        'uri'  : 'v3/roles/<ROLEID>',
        'body' : '''
                {
                  "name": "<NAME>",
                  "l3Filters": [<L3FILTERSLIST>]
                }
                ''',
    },

}

