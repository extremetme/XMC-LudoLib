#
# SNMP dictionary
# snmpDict.py
#

SNMP_TruthValue = { # Mapping input enable/disable
    'enable' : 1, # true
    'disable': 2, # false
}

SNMP_Request = { # outValue = snmpGet|snmpSet|snmpWalk(SNMP_Request['<name>'], [instance=<instance>], [value=<value>])
# SAMPLE Syntax:
#   'queryName|mibName': {
#       'oid': [<oidName>:]<singleOid> | [<listOf>], # For get & set; no leading dot; optional "oidName:" prepended
#       'asn': <ASN_?> | [<listOf>],                 # Only for set, mandatory
#       'set': <value> | [<listOf>],                 # Only for set, optional
#       'map': {'key1': <val1>, 'key2': <val2> }     # Mapping ASCII values to int values
#   },
    'ifName': { # Walk as is; Get supply instance
        'oid': 'ifName',
        'asn': ASN_OCTET_STR, #DisplayString
    },
    'ifAdminStatus': { # Walk as is; Get|Set supply instance
        'oid': 'ifAdminStatus',
        'asn': ASN_INTEGER, #INTEGER {up(1), down(2), testing(3)
    },
    'ifAlias': { # Walk as is; Get|Set supply instance
        'oid': 'ifAlias',
        'asn': ASN_OCTET_STR_PRINTABLE, #DisplayString (SIZE(0..64))
    },
    'ifName_ifAlias': { # Walk as is; Get supply instance
        'oid': ['ifName', 'ifAlias'],
    },
    'disableIqAgent': { # Get|Set only; supply no instance
        'oid': 'rcCloudIqAgentEnable: 1.3.6.1.4.1.2272.1.230.1.1.1.0',
        'asn': ASN_INTEGER, #TruthValue = INTEGER { true(1), false(2) }
        'set': 2,
    },
    'enableIqAgent': { # Get|Set only; supply no instance
        'oid': 'rcCloudIqAgentEnable: 1.3.6.1.4.1.2272.1.230.1.1.1.0',
        'asn': ASN_INTEGER, #TruthValue = INTEGER { true(1), false(2) }
        'set': 1,
    },
    'rcCloudIqAgentEnable': { # Get|Set only; supply no instance
        'oid': 'rcCloudIqAgentEnable: 1.3.6.1.4.1.2272.1.230.1.1.1.0',
        'asn': ASN_INTEGER, #TruthValue = INTEGER { true(1), false(2) }
    },
    'rcSshGlobalEnable': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalEnable: 1.3.6.1.4.1.2272.1.34.1.11.0',
        'asn': ASN_INTEGER, #INTEGER { false(0), true(1), secure(2) }
    },
    'rcSshGlobalClientEnable': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalClientEnable: 1.3.6.1.4.1.2272.1.34.1.24.0',
        'asn': ASN_INTEGER, #TruthValue = INTEGER { true(1), false(2) }
    },
    'rcSshGlobalSftpEnable': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalSftpEnable: 1.3.6.1.4.1.2272.1.34.1.19.0',
        'asn': ASN_INTEGER, #TruthValue = INTEGER { true(1), false(2) }
    },
    'rcSshGlobalPort': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalPort: 1.3.6.1.4.1.2272.1.34.1.2.0',
        'asn': ASN_INTEGER, #INTEGER (1..49151)
    },
    'rcSshGlobalMaxSession': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalMaxSession: 1.3.6.1.4.1.2272.1.34.1.3.0',
        'asn': ASN_INTEGER, #INTEGER (0..8)
    },
    'rcSshGlobalTimeout': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalTimeout: 1.3.6.1.4.1.2272.1.34.1.4.0',
        'asn': ASN_INTEGER, #INTEGER (1..120)
    },
    'rcSshGlobalRsaAuth': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalRsaAuth: 1.3.6.1.4.1.2272.1.34.1.7.0',
        'asn': ASN_INTEGER, #TruthValue = INTEGER { true(1), false(2) }
    },
    'rcSshGlobalDsaAuth': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalDsaAuth: 1.3.6.1.4.1.2272.1.34.1.8.0',
        'asn': ASN_INTEGER, #TruthValue = INTEGER { true(1), false(2) }
    },
    'rcSshGlobalPassAuth': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalPassAuth: 1.3.6.1.4.1.2272.1.34.1.9.0',
        'asn': ASN_INTEGER, #TruthValue = INTEGER { true(1), false(2) }
    },
    'rcSshGlobalKeyboardInteractiveAuth': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalKeyboardInteractiveAuth: 1.3.6.1.4.1.2272.1.34.1.20.0',
        'asn': ASN_INTEGER, #TruthValue = INTEGER { true(1), false(2) }
    },
    'rcSshGlobalX509AuthEnable': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalX509AuthEnable: 1.3.6.1.4.1.2272.1.34.1.25.0',
        'asn': ASN_INTEGER, #TruthValue = INTEGER { true(1), false(2) }
    },
    'rcSshGlobalX509AuthCertCAName': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalX509AuthCertCAName: 1.3.6.1.4.1.2272.1.34.1.31.0',
        'asn': ASN_OCTET_STR_PRINTABLE, #DisplayString (SIZE(0..45))
    },
    'rcSshGlobalX509AuthCertSubjectName': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalX509AuthCertSubjectName: 1.3.6.1.4.1.2272.1.34.1.30.0',
        'asn': ASN_OCTET_STR_PRINTABLE, #DisplayString (SIZE(0..45))
    },
    'rcSshGlobalX509AuthUsernameOverwrite': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalX509AuthUsernameOverwrite: 1.3.6.1.4.1.2272.1.34.1.27.0',
        'asn': ASN_INTEGER, #TruthValue = INTEGER { true(1), false(2) }
    },
    'rcSshGlobalX509AuthUsernameStripDomain': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalX509AuthUsernameStripDomain: 1.3.6.1.4.1.2272.1.34.1.28.0',
        'asn': ASN_INTEGER, #TruthValue = INTEGER { true(1), false(2) }
    },
    'rcSshGlobalX509AuthUsernameUseDomain': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalX509AuthUsernameUseDomain: 1.3.6.1.4.1.2272.1.34.1.29.0',
        'asn': ASN_OCTET_STR_PRINTABLE, #DisplayString (SIZE(0..255))
    },
    'rcSshGlobalX509AuthRevocationCheckMethod': { # Get|Set only; supply no instance
        'oid': 'rcSshGlobalX509AuthRevocationCheckMethod: 1.3.6.1.4.1.2272.1.34.1.26.0',
        'asn': ASN_INTEGER, #INTEGER { ocsp(1), none(2) }
        'map': { 'ocsp': 1, 'none': 2 }
    },
    'rcSshAuthType': { # Get|Set only; supply no instance
        'oid': 'rcSshAuthType: 1.3.6.1.4.1.2272.1.34.1.21.0',
        'asn': ASN_OCTET_STR_HEX, #BITS { hmacSha1(0), aeadAes128GcmSsh(1), aeadAes256GcmSsh(2), hmacSha2256(3) }
    },
    'rcSshEncryptionType': { # Get|Set only; supply no instance
        'oid': 'rcSshEncryptionType: 1.3.6.1.4.1.2272.1.34.1.22.0',
        'asn': ASN_OCTET_STR_HEX, #BITS { aes128Cbc(0), aes256Cbc(1), threeDesCbc(2), aeadAes128GcmSsh(3), aeadAes256GcmSsh(4), aes128Ctr(5),
                            #       rijndael128Cbc(6), aes256Ctr(7), aes192Ctr(8), aes192Cbc(9), rijndael192Cbc(10), blowfishCbc(11) }
    },
    'rcSshKeyExchangeMethod': { # Get|Set only; supply no instance
        'oid': 'rcSshKeyExchangeMethod: 1.3.6.1.4.1.2272.1.34.1.23.0',
        'asn': ASN_OCTET_STR_HEX, #BITS { diffieHellmanGroup14Sha1(0), diffieHellmanGroup1Sha1(1) -- obsolete, diffieHellmanGroupExchangeSha256(2) }
    },
}
