#
# XMC NBI dictionary
# apiXmcDict.py

NBI_Query = { # GraphQl query / outValue = nbiQuery(NBI_Query['getDeviceUserData'], IP=deviceIp)
# QUERIES (General):
    'nbiAccess': {
        'json': '''
                {
                  administration {
                    serverInfo {
                      version
                    }
                  }
                }
                ''',  
        'key': 'version'
    },
    'get_peer_nickname': {
        'json': '''
                {
                  network {
                    device(ip: "<IP>") {
                      deviceData {
                        userData1
                      }
                    }
                  }
                }
                ''',
        'key': ''
    },
    'getDeviceSiteVariables': {
        'json': '''
                {
                  network {
                    device(ip: "<IP>") {
                      sitePath
                      customVariables {
                        globalAttribute
                        name
                        scopeCategory
                        value
                        valueType
                      } 
                    }
                  }
                }
                ''',
        'key': 'device'   
    },
    'getSiteVariables': {
        'json': '''
                {
                  network {
                    siteByLocation(location: "<SITE>") {
                      customVariables {
                        globalAttribute
                        name
                        scopeCategory
                        value
                        valueType
                      } 
                    }
                  }
                }
                ''',
        'key': 'siteByLocation'
    },
    'getDeviceUserData': {
        'json': '''
                {
                  network {
                    device(ip: "<IP>") {
                      userData1
                      userData2
                      userData3
                      userData4
                    }
                  }
                }
                ''',
        'key': 'device'
    },
    'getSiteList': {
        'json': '''
                {
                  network {
                    sites {
                      location
                    }
                  }
                }
                ''',
        'key': 'sites'
    },
    'getSitePath': {
        'json': '''
                {
                  network {
                    device(ip: "<IP>") {
                      sitePath
                    }
                  }
                }
                ''',
        'key': 'sitePath'
    },
    'getSiteDvrDomain': {
        'json': '''
                {
                  network {
                    siteByLocation(location: "<SITE>") {
                      fabricDvrDomainId
                    } 
                  }
                }
                ''',
        'key': 'fabricDvrDomainId'
    },
    'getDeviceAdminProfile': {
        'json': '''
                {
                  network {
                    device(ip:"<IP>") {
                      deviceData {
                        profileName
                      }
                    }
                  }
                }
                ''',
        'key': 'profileName'
    },
    'getAdminProfileCreds': {
        'json': '''
                {
                  administration {
                    profileByName(name:"<PROFILE>") {
                      authCred {
                        userName
                        loginPassword
                      }
                    }
                  }
                }
                ''',
        'key': 'authCred'
    },
    'checkSwitchXmcDb': {
        'json': '''
                {
                  network {
                    device(ip:"<IP>") {
                      id
                    }
                  }
                }
                ''',
        'key': 'device'
    },
    'check_device': {
        'json': '''
                {
                  network {
                    device(ip: "<IP>") {
                      down
                    }
                  }
                }
                ''',
        'key': 'device'
    },
    'getProfileCredentials': {
        'json': '''
                {
                  administration {
                    profileByName(name: "<PROFILE>") {
                      authCred {
                        userName
                        loginPassword
                      }
                    }
                  }
                }
                ''',
        'key': 'authCred'
    },
    'getDeviceFirmware': {
        'json': '''
                {
                  network {
                    device(ip: "<IP>") {
                      firmware
                    }
                  }
                }
                ''',
        'key': 'firmware'
    },
    'getDevicesIpAndSerialData': {
        'json': '''
                {
                  network {
                    devices {
                      deviceData {
                        ipAddress
                        serialNumber
                      }
                    }
                  }
                }
                ''',
        'key': 'devices' # [{"deviceData": {"ipAddress": <IP>, "serialNumber": <SN>},...]
    },
    'getDevicesSerialNumbers': {
        'json': '''
                {
                  network {
                    devices {
                      deviceData {
                        serialNumber
                      }
                    }
                  }
                }
                ''',
        'key': 'devices' # [{"deviceData": {"serialNumber": <SN>},...]
    },
    'getDiscoveredDevicesSerialNumbers': {
        'json': '''
                {
                  network {
                    discoveredDevices {
                      serialNumber
                    }
                  }
                }
                ''',
        'key': 'discoveredDevices' # [{"serialNumber": <SN>},...]
    },
    'getDevicesGeneralData': {
        'json': '''
                {
                  network {
                    devices {
                      deviceName
                      nickName
                      ip
                      status
                      policyDomain
                      sitePath
                      sysContact
                      sysLocation
                      deviceData {
                        serialNumber
                        family
                      }
                    }
                  }
                }
                ''',
        'key': 'devices' # [{"deviceName": <>, "nickName": <>, etc., "deviceData": {"serialNumber": <SN>},...]
    },
    'getDeviceSerialNumber': {
        'json': '''
                {
                  network {
                    device(ip: "<IP>") {
                      deviceData {
                        serialNumber
                      }
                    }
                  }
                }
                ''',
        'key': 'serialNumber'
    },
    'getDeviceSerialAndMac': {
        'json': '''
                {
                  network {
                    device(ip: "<IP>") {
                      deviceData {
                        serialNumber
                        macAddress
                      }
                    }
                  }
                }
                ''',
        'key': 'deviceData'
    },
    'getDeviceData': {
        'json': '''
                {
                  network {
                    device(ip: "<IP>") {
                      firmware
                      sysName
                    }
                  }
                }
                ''',
        'key': 'device'
    },
    'checkSiteExists': {
        'json': '''
                {
                  network {
                    siteByLocation(location: "<SITE>") {
                      siteId
                    }
                  }
                }
                ''',
        'key': 'siteId'
    },
    'getAdminProfileCredentials': {
        'json': '''
                {
                  administration {
                    profileByName(name: "<PROFILENAME>") {      # null OR {                               
                      authCred {                                #           "authCred": {                 
                        loginPassword                           #             "loginPassword": "rwa",     
                        type                                    #             "type": "SSH",              
                        userName                                #             "userName": "rwa"           
                      }                                         #           },                            
                      readSecLevel                              #           "readSecLevel": "AuthNoPriv", 
                      readCredential {                          #           "readCredential": {           
                        authPassword                            #             "authPassword": "passwdvbn",
                        authType                                #             "authType": "SHA",          
                        communityName                           #             "communityName": "",        
                        privPassword                            #             "privPassword": "",         
                        privType                                #             "privType": "None",         
                        snmpType                                #             "snmpType": 3,              
                        userName                                #             "userName": "admin"         
                      }                                         #           },                            
                      writeSecLevel                             #           "writeSecLevel": "AuthNoPriv",
                      writeCredential {                         #           "writeCredential": {          
                        authPassword                            #             "authPassword": "passwdvbn",
                        authType                                #             "authType": "SHA",          
                        communityName                           #             "communityName": "",        
                        privPassword                            #             "privPassword": "",         
                        privType                                #             "privType": "None",         
                        snmpType                                #             "snmpType": 3,              
                        userName                                #             "userName": "admin"         
                      }                                         #           }                             
                    }                                           #         }                               
                  }
                }
                ''',
        'key': 'profileByName'
    },
    'getDeviceFamily': {
        'json': '''
                {
                  network {
                    device(ip: "<IP>") {
                      deviceData {
                        family
                      }
                    }
                  }
                }
                ''',
        'key': 'family'
    },
    'getDeviceId': {
        'json': '''
                {
                  network {
                    device(ip: "<IP>") {
                      deviceId
                    }
                  }
                }
                ''',
        'key': 'deviceId'
    },
    'getAdminProfileData': {
        'json': '''
                {
                  administration {
                    profileByName(name: "<PROFILENAME>") {
                      snmpType
                      readCredential {
                        credentialName
                      }
                      readSecLevel
                      writeCredential {
                        credentialName
                      }
                      writeSecLevel
                      maxCredential {
                        credentialName
                      }
                      maxSecLevel
                    }
                  }
                }
                ''',
        'key': 'profileByName'
    },
    'getSysLocation': {
        'json': '''
                {
                  network {
                    siteByLocation(location: "<SITE>"){
                      sysLocation
                    }
                  }
                }
                ''',
        'key': 'sysLocation'
    },
    'getSysContact': {
        'json': '''
                {
                  network {
                    siteByLocation(location: "<SITE>"){
                      sysContact
                    }
                  }
                }
                ''',
        'key': 'sysContact'
    },







# QUERIES (Workflows):
    'getWorkflowIds': {
        'json': '''
                {
                  workflows {
                    allWorkflows {
                      name
                      category
                      path
                      id
                    }
                  }
                }
                ''',
        'key': 'allWorkflows'
    },
    'getWorkflowList': {
        'json': '''
                {
                  workflows {
                    allWorkflows{
                      name
                      category
                      path
                    }
                  }
                }
                ''',
        'key': 'allWorkflows'
    },
    'listRunningWorkflows': {
        'json': '''
                {
                  workflows {
                    activeExecutions {     # [] OR [{
                      workflowName         #          "workflowName": "Onboard VSP"
                    }                      #       }]
                  }
                }
                ''',
        'key': 'activeExecutions'
    },
    'getWorkflowExecutionStatus': {
        'json': '''
                {
                  workflows {
                    execution(executionId: <EXECUTIONID>) {
                      status
                    }
                  }
                }
                ''',
        'key': 'status' # FAILED (failed or non existent), SUCCESS (finished), RUNNING (still running)
    },


# QUERIES (Access Control):
    'nacConfig': {
        'json': '''
                {
                  accessControl {
                    switch(ipAddress: "<IP>") {
                      primaryGateway
                      secondaryGateway
                      sharedSecret
                      radiusAccountingEnabled
                    }
                  }
                }
                ''',
        'key': 'switch'
    },
    'checkSwitchNacConfig': {
        'json': '''
                {
                  accessControl {
                    switch(ipAddress: "<IP>") {
                      ipAddress
                    }
                  }
                }
                ''',
        'key': 'switch'
    },
    'getNacRules': {
        'json': '''
                {
                  accessControl {
                    configuration(name: "<CONFIGNAME>") {
                      aaaConfiguration
                      name
                      portalConfiguration
                      customRules {
                        enabled
                        nacProfile
                        name
                      }
                    }
                  }
                }
                ''',
        'key': 'customRules'
    },
    'getNacGroup': {
        'json': '''
                {
                  accessControl {
                    groupInfoByName(name: "<PROFILENAME>") {
                      description
                      dynamic
                      name
                      type
                    }
                  }
                }
                ''',
        'key': 'groupInfoByName'
    },
    'getNacEngineGroups': {
        'json': '''
                {
                  accessControl {
                    allEngineGroups {
                      nacConfiguration
                      name
                    }
                  }
                }
                ''',
        'key': 'allEngineGroups'
    },
    'getNacEngineGroupsWithLoadBalancers': {
        'json': '''
                {
                  accessControl {
                    allEngineGroups {
                      name
                      loadBalancingEnabled
                      loadBalancerIps
                    }
                  }
                }
                ''',
        'key': 'allEngineGroups' # [{"name": <engine group>, "loadBalancerIps": [<list-of-IPs|empty list>], "loadBalancingEnabled": true|false},...]
    },
    'getNacGroupEngineIPs': {
        'json': '''
                {
                  accessControl {
                    enginesForGroup(name: "<NACGROUP>") {
                      ipAddress
                    }
                  }
                }
                ''',
        'key': 'enginesForGroup'
    },
    'getNacLocationGroups': {
        'json': '''
                {
                  accessControl {
                    groupNamesByType(typeString: "LOCATION")
                  }
                }
                ''',
        'key': 'groupNamesByType'
    },
    'getNacLocationGroupsMembers': {
        'json': '''
                {
                  accessControl {
                    group(name: "<LOCATIONGROUP>") {
                      values
                    }
                    
                  }
                }
                ''',
        'key': 'values'
    },
    'getNacEngineLoadBalancing': {
        'json': '''
                {
                  accessControl {
                    engineGroup(name: "<NACGROUP>") {
                      loadBalancingEnabled
                    }
                  }
                }
                ''',
        'key': 'loadBalancingEnabled'
    },
    'getNacEngineLoadBalancingIPs': {
        'json': '''
                {
                  accessControl {
                    engineGroup(name: "<NACGROUP>") {
                      loadBalancerIps
                    }
                  }
                }
                ''',
        'key': 'loadBalancerIps'
    },
    'getNacEngineLoadBalancing': {
        'json': '''
                {
                  accessControl {
                    engineGroup(name: "<NACGROUP>") {
                      loadBalancingEnabled
                      loadBalancerIps
                    }
                  }
                }
                ''',
        'key': 'engineGroup'
    },
    'getSwitchesForEngineGroup': {
        'json': '''
                {
                  accessControl {
                    switchesForEngineGroup(name: "<NACGROUP>") {
                      ipAddress
                      primaryGateway
                      secondaryGateway
                      tertiaryGateway
                      quaternaryGateway
                      attributesToSend
                      authTypeStr
                    }
                  }
                }
                ''',
        'key': 'switchesForEngineGroup' # [{"ipAddress": <switch ip>, "primaryGateway": <>, "secondaryGateway": <>, "tertiaryGateway": <>, "quaternaryGateway": <>},...]
    },
    'getNacPolicyMappings': {
        'json': '''
                {
                  accessControl{
                    allPolicyMappingEntries {
                      name
                      locationName
                      policyName
                      vlanId
                      vlanName
                    }
                  }
                }
                ''',
        'key': 'allPolicyMappingEntries'
    },



# QUERIES (Policy):
    'getPolicyDomains': {
        'json': '''
                {
                  policy {
                    domainNames
                  }
                }
                ''',
        'key': 'domainNames'
    },
    'getDevicePolicyDomain': {
        'json': '''
                {
                  policy{
                    domainNameByIp(ip:"<IP>")   # null or "name"
                  }
                }
                ''',
        'key': 'domainNameByIp'
    },
    'getPolicyVlanIslands': {
        'json': '''
                {
                  policy {
                    pviIslands(input: {
                      domainName: "<POLICYDOMAIN>"
                      fromDatabase: <DB>              # true (from DB), false (from cache)
                    }) {
                      data {                          # null OR [{
                        defaultIsland                 #             "defaultIsland": true|false,
                        name                          #             "name": "Default Island"
                      }                               #         }]
                    }
                  }
                }
                ''',
        'key': 'data'
    },
    'getPolicyVlanIslandDevices': {
        'json': '''
                {
                  policy{
                    pviIsland(input:{
                      domainName: "<POLICYDOMAIN>"
                      name: "<TOPOLOGY>"
                    }) {
                      data {
                        devices {       # [] OR [{
                          name          #          "name": "10.9.193.20"
                        }               #       }]
                      }
                      message
                      status
                      result{
                        msg
                      }
                    }
                  }
                }
                ''',
        'key': 'devices'
    },
    'getPolicyVlanIslandData': {
        'json': '''
                {
                  policy {
                    pviIslands(input: {
                      domainName: "<POLICYDOMAIN>"
                    }) {
                      data {
                        name
                        devices {
                          name
                        }
                      }
                      message
                      status
                      result {
                        msg
                      }
                    }
                  }
                }
                ''',
        'key': 'data' # [{"name": <islandName>, "devices": [{"name": <switch IP>>}, ...]}, ...]
    },
    'getPolicyVlanIslandData': {
        'json': '''
                {
                  policy {
                    pviIslands(input: {
                      domainName: "<POLICYDOMAIN>"
                      fromDatabase: true
                    }) {
                      data {
                        defaultIsland
                        name
                        nsiList {
                          name
                          nsi
                        }
                        vlans {
                          name
                          vid
                        }
                      }
                      message
                      status
                      result {
                        msg
                      }
                    }
                  }
                }
                ''',
        'key': 'data'
    },
    'getPolicyRoleServices': {
        'json': '''
                {
                  policy{
                    roles (input: {
                      domainName: "<POLICYDOMAIN>"
                      fromDatabase:true
                    }) {
                      data {
                        name
                        services {
                          name
                        }
                      }
                      message
                      status
                      result{
                        msg
                      }
                    }
                  }
                }
                ''',
        'key': 'data'
    },
    'getPolicyServiceRules': {
        'json': '''
                {
                  policy{
                    service(input: {
                      domainName: "<POLICYDOMAIN>"
                      name:"<SERVICENAME>"
                      fromDatabase:true
                    }) {
                      data {
                        rules {
                          enabled
                          typeStr
                          name
                          aclIndex
                          vlan {
                            name
                            vid
                          }
                          trafDesc {
                            extraData
                            trafDescTypeStr
                            trafDescValue
                            trafDescValueStr
                          }
                          httpRedirectIndex
                        }
                      }
                      message
                      status
                      result{
                        msg
                      }
                    }
                  }
                }
                ''',
        'key': 'rules'
    },
    'getPolicyVlanIslandDevices': {
        'json': '''
                {
                  policy {
                    pviIsland(input: {
                      domainName: "<POLICYDOMAIN>"
                      name:"<TOPOLOGY>"
                      fromDatabase: true
                    }) {
                      data {
                        devices {
                          device {
                            ip
                            deviceDisplayFamily
                          }
                        }
                      }
                      message
                      status
                      result {
                        msg
                      }
                    }
                  }
                }
                ''',
        'key': 'devices' # ["ip": <IP>, "deviceDisplayFamily": <Family>]
    },
    'checkPolicyEnforceComplete': {
        'json': '''
                {
                  policy {
                    enforceVerifyDomainResult(input: {
                      uniqueId: "<UNIQUEID>"
                    }) {
                      message
                      status
                      result {
                        devicesRemaining
                        toString
                      }
                    }
                  }
                }
                ''',
        'key': 'devicesRemaining' # 0 = complete; > 0 still running
    },



# MUTATIONS (General):
    # This is not a mutation in itself; its json which gets replaced into addSiteCustomActionTaskList below as <TASKLIST>
    'customActionTask': '''
        {
          enabled: true
          vendor: "<VENDOR>"
          family: "<FAMILY>"
          topology: "<TOPOLOGY>"
          task: "<TASKPATH>"
        }
    ''',
    'addSiteCustomActionTaskList': {
        'json': '''
                mutation{
                  network{
                    modifySite(input:{
                      siteLocation: "<SITEPATH>"
                      siteConfig:{
                        customActionsConfig:{
                          mutationType: ADD
                          customActionConfig: [
                            <TASKLIST>
                          ]
                        }
                      }
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'rediscover_device': {
        'json': '''
                mutation {
                  network {
                    rediscoverDevices(input: {devices: {ipAddress: "<IP>"}}) {
                      status
                      message
                    }
                  }
                }
                ''',
    },
    'delete_device': {
        'json': '''
                mutation {
                  network {
                    deleteDevices(input:{
                      removeData: true
                      devices: {
                        ipAddress:"<IP>"
                      }
                    }) {
                      status
                      message
                    }
                  }
                }
                ''',
    },
    'create_device': {
        'json': '''
                mutation {
                  network {
                    createDevices(input:{
                      devices: {
                        ipAddress:"<IP>"
                        siteLocation:"<SITE>"
                        profileName:"<PROFILE>"
                      }
                    }) {
                      status
                      message
                    }
                  }
                }
                ''',
    },
    'createSitePath': {
        'json': '''
                mutation {
                  network {
                    createSite(input: {
                      siteLocation: "<SITEPATH>"
                      siteConfig: {
                        customActionsConfig: {
                          mutationType: REMOVE_ALL
                        }
                        actionsConfig: {
                          addSyslogReceiver: true
                          addTrapReceiver: true
                          autoAddDevices: true
                          addToArchive: true
                        }
                      }
                    })
                    {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'setDeviceUserData': {
        'json': '''
                mutation {
                  network {
                    configureDevice(input: {
                      deviceConfig:{
                        ipAddress: "<IP>",
                        deviceAnnotationConfig: {
                          userData1: "<UD1>",
                          userData2: "<UD2>",
                          userData3: "<UD3>",
                          userData4: "<UD4>"
                        }
                      }
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'setDeviceTopoRole': {
        'json': '''
                mutation {
                  network {
                    configureDevice(input: {
                      deviceConfig:{
                        ipAddress: "<IP>"
                        generalConfig: {
                          topologyRole: <ROLE> # ANY,APPLIANCE,FIREWALL,GATEWAY,Hypervisor,L2_ACCESS,L2_LEAF,L3_ACCESS,L3_CORE,L3_DISTRIBUTION,L3_LEAF,L3_SPINE,LOAD_BALANCER,Server,WAN
                        }
                      }
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'setDeviceNickName': {
        'json': '''
                mutation {
                  network {
                    configureDevice(input: {
                      deviceConfig:{
                        ipAddress: "<IP>"
                        deviceAnnotationConfig: {
                          nickName: "<NICKNAME>"
                        }
                      }
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'setDeviceAssetTag': {
        'json': '''
                mutation {
                  network {
                    configureDevice(input: {
                      deviceConfig:{
                        ipAddress: "<IP>",
                        deviceAnnotationConfig: {
                          assetTag: "<TAG>"
                        }
                      }
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'setDeviceNotes': {
        'json': '''
                mutation {
                  network {
                    configureDevice(input: {
                      deviceConfig:{
                        ipAddress: "<IP>",
                        deviceAnnotationConfig: {
                          note: "<NOTE>"
                        }
                      }
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'setDeviceNickNameAndTopoRole': {
        'json': '''
                mutation {
                  network {
                    configureDevice(input: {
                      deviceConfig:{
                        ipAddress: "<IP>"
                        generalConfig: {
                          topologyRole: <ROLE> # ANY,APPLIANCE,FIREWALL,GATEWAY,Hypervisor,L2_ACCESS,L2_LEAF,L3_ACCESS,L3_CORE,L3_DISTRIBUTION,L3_LEAF,L3_SPINE,LOAD_BALANCER,Server,WAN
                        }
                        deviceAnnotationConfig: {
                          nickName: "<NICKNAME>"
                        }
                      }
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'enforceDeviceConfiguration': {
        'json': '''
                mutation {
                  network {
                    configureDevice(input: {
                      enforceAll:        false
                      enforceSystem:     false
                      enforceTopology:   false
                      enforceVlan:       true
                      enforceVrf:        false
                      enforceClip:       false
                      enforceServices:   false
                      enforceLag:        false
                      enforcePortAlias:  false
                      enforcePortVlan:   true
                      enforcePortFabric: false
                      timeout: 30
                      deviceConfig: {
                        ipAddress:"<IP>"
                      }
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'setDeviceWebHttps': {
        'json': '''
                mutation {
                  network {
                    configureDevice (input:{
                      deviceConfig:{
                        ipAddress: "<IP>"
                        generalConfig:{
                          deviceWebViewUrl: "https://%IP"
                        }
                      }
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'changeDeviceAdminProfile': {
        'json': '''
                mutation {
                  network {
                    configureDevice(input:{
                      deviceConfig: {
                        ipAddress: "<IP>"
                        generalConfig: {
                          adminProfile: "<PROFILE>"
                        }
                      }
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'deleteDiscoveredDevice': { # Always succeeds, even if IP does not exist under Discovered devices
        'json': '''
                mutation{
                  network{
                    deleteDiscoveredDevices(input:{
                      devices:[{
                        ipAddress: "<IP>"
                      }]
                      removeData:true
                    }
                    ) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'createTelnetCliProfile': {
        'json': '''
                mutation {
                  administration {
                    createCliProfiles(input: {
                      profiles: [
                        {
                          description: "<PROFILENAME>"
                          userName: "<USERNAME>"
                          protocolType: TELNET
                          loginPassword: "<PASSWORD>"
                        }
                      ]
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'createDeviceProfile': {
        'json': '''
                mutation {
                  administration {
                    createDeviceProfiles(input: {
                      profiles: [
                        {
                          profileName: "<PROFILENAME>"
                          snmpVersion:<SNMPVERSION>
                          readProfileName:"<SNMPPROFILE>"
                          writeProfileName:"<SNMPPROFILE>"
                          writeSecurity:<SECURITY>
                          maxSecurity:<SECURITY>
                          cliProfileName:"<CLIPROFILE>"
                        }
                      ]
                    } )
                     {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'preRegisterDevice': {
        'json': '''
                mutation {
                  network {
                    preRegisterDevices(input: {
                      devices: [{
                        serialNumber: "<SN>"
                        siteLocation: "<SITE>"
                        useDiscoveredIP: false
                        name: "<NAME>"
                        ipAddress:"<IP>/<CIDRMASK>"
                        gateway: "<GATEWAY>"
                      }]
                    }) {
                      status
                      message
                    }
                  }
                }
                ''',
    },
    'configurePreRegisteredDevice': {
        'json': '''
                mutation {
                  network {
                    configureDiscoveredDevice(input: {
                      deviceConfig: {
                        serialNumber: "<SN>"
                        generalConfig: {
                          defaultSitePath: "<SITE>"
                          sysName: "<NAME>"
                          sysLocation: "<LOCATION>"
                          sysContact: "<CONTACT>"
                          topologyRole: <TOPOLOGY>
                        }
                        deviceAnnotationConfig: {
                          nickName: "<NAME>"
                          assetTag: "<ASSETTAG>"
                        }
                        ztpPlusConfig: {
                          useDiscoveredMode: DISABLED
                          mgmtInterface: MANAGEMENT_ISID
                          subnetAddress: "<IP>/<CIDRMASK>"
                          gatewayAddress: "<GATEWAY>"
                          domainName: "<DOMAINNAME>"
                          dnsServer: "<DNSSERVER1>"
                          dnsServer2: "<DNSSERVER2>"
                          dnsServer3: "<DNSSERVER3>"
                          ntpServer: "<NTPSERVER1>"
                          ntpServer2: "<NTPSERVER2>"
                          firmwareUpgradeType: <FWUPDATE>
                          firmwareUpgradePersonaChange: <NOSFECONVERT>
                        }
                      }
                    }) {
                      status
                      message
                    }
                  }
                }
                ''',
    },
    # This is not a mutation in itself; its json which gets replaced into updateEndpointLocations below as <ENDPOINTLIST>
    'endpointData': '''
        {
          ipmask: "<IPCIDRNET>" 
          alias: "<ALIAS>"
          description:"<DESCRIPTION>"
        }
    ''',
    'updateEndpointLocations': {
        'json': '''
                mutation {
                  network {
                    modifySite(input: {
                      siteLocation:"<SITE>"
                      siteConfig: {
                        endpointLocationsConfig: {
                          endpointLocationConfig: {
                            mutationType: REPLACE
                            endpointLocations: [
                              <ENDPOINTLIST>
                            ]
                          }
                        }
                      }
                    }) {
                      status
                      message
                    }
                  }
                }
                ''',
    },


# MUTATIONS (Workflows):
    'executeWorkflow': {
        'json': '''
                mutation {
                  workflows {
                    startWorkflow(input: {
                      id: <ID>,
                      variables: <JSONINPUTS>
                    })
                    {
                      message
                      status
                      executionId
                      errorCode
                    }
                  }
                }
                ''',
        'key': 'executionId'
    },


# MUTATIONS (Access Control):
    'cloneNacProfile': {
        'json': '''
                mutation {
                  accessControl {
                    createDCMVirtualAndPhysicalNetwork(input: {
                      vlanName: "untagged"
                      primaryVlanId: 0
                      name: "<NAME>"
                      nacConfig: "<CONFIGNAME>"
                    }) {
                      status
                      message
                    }
                  }
                }
                ''',
    },
    'accessControlCreateSwitch': {
        'json': '''
                mutation {
                  accessControl {
                    createSwitch(input: {
                      nacApplianceGroup: "<NACGROUP>",
                      ipAddress: "<IP>",
                      switchType: L2_OUT_OF_BAND,
                      primaryGateway: "<ENGINE1>",
                      secondaryGateway: "<ENGINE2>",
                      tertiaryGateway: "<ENGINE3>",
                      quaternaryGateway: "<ENGINE4>",
                      authType: NONE,
                      attrsToSend: "<RADIUSTEMPLATE>",
                      radiusAccountingEnabled: true,
                      overrideSharedSecret: true,
                      sharedSecret: "<SHAREDSECRET>"
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'accessControlDeleteSwitch': {
        'json': '''
                mutation {
                  accessControl {
                    deleteSwitch(input: {
                      searchKey: "<IP>"
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'createNacProfile': {
        'json': '''
                mutation {
                  accessControl {
                    createDCMVirtualAndPhysicalNetwork(input: {
                      vlanName: "<NAME>"
                      primaryVlanId: <VID>
                      name: "<NAME>"
                      nacConfig: "<CONFIGNAME>"
                    }) {
                      status
                      message
                    }
                  }
                }
                ''',
    },
    'removeNacProfile': {
        'json': '''
                mutation {
                  accessControl {
                    removeDCMVirtualAndPhysicalNetwork(input: {
                      primaryVlanId: <VID>
                      name: "<NAME>"
                      nacConfig: "<CONFIGNAME>"
                      removeEndSystemGroup: true
                    }) {
                      status
                      message
                    }
                  }
                }
                ''',
    },
    'accessControlEnforceEngines': {
        'json': '''
                mutation {
                  accessControl {
                    enforceAccessControlEngines(input: {
                      engineGroup: "<NACGROUP>",
                      ignoreWarnings: true
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'accessControlEnforceAllEngines': {
        'json': '''
                mutation {
                  accessControl {
                    enforceAccessControlEngines(input: {
                      ignoreWarnings: true
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'accessControlCreateLocationGroup': {
        'json': '''
                mutation {
                  accessControl {
                    createGroup(input: {
                      name: "<LOCATIONGROUP>"
                      type: LOCATION
                    }) {
                      status
                      message
                    }
                  }
                }
                ''',
    },
    'accessControlAddSwitchToLocation': {
        'json': '''
                mutation {
                  accessControl {
                    addLocationEntryToGroup(input: {
                      description: "<DESCRIPTION>"
                      group: "<LOCATIONGROUP>"
                      switches: "<IP>"
                      interfaceType:ANY 
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'accessControlRemoveSwitchFromLocation': {
        'json': '''
                mutation {
                  accessControl {
                    removeEntryFromGroup(input: {
                      group: "<LOCATIONGROUP>"
                      value: "<IP>"
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },
    'updatePolicyMappingEntry': {
        'json': '''
                mutation {
                  accessControl{
                    updatePolicyMappingEntry(input:{
                      name:"<MAPPINGNAME>"
                      locationName:"*"
                      vlanId:<VID>
                      vlanName:"<VLANNAME>"
                    }) {
                      message
                      status
                    }
                  }
                }
                ''',
    },


# MUTATIONS (Policy):
    'openPolicyDomain': {
        'json': '''
                {
                  policy {
                    openDomain(input: {
                      name: "<POLICYDOMAIN>"
                    }) {
                      message
                      status
                      result{
                        msg
                      }
                    }
                  }
                }
                ''',
    },
    'lockOpenedPolicyDomain': {
        'json': '''
                mutation{
                  policy{
                    lockDomain(input:{
                      revoke: <FORCEFLAG>   # true|false
                    }) {
                      message
                      status
                      result{
                        msg
                      }
                    }
                  }
                }
                ''',
    },
    'unlockOpenedPolicyDomain': {
        'json': '''
                mutation{
                  policy{
                    unlockDomain(input:{}) {
                      message
                      status
                      result{
                        msg
                      }
                    }
                  }
                }
                ''',
    },
    'closePolicyDomain': {
        'json': '''
                {
                  policy {
                    closeDomain(input: {
                      name: "<POLICYDOMAIN>"
                    }) {
                      message
                      status
                      result{
                        msg
                      }
                    }
                  }
                }
                ''',
    },
    'savePolicyDomain': {
        'json': '''
                mutation{
                  policy{
                    saveDomain(input:{
                      name: "<POLICYDOMAIN>"
                      closeDomain: <CLOSEFLAG>   # true|false
                    }) {
                      message
                      status
                      result{
                        msg
                      }
                    }
                  }
                }
                ''',
    },
    'removeDeviceFromPolicyDomain': {
        'json': '''
                mutation{
                  policy{
                    mutateDeviceList(input:{
                      domainName: "<POLICYDOMAIN>"
                      mutationType: REMOVE
                      devices: ["<IP>"]
                    }) {
                      message
                      status
                      result{
                        msg
                      }
                    }
                  }
                }
                ''',
    },
    'addDeviceToPolicyDomain': {
        'json': '''
                mutation{
                  policy{
                    mutateDeviceList(input:{
                      domainName: "<POLICYDOMAIN>"
                      mutationType: ADD
                      devices: ["<IP>"]
                    }) {
                      message
                      status
                      result{
                        msg
                      }
                    }
                  }
                }
                ''',
    },
    'addDeviceToPolicyVlanIsland': {
        'json': '''
                mutation{
                  policy{
                    mutatePviIsland(input:{
                      domainName: "<POLICYDOMAIN>"
                      dataIdentifier: "<TOPOLOGY>"
                      mutationType: MODIFY
                      mutationData:{
                        addIps:["<IP>"]
                      }
                    }) {
                      message
                      status
                      result{
                        msg
                      }
                    }
                  }
                }
                ''',
    },
    'enforcePolicyDomain': {
        'json': '''
                mutation{
                  policy{
                    enforceDomain(input:{
                      name:"<POLICYDOMAIN>"
                      deviceIds: [<DEVICEIDLIST>]
                    }) {
                      message
                      status
                      result{
                        uniqueId
                        msg
                      }
                    }
                  }
                }
                ''',
        'key': 'uniqueId'
    },
}
