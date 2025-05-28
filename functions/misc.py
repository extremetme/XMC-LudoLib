#
# Other Custom Functions
# misc.py

def extractVistData(): # v1 - Tricky command to extract from, as it is different across VOSS, VSP8600 and XA
    # Only supported for family = 'VSP Series'
    data = sendCLI_showRegex(CLI_Dict[Family]['get_virtual_ist_data'])
    dataDict = {}
    dataDict['vlan']  = data[0][0] if data else None
    dataDict['state'] = data[0][1] if data else None
    dataDict['role']  = data[1][2] if data else None
    debug("extractVistData() = {}".format(dataDict))
    return dataDict

def compareIsisSysId(selfId, peerId): # v1 - Returns TRUE if selfId < peerId
    selfId = int(selfId.replace('.', ''), 16) # Convert from hex
    peerId = int(peerId.replace('.', ''), 16) # Convert from hex
    if selfId < peerId:
        return True
    return False

def compareMacIsisSysId(chassisMac, isisSysId): # v1 - Determines whether the ISIS System ID was user assigned or is derived from chassis MAC
    chassisMac = chassisMac.replace(':', '')[0:10] #94:9b:2c:b4:74:00 ==> 949b2cb474
    isisSysId  = isisSysId.replace('.', '')[0:10]  #949b.2cb4.7484    ==> 949b2cb474
    result = (chassisMac == isisSysId)
    debug("compareMacIsisSysId() = {}".format(result))
    return result

def determineIstRole(selfId, peerId): # v1 - Determines role of switch in SMLT Cluster
    if compareIsisSysId(selfId, peerId):
        role = 'Primary'
    else:
        role = 'Secondary'
    debug("determineIstRole() = {}".format(role))
    return role

def allocateSmltVirtBmac(role, selfId, peerId, takenBmacs): # v1 - Given the SysId of the primary vIST node, cycles last byte until it finds a BMAC not in the list provided 
    baseId = selfId if role == 'Primary' else peerId
    baseId = baseId.replace('.', '') #949b.2cb4.7484    ==> 949b2cb47484
    baseMac = ':'.join(re.findall(r'[\da-f]{2}', baseId[:-2])) # All but last hex byte ==> 94:9b:2c:b4:74
    initLastByte = int(baseId[-2:], 16) # decimal of hex 84
    lastByte = initLastByte
    direction = 1 # We try and increment it
    while 1: # Until we find a unique Bmac
        if lastByte == 255: # If we reach 0xff, we need to search decrementing
            direction = -1
            lastByte = initLastByte # We go the other way
        elif direction == -1 and lastByte == 0: # Bad sign..
            exitError('allocateSmltVirtBmac(): unable to allocate smlt-virt-bmac in range {}:xx'.format(baseMac))
        byteValue = lastByte + direction
        smltVirtBmac = "{}:{:02x}".format(baseMac, byteValue)
        if smltVirtBmac not in takenBmacs:
            break
        lastByte = byteValue
    debug("allocateSmltVirtBmac() = {}".format(smltVirtBmac))
    return smltVirtBmac

def allocateIstVlan(selfList, peerList): # v1 - Given a list of already used VLANs in 4k range, allocates the vIST VLAN
    step = 1 if IstVLANrange[0] < IstVLANrange[1] else -1
    istVlan = None
    for vlan in range(IstVLANrange[0], IstVLANrange[1], step):
        if str(vlan) not in selfList and str(vlan) not in peerList:
            istVlan = vlan
            break
    if not istVlan:
        exitError('allocateIstVlan(): unable to allocate available vIST VLAN in range {}-{}'.format(IstVLANrange[0], IstVLANrange[1]))
    debug("allocateIstVlan() = {}".format(istVlan))
    return istVlan

def allocateIstMltId(selfList, peerList): # v1 - Given a list of already used MLT ids, allocates the vIST MLT id
    step = 1 if IstMLTrange[0] < IstMLTrange[1] else -1
    istMltId = None
    for mltid in range(IstMLTrange[0], IstMLTrange[1], step):
        if str(mltid) not in selfList and str(mltid) not in peerList:
            istMltId = mltid
            break
    if not istMltId:
        exitError('allocateIstMltId(): unable to allocate available vIST MLT id in range {}-{}'.format(IstMLTrange[0], IstMLTrange[1]))
    debug("allocateIstMltId() = {}".format(istMltId))
    return istMltId

def allocateClusterId(role, selfNickname, peerNickname): # v1 - Allocates a DVR Leaf Cluster Id by taking the last 9 bits of the Primary node's nickname
    nickname = selfNickname if role == 'Primary' else peerNickname
    nicknumber = int(nickname.replace('.', ''), 16)
    clusterId = nicknumber & 0x1ff # Cluster-id 1-1000 = last 9bits of primary nickname
    debug("allocateClusterId() = {}".format(clusterId))
    return clusterId

def allocateIstIsid(role, selfNickname, peerNickname): # v1 - Allocates a vIST I-SID by taking the last 19 bits of the Primary node's nickname
    nickname = selfNickname if role == 'Primary' else peerNickname
    nicknumber = int(nickname.replace('.', ''), 16)
    vistIsid = VistIsidOffset + (nicknumber & 0x7ffff) # IST I-SID (15000000 + last 19bits of Primary Nickname)  
    debug("allocateIstIsid() = {}".format(vistIsid))
    return vistIsid

def allocateIstIP(role, selfNickname, peerNickname): # v3 - Allocates the vIST IP by taking 192.168.255.X/30 with last 6bits of Secondary's nickname
    nickname = peerNickname if role == 'Primary' else selfNickname
    nicknumber = int(nickname.replace('.', ''), 16)
    ipSubnet = ipToNumber(VistIPbase[0]) + ((nicknumber & 0x3f) << 2)
    ipNumber1 = ipSubnet + 1
    ipNumber2 = ipSubnet + 2
    istIp1 = numberToIp(ipNumber1)
    istIp2 = numberToIp(ipNumber2)
    istSubnet = (numberToIp(ipSubnet), VistIPbase[1]) # IP/Mask
    istIPself = istIp2 if role == 'Primary' else istIp1 # Here we ensure Master = Primary
    istIPpeer = istIp1 if role == 'Primary' else istIp2 # Here we ensure Master = Primary
    debug("allocateIstIP() subnet = {} / self = {} / peer = {}".format(istSubnet, istIPself, istIPpeer))
    return istSubnet, istIPself, istIPpeer

def allocateMltIds(offsetId, numberOfMlts, inUseList1, inUseList2=[]): # v1 - Given the list of in use MLTs from both vIST peers, provides a list of free MLT ids to use
    mltList = []
    mltid = offsetId
    while 1:
        if str(mltid) not in inUseList1 and str(mltid) not in inUseList2:
            mltList.append(str(mltid))
        if len(mltList) == numberOfMlts:
            break
        mltid += 1
    debug("allocateMltIds() = {}".format(mltList))
    return mltList

def allocateMltId(offsetId, inUseList1, inUseList2=[]): # v1 - Given the list of in use MLTs from both vIST peers, provides a list of free MLT ids to use
    allocatedMltid = None
    mltid = offsetId
    while 1:
        if str(mltid) not in inUseList1 and str(mltid) not in inUseList2:
            allocatedMltid = mltid
            break
        mltid += 1
    debug("allocateMltId() = {}".format(allocatedMltid))
    return allocatedMltid

def extractMltData(include=[]): # v2 - Extract MLT data: optionally include = ['fa', 'vlacp', 'lacp-extra']
    # Only supported for family = 'VSP Series'
    data = sendCLI_showRegex(CLI_Dict[Family]['get_mlt_data'])
    mltDict = {}
    mltPortDict = {}
    for tpl in data:
        if tpl[0]:
            mltDict[tpl[0]] = {'type': tpl[1], 'ports': tpl[2]}
        elif tpl[3]:
            mltDict[tpl[3]]['lacp'] = tpl[4]
        elif tpl[5]:
            mltDict[tpl[5]]['flex'] = tpl[6]
    for mltid in mltDict:
        for port in generatePortList(mltDict[mltid]['ports']):
            mltPortDict[port] = mltid

    if mltDict:
        if 'fa' in include:
            data = sendCLI_showRegex(CLI_Dict[Family]['list_fa_mlts'])
            for mltid in mltDict:
                mltDict[mltid]['fa'] = bool(mltid in data)
        if 'vlacp' in include:
            for mltid in mltDict:
                mltDict[mltid]['vlacp'] = False
            data = sendCLI_showRegex(CLI_Dict[Family]['list_vlacp_ports'].format(generatePortRange(mltPortDict.keys())))
            for port in data:
                if data[port] == 'true' and port in mltPortDict:
                    mltDict[mltPortDict[port]]['vlacp'] = True
        if 'lacp-extra' in include:
            for mltid in mltDict:
                mltDict[mltid]['key'] = None
            mltKey = sendCLI_showRegex(CLI_Dict[Family]['list_mlt_lacp_key'])
            portKey = sendCLI_showRegex(CLI_Dict[Family]['list_port_lacp_key'])
            for mltid in mltKey:
                mltDict[mltid]['key'] = mltKey[mltid]
                matchingKeyPortList = [x for x in portKey if portKey[x] == mltKey[mltid]]
                # This overwrites the ports, but at least we get in there all ports configured with matching LACP key (not just ports active in MLT LAG)
                mltDict[mltid]['ports'] = generatePortRange(matchingKeyPortList)

    debug("extractMltData() = {}".format(mltDict))
    return mltDict, mltPortDict

def findUnusedPorts(mltPortDict={}): # v1 - This functions returns a list of "default" ports, i.e. unconfigured ports
    # Only supported for family = 'VSP Series'
    # A port is considered here to be default if it is untagged and only member of VLAN 1 or no VLAN at all (this already excludes ISIS ports)
    # The up/down state of the port is intentionally not considered here (a default port can be already enabled)
    # Checks are also made to ensure that the returned port list does not contain any:
    # - Brouter ports
    # - MLT ports:  In some scripts MLT data needs extracting in greater depth than what needed here; in which case
    #               an already populated mltPortDict can be supplied; see function extractMltData()
    vlanDefaultPorts = sendCLI_showRegex(CLI_Dict[Family]['list_vlan_default_ports'], 'vlanDefaultPorts')
    brouterPorts = sendCLI_showRegex(CLI_Dict[Family]['list_brouter_ports'], 'brouterPorts')
    if not mltPortDict:
        mltPortDict = extractMltData(['lacp-extra'])[1] # We just fetch the basic MLT data + lacp enabled ports
    defaultPorts = [x for x in vlanDefaultPorts if x not in brouterPorts and x not in mltPortDict]
    debug("findUnusedPorts() = {}".format(defaultPorts))
    return defaultPorts

def extractFAelements(newPortList): # v1 - Extracts data from show fa elements
    # Dump FA element tables
    data = sendCLI_showRegex(CLI_Dict[Family]['list_fa_elements'])
    dataDict = {}
    for tpl in data:
        if Family in ['VSP Series', 'ERS Series']:
            if tpl[0]:
                elType = re.sub(r'NoAuth$', '', tpl[1]).lower()
                elAuth = None
                dataDict[tpl[0]] = {'type': elType, 'auth': None, 'macid': tpl[2], 'portid': tpl[3], 'lacp': False}
            elif tpl[5] and tpl[5] in dataDict:
                dataDict[tpl[5]]['auth'] = False if re.search(r'NoAuth$', tpl[6]) else True
        else: # Summit Series
            macid = re.sub(r'-', ':', tpl[0])
            portid = re.sub(r'-', ':', tpl[1])
            typeMatch = re.match(r'(Server|Proxy)( \(No Auth\))?', tpl[3])
            if typeMatch:
                elType = typeMatch.group(1).lower()
                elAuth = False if typeMatch.group(2) else True
            else:
                elType = 'client'
                elAuth = None
            dataDict[tpl[2]] = {'type': elType, 'auth': elAuth, 'macid': macid, 'portid': portid, 'lacp': False}

    if Family == 'VSP Series': # On VSP only, dump LLDP neighbour tables
        data = sendCLI_showRegex(CLI_Dict[Family]['list_lldp_neighbours'].format(generatePortRange(dataDict.keys())))
        for port in dataDict:
            if port in data:
                if re.match(r'Ethernet Routing Switch', data[port]):
                    dataDict[port]['neigh'] = 'ERS'
                elif re.match(r'ExtremeXOS', data[port]):
                    dataDict[port]['neigh'] = 'XOS'
                else:
                    dataDict[port]['neigh'] = None

    if newPortList: # These are default ports enabled with FA & LACP by this script (only VSP Series will execute this part)
        testPortList = [x for x in dataDict if x in newPortList] # Of ports above, these are the ones where an FA neighbour is seen
        debug("extractFAelements() testPortList = {}".format(testPortList))
        if testPortList:
            testPortRange = generatePortRange(testPortList, 'testPortRange')
            lacpDetectedPorts = sendCLI_showRegex(CLI_Dict[Family]['list_lacp_up_ports'].format(testPortRange))
            for port in testPortList:
                if port in lacpDetectedPorts:
                    dataDict[port]['lacp'] = True

    # {u'1/5': {'portid': u'00:01:00:18', 'type': u'proxy', 'auth': False, 'macid': u'02:04:96:af:0e:ea', 'lacp': True, 'neigh': ERS|XOS}}
    debug("extractFAelements() = {}".format(dataDict))
    return dataDict

def extractChassisMac(): # v1 - Extract chassis MAC and return a sanitized MAC (lowercase hex and ':' byte separator)
    family = emc_vars["family"]
    data = sendCLI_showRegex(CLI_Dict[family]['get_chassis_mac'])
    chassisMac = data.replace('-', ':').lower()
    debug("extractChassisMac() = {}".format(chassisMac))
    return chassisMac

def extractMltAndPortData(mltInclude=[], portInclude=[]): # v1 - Extract MLT data (include = ['fa','lacp','vlacp']) / and Port data (include = ['fa','lacp','vlacp'])
    # Only supported for family = 'VSP Series'
    mltDict = {}
    portDict = {}
    mltData = sendCLI_showRegex(CLI_Dict[Family]['get_mlt_data'])
    if 'fa' in mltInclude or 'fa' in portInclude:
        faData = sendCLI_showRegex(CLI_Dict[Family]['list_fa_interfaces'])
        for tpl in faData:
            enableFlag = True if tpl[1] == 'enabled' else False
            faMgmt = tpl[3]+':'+tpl[2] if tpl[3] != '0' and tpl[2] != '0' else None
            faAuth = True if tpl[4] == 'enabled' else False
            portDict[tpl[0]] = {'fa': enableFlag, 'faAuth': faAuth, 'faMgmt': faMgmt, 'key': None, 'lacp': False, 'mlt': None, 'vlacp': False}
            # Keys of portDict might include MLT-ids; these would be deleted below
    if 'lacp' in mltInclude or 'lacp' in portInclude:
        lacpPortData = sendCLI_showRegex(CLI_Dict[Family]['get_lacp_port_data'])
        for tpl in lacpPortData:
            enableFlag = True if tpl[2] == 'true' else False
            if tpl[0] not in portDict:
                if enableFlag:
                    portDict[tpl[0]] = {'fa': None, 'faAuth': None, 'faMgmt': None, 'key': tpl[1], 'lacp': enableFlag, 'mlt': None, 'vlacp': False}
                continue
            portDict[tpl[0]]['key'] = tpl[1]
            portDict[tpl[0]]['lacp'] = enableFlag
    if 'lacp' in mltInclude:
        lacpMltKey = sendCLI_showRegex(CLI_Dict[Family]['list_mlt_lacp_key'])
    for tpl in mltData:
        if tpl[0]:
            mltDict[tpl[0]] = {'type': tpl[1], 'ports': tpl[2]}
        elif tpl[3]:
            mltDict[tpl[3]]['lacp'] = True if tpl[4] == 'enable' else False
        elif tpl[5]:
            mltDict[tpl[5]]['flex'] = True if tpl[6] == 'enable' else False
    for mltid in mltDict:
        for port in generatePortList(mltDict[mltid]['ports']):
            if port not in portDict:
                portDict[port] = {'fa': None, 'faAuth': None, 'faMgmt': None, 'key': None, 'lacp': False, 'mlt': None, 'vlacp': False}
            portDict[port]['mlt'] = mltid
    for mltid in mltDict:
        if mltid in portDict:
            if 'fa' in mltInclude:
                mltDict[mltid]['fa'] = portDict[mltid]['fa']
                mltDict[mltid]['faAuth'] = portDict[mltid]['faAuth']
                mltDict[mltid]['faMgmt'] = portDict[mltid]['faMgmt']
            del portDict[mltid] # We no longer need it
        elif 'fa' in mltInclude:
            mltDict[mltid]['fa'] = None
            mltDict[mltid]['faAuth'] = None
            mltDict[mltid]['faMgmt'] = None
    if 'vlacp' in portInclude:
        vlacpData = sendCLI_showRegex(CLI_Dict[Family]['list_vlacp_ports'].format('')) # All ports
    elif 'vlacp' in mltInclude:
        vlacpData = sendCLI_showRegex(CLI_Dict[Family]['list_vlacp_ports'].format(generatePortRange(portDict.keys()))) # Only MLT ports
    if 'vlacp' in mltInclude:
        for mltid in mltDict:
            mltDict[mltid]['vlacp'] = False
        for port in vlacpData:
            if vlacpData[port] == 'true' and port in portDict and portDict[port]['mlt']:
                mltDict[portDict[port]['mlt']]['vlacp'] = True
    if 'vlacp' in portInclude:
        for port in vlacpData:
            if vlacpData[port] == 'true':
                if port not in portDict:
                    portDict[port] = {'fa': None, 'faAuth': None, 'faMgmt': None, 'key': None, 'lacp': False, 'mlt': None, 'vlacp': True}
                else:
                    portDict[port]['vlacp'] = True
    if 'lacp' in mltInclude:
        for mltid in mltDict:
            mltDict[mltid]['key'] = None
        for mltid in lacpMltKey:
            mltDict[mltid]['key'] = lacpMltKey[mltid]
            matchingKeyPortList = [x for x in portDict if portDict[x]['key'] == lacpMltKey[mltid]]
            # This overwrites the ports, but at least we get in there all ports configured with matching LACP key (not just ports active in MLT LAG)
            mltDict[mltid]['ports'] = generatePortRange(matchingKeyPortList)

    debug("extractMltAndPortData() mltDict = {}".format(mltDict))
    debug("extractMltAndPortData() portDict = {}".format(portDict))
    # mltDict: will include info of all MLTs
    # {"id" {'fa': None|True|False, 'faAuth': True|False, 'faMgmt': "vlan:isid", 'flex': True|False, 'key': None|"key", 'lacp': True|False, 'ports': "port-range", 'type': "smlt|norm", 'vlacp': True|False}}
    # portDict: will include info of all ports which are either FA enabled or LACP enabled or assigned to an MLT (statically or via LACP) [so not all ports]
    # {"port": {'fa': None|True|False, 'faAuth': True|False, 'faMgmt': "vlan:isid", 'key':None|"key", 'lacp': True|False, 'mlt': None|"id", 'vlacp': True|False}}
    return mltDict, portDict, faData

def xosExtractMltAndPortData(faAuthSupport=None): # v1 - Extract MLT data and Port data from XOS device
    # Only supported for family = 'Summit Series'
    mltDict = {}
    portDict = {}
    mltData = sendCLI_showRegex(CLI_Dict[Family]['get_mlt_data'])
    if faAuthSupport:
        faData = sendCLI_showRegex(CLI_Dict[Family]['list_fa_auth_ports'])
        for port in faData:
            faAuth = True if faData[port] == 'Enabled' else False
            portDict[port] = {'faAuth': faAuth, 'mlt': None}
    masterPort = None
    for tpl in mltData:
        if tpl[0]:
            masterPort = tpl[0]
            lacpEnabled = True if tpl[1] == 'LACP' else False
            mltDict[masterPort] = {'lacp': lacpEnabled, 'ports': [tpl[2]]}
        else:
            mltDict[masterPort]['ports'].append(tpl[2])
    for mltid in mltDict:
        for port in mltDict[mltid]['ports']:
            if port not in portDict:
                portDict[port] = {'faAuth': None, 'mlt': mltid}
            else:
                portDict[port]['mlt'] = mltid
        mltDict[mltid]['ports'] = generatePortRange(mltDict[mltid]['ports'])

    debug("xosExtractMltAndPortData() mltDict = {}".format(mltDict))
    debug("xosExtractMltAndPortData() portDict = {}".format(portDict))
    # mltDict: will include info of all MLTs
    # {"id" {'lacp': True|False, 'ports': "port-range"}}
    # portDict: will include info of all ports
    # {"port": {'faAuth': None|True|False, 'mlt': None|"id"}}
    return mltDict, portDict

def ersExtractMltAndPortData(include=[]): # v1 - Extract MLT data and Port data from ERS device (include = ['vlacp'])
    # Only supported for family = 'ERS Series'
    mltDict = {}
    portDict = {}
    mltData = sendCLI_showRegex(CLI_Dict[Family]['get_mlt_data'])
    for tpl in mltData:
        ports = None if tpl[1] == 'NONE' else tpl[1]
        mltEnabled = True if tpl[2] == 'Enabled' else False
        lacpKey = None if tpl[3] == 'NONE' else tpl[3]
        if not ports and not lacpKey:
            continue
        lacpEnabled = True if lacpKey else False
        mltDict[tpl[0]] = {'enable': mltEnabled, 'key': lacpKey, 'lacp': lacpEnabled, 'ports': ports, 'vlacp': False}
    for mltid in mltDict:
        if mltDict[mltid]['ports']: # If not None
            for port in generatePortList(mltDict[mltid]['ports']):
                portDict[port] = {'mlt': mltid}
    if 'vlacp' in include:
        vlacpData = sendCLI_showRegex(CLI_Dict[Family]['list_vlacp_ports'].format(generatePortRange(portDict.keys()))) # Only MLT ports
        for mltid in mltDict:
            mltDict[mltid]['vlacp'] = False
        for port in vlacpData:
            if vlacpData[port] == 'true' and port in portDict and portDict[port][mlt]:
                mltDict[portDict[port][mlt]]['vlacp'] = True

    debug("ersExtractMltAndPortData() mltDict = {}".format(mltDict))
    debug("ersExtractMltAndPortData() portDict = {}".format(portDict))
    # mltDict: will include info of all MLTs
    # {"id" {'enable': True|False, 'key': None|"key", 'lacp': True|False, 'ports': "port-range", 'vlacp': True|False}}
    # portDict: will include info of all ports which are assigned to an MLT [so not all ports]; we don't care about fa,faAuth as these are always enabeld on ERS
    # {"port": {'mlt': None|"id"}}
    return mltDict, portDict

def extractSpbmGlobal(): # v1 - Tricky command to extract from, as it is different across VOSS, VSP8600 and XA
    # Only supported for family = 'VSP Series'
    cmd = 'list://show isis spbm||(?:(B-VID) +PRIMARY +(NICK) +LSDB +(IP)(?: +(IPV6))?(?: +(MULTICAST))?|^\d+ +(?:(\d+)-(\d+) +\d+ +)?(?:([\da-f]\.[\da-f]{2}\.[\da-f]{2}) +)?(?:disable|enable) +(disable|enable)(?: +(disable|enable))?(?: +(disable|enable))?|^\d+ +(?:primary|secondary) +([\da-f:]+)(?: +([\da-f\.]+))?)'
    data = sendCLI_showRegex(cmd)
    # VOSS:[(u'B-VID', u'NICK', u'IP', u'IPV6', u'MULTICAST', u'', u'', u'', u'', u'', u'', u'', u''), (u'', u'', u'', u'', u'', u'4051', u'4052', u'0.00.75', u'enable', u'disable', u'disable', u'', u''),           (u'', u'', u'', u'', u'', u'', u'', u'', u'', u'', u'', u'00:00:00:00:00:00', u'')]
    # V86: [(u'B-VID', u'NICK', u'IP', u'', u'MULTICAST', u'', u'', u'', u'', u'', u'', u'', u''),     (u'', u'', u'', u'', u'', u'4051', u'4052', u'0.00.11', u'enable',             u'disable', u'', u'', u''),      (u'', u'', u'', u'', u'', u'', u'', u'', u'', u'', u'', u'82:bb:00:00:11:ff', u'82bb.0000.1200')]
    # XA:  [(u'B-VID', u'NICK', u'IP', u'', u'', u'', u'', u'', u'', u'', u'', u'', u''),              (u'', u'', u'', u'', u'', u'4051', u'4052', u'0.00.46', u'enable',                         u'', u'', u'', u'')]
    dataDict = {
        'SpbmInstance' : False,
        'BVIDs'        : [],
        'Nickname'     : None,
        'IP'           : None,
        'IPV6'         : None,
        'Multicast'    : None,
        'SmltVirtBmac' : None,
        'SmltPeerBmac' : None,
    }
    if len(data) > 1: # If we did not just match the banner line
        dataDict['SpbmInstance'] = True
        if data[1][5] and data[1][6]:
            dataDict['BVIDs'] = [data[1][5],data[1][6]]
        else:
            dataDict['BVIDs'] = []
        dataDict['Nickname'] = data[1][7]
        dataDict['IP'] = data[1][8]
        if data[0][3] == 'IPV6':
            dataDict['IPV6'] = data[1][9]
            if data[0][4] == 'MULTICAST':
                dataDict['Multicast'] = data[1][10]
        else:
            if data[0][4] == 'MULTICAST':
                dataDict['Multicast'] = data[1][9]
    if len(data) == 3: # We got SMLT data (on XA we don't have the line)
        if data[2][11] and data[2][11] != '00:00:00:00:00:00':
            dataDict['SmltVirtBmac'] = data[2][11]
            dataDict['SmltPeerBmac'] = data[2][12]
    debug("extractSpbmGlobal() = {}".format(dataDict))
    return dataDict

def extractExosVmData(): # v1 - Extract EXOS VM data
    # Only supported for family = 'Summit Series'
    data = sendCLI_showRegex(CLI_Dict[Family]['get_vm_data'])
    slotVmDict = {}
    if data:
        for tpl in data:
            if tpl[0]:
                slotVmDict['0'] = {'Memory': tpl[0]}
            elif tpl[1]:
               slotVmDict['0']['Cores'] = tpl[1]
            elif tpl[2]:
                slotVmDict[tpl[2]] = slotVmDict['0']
                del slotVmDict['0']
        debug("extractExosVmData() = {}".format(slotVmDict))
    # On Stack returns: {u'1': {'Memory': u'5728', 'Cores': u'1'}, u'2': {'Memory': u'4096', 'Cores': u'1'}}
    # On Standalone   : {'0': {'Memory': u'4096', 'Cores': u'1'}}
    # If no VMs       : {}
    return slotVmDict

def extractPortVlanData(portListStr): # v1 - Extract VLAN config on provided ports
    portVlanData = sendCLI_showRegex(CLI_Dict[Family]['list_port_vlans'].format(portListStr))
    portVlanDict = {}
    for tpl in portVlanData:
        portVlanDict[tpl[0]] = {
            'untagged': None,
            'tagged'  : tpl[2].split(','),
        }
        if tpl[3] == 'enable' and int(tpl[1]) > 0: 
            portVlanDict[tpl[0]]['untagged'] = tpl[1]
    debug("extractPortVlanData() = {}".format(portVlanDict))
    return portVlanDict

def extractFabricIds(): # v1 - Extracts all the BMACs (including SMLT Virt bmacs) and nicknames in fabric areas
    # Only supported for family = 'VSP Series'
    isisAreaDict = sendCLI_showRegex(CLI_Dict[Family]['get_isis_area'], 'isisAreaDict') # Get the ISIS areas
    fabricIdDict = {}
    for area in isisAreaDict:
        # Get the fabric IDs in current area
        fabricIdList = sendCLI_showRegex(CLI_Dict[Family]['get_in_use_fabric_ids'].format(isisAreaDict[area].lower()), 'fabricIdList')

        bmacHash = {}
        nicknameHash = {}
        for row in fabricIdList:
            bmacHash[numberToMacAddr(idToNumber(row[0]))] = 1
            nicknameHash[row[1]] = 1
            if row[2] != '00:00:00:00:00:00':
                bmacHash[row[2]] = 1
        fabricIdDict[area] = {'bmacs': list(bmacHash.keys()), 'nicknames': list(nicknameHash.keys())}

    debug("extractFabricIds() = {}".format(fabricIdDict))
    return fabricIdDict

def extractIsisInterfaces(): # v1 - Extract all the ISIS interfaces, in the 3 possible types: Port, MLT, Logical-intf
    # Only supported for family = 'VSP Series'
    isisIntfList = sendCLI_showRegex(CLI_Dict[Family]['get_isis_interfaces'], 'isisIntfList') # Get the ISIS areas
    isisIntfPortList = []
    isisIntfMltList = []
    isisLogicalIntfNameList = []
    isisLogicalIntfIdList = []
    for intf in isisIntfList:
        portMatch = re.match(r'^Port(\d+/\d+(?:/\d+)?)', intf)
        mltMatch  = re.match(r'^Mlt(\d+)', intf)
        if portMatch:
            isisIntfPortList.append(portMatch.group(1))
        elif mltMatch:
            isisIntfMltList.append(mltMatch.group(1))
        else:
            isisLogicalIntfNameList.append(intf)
    debug("extractIsisInterfaces() isisIntfPortList = {}".format(isisIntfPortList))
    debug("extractIsisInterfaces() isisIntfMltList = {}".format(isisIntfMltList))
    debug("extractIsisInterfaces() isisLogicalIntfNameList = {}".format(isisLogicalIntfNameList))

    if isisLogicalIntfNameList: # We have some Fabric Extend interfaces..
        feTunnelNameDict = sendCLI_showRegex(CLI_Dict[Family]['list_fe_tunnels_name'], 'feTunnelNameDict')
        for tunName in isisLogicalIntfNameList:
            isisLogicalIntfIdList.append(feTunnelNameDict[tunName])
        debug("extractIsisInterfaces() isisLogicalIntfIdList = {}".format(isisLogicalIntfIdList))

    isisIntfMltList.sort(key=int)
    isisLogicalIntfIdList.sort(key=int)
    isisIntfDict = {
        'port'    : generatePortRange(isisIntfPortList),
        'mlt'     : isisIntfMltList,
        'logical' : isisLogicalIntfIdList,
    }
    debug("extractIsisInterfaces() isisIntfDict = {}".format(isisIntfDict))
    return isisIntfDict

def getIsidUniStruct(isid): # v1 - Extract all port members of an I-SID
    # Only supported for family = 'VSP Series'
    # the "show i-sid" command is too fiddly to scrape...
    # the "show interfaces gigabitEthernet i-sid" command does not show I-SIDs with no ports assigned...
    # so we use "show run module i-sid" instead...
    cliOutput = sendCLI_showCommand(CLI_Dict[Family]['get_isid_uni_data'].format(isid))
    isidPorts = {}
    foundIsidData = False
    for line in cliOutput.splitlines():
        if foundIsidData:
            matchObj = re.match(r'c-vid (\d+) (port|mlt) (\S+)', line)
            if matchObj:
                tagging = 'tag'
                cvlan = matchObj.group(1)
                btype = matchObj.group(2)
                if btype == 'port':
                    ports = matchObj.group(3)
                    mlt = None
                else:
                    ports = None
                    mlt = matchObj.group(3)
            else:
                matchObj = re.match(r'untagged-traffic (port|mlt) (\S+)', line)
                if matchObj:
                    tagging = 'untag'
                    cvlan = None
                    btype = matchObj.group(1)
                    if btype == 'port':
                        ports = matchObj.group(2)
                        mlt = None
                    else:
                        ports = None
                        mlt = matchObj.group(2)
                else:
                    matchObj = re.match(r'(port|mlt) (\S+)', line)
                    if matchObj:
                        tagging = 'transparent'
                        cvlan = None
                        btype = matchObj.group(1)
                        if btype == 'port':
                            ports = matchObj.group(2)
                            mlt = None
                        else:
                            ports = None
                            mlt = matchObj.group(2)
                    elif re.match(r'exit', line):
                        break # We come out!
                    else:
                        continue
            if ports:
                portList = generatePortList(ports)
                debug("portList = {}".format(portList))
                for port in portList:
                    isidPorts[port] = {'type': tagging, 'vlan': cvlan}
            if mlt:
                isidPorts[mlt] = {'type': tagging, 'vlan': cvlan}

        elif re.match(r'^i-sid {} '.format(isid), line):
            isidPorts['exists'] = True
            foundIsidData = True
            continue
        else: # Other line, skip
            continue

    debug("getIsidUniStruct OUT = {}".format(isidPorts))
    return isidPorts


def idToNumber(idString): # v1 - Convert the sys-id or nickname or mac to a number
    return int(re.sub(r'[\.:]', '', idString), base=16)

def numberToHexStr(number, nibbleSize=''): # v1 - Convert a number to hex string
    template = "{:0" + str(nibbleSize) + "x}"
    return template.format(number)

def numberToBinStr(number, bitSize=''): # v1 - Convert a number to binary string
    template = "{:0" + str(bitSize) + "b}"
    return template.format(number)

def numberToNickname(idNumber): # v1 - Convert number to nickname string
    hexStr = numberToHexStr(idNumber, 5)
    return hexStr[0] + '.' + '.'.join(hexStr[i:i+2] for i in range(1, len(hexStr), 2))

def numberToSystemId(idNumber): # v1 - Convert number to System ID
    hexStr = numberToHexStr(idNumber, 12)
    return '.'.join(hexStr[i:i+4] for i in range(0, len(hexStr), 4))

def numberToMacAddr(idNumber):  # v1 - Convert number to MAC address
    hexStr = numberToHexStr(idNumber, 12)
    return ':'.join(hexStr[i:i+2] for i in range(0, len(hexStr), 2))

def nicknameXorMask(nickname, mask): # v1 - Perform XOR of nickname with mask
    return numberToNickname(idToNumber(nickname) ^ idToNumber(mask))

def systemIdXorMask(sysId, mask): # v1 - Perform XOR of system-id with mask
    return numberToSystemId(idToNumber(sysId) ^ idToNumber(mask))

def macXorMask(mac, mask): # v1 - Perform XOR of MAC address with mask
    return numberToMacAddr(idToNumber(mac) ^ idToNumber(mask))

def idReplMask(inId, mask, value, nibbles=12): # v1 - Replaces masked bits with value provided; nibbles = 12 (MAC/SysId) / 5 (nickname)
    bits = nibbles * 4
    inIdNumber = idToNumber(inId)
    maskNumber = idToNumber(mask)
    notMaskNumber = maskNumber ^ ((1 << bits) - 1)
    valueNumber = idToNumber(value)
    maskBinStr = numberToBinStr(maskNumber, bits)
    valueBinStr = numberToBinStr(valueNumber)
    debug("inId     = {} / {}".format(numberToHexStr(inIdNumber, nibbles), numberToBinStr(inIdNumber, bits)))
    debug("mask     = {} / {}".format(numberToHexStr(maskNumber, nibbles), maskBinStr))
    debug("!mask    = {} / {}".format(numberToHexStr(notMaskNumber, nibbles), numberToBinStr(notMaskNumber, bits)))
    debug("value    = {} / {}".format(numberToHexStr(valueNumber), valueBinStr))

    valueMaskStr = ''
    for b in reversed(maskBinStr):
        if b == '1' and len(valueBinStr):
            valueMaskStr = valueBinStr[-1] + valueMaskStr
            valueBinStr = valueBinStr[:-1] # chop last bit off
        else:
            valueMaskStr = '0' + valueMaskStr
    if len(valueBinStr):
        print "idReplMask() remaining value bits {} not inserted !!".format(len(valueBinStr))
    valueMaskNumber = int(valueMaskStr, base=2)
    debug("vmask    = {} / {}".format(numberToHexStr(valueMaskNumber, nibbles), valueMaskStr))
    maskedIdNumber = inIdNumber & notMaskNumber
    debug("maskedId = {} / {}".format(numberToHexStr(maskedIdNumber, nibbles), numberToBinStr(maskedIdNumber, bits)))
    finalIdNumber = maskedIdNumber | valueMaskNumber
    debug("finalId  = {} / {}".format(numberToHexStr(finalIdNumber, nibbles), numberToBinStr(finalIdNumber, bits)))
    return finalIdNumber

def nicknameReplMask(nickname, mask, value): # v1 - Replaces nickname masked bits with value provided
    return numberToNickname(idReplMask(nickname, mask, value, 5))

def systemIdReplMask(sysId, mask, value): # v1 - Replaces system-id masked bits with value provided
    return numberToSystemId(idReplMask(sysId, mask, value))

def macReplMask(mac, mask, value): # v1 - Replaces MAC address masked bits with value provided
    return numberToMacAddr(idReplMask(mac, mask, value))

def parseCliCommands(chainStr): # v4 - Parses the CLI commands string and filters out empty lines and comment lines
    cmdList = map(str.rstrip, str(chainStr.encode('ascii', 'ignore')).splitlines()) # Force to ASCII without warnings, in case user pasted text with unicode
    cmdList = filter(None, cmdList) # Filter out empty lines, if any
    if "RegexEmbeddedIfElse" in globals(): # Valid pragma lines include velocity statements 
        pragmaRegex = re.compile('^#(error|sleep|if|elseif|else|end|eval|last)') # "#block" missing as we don't use it where we use this function 
    else: # Valid pragma lines do not include velocity statements
        pragmaRegex = re.compile('^#(error|sleep)')
    cmdList = [x for x in cmdList if x[0] != "#" or pragmaRegex.match(x)] # Strip commented lines out, except accepted pragma lines
    return "\n".join(cmdList)

import json
def parsePatterns(chainStr): # v4 - Parses the input grep patternsm and filters out empty lines and comment lines
    patList = map(str.rstrip, str(chainStr.encode('ascii', 'ignore')).splitlines()) # Force to ASCII without warnings, in case user pasted text with unicode
    patList = filter(None, patList) # Filter out empty lines, if any
    patList = [x for x in patList if len(x) and x[0] != "#"] # Strip empty lines and commented lines out
    patDictList = []
    for pat in patList:
        patMatch = re.match(r'^(?:(VOSS|EXOS|ISW1|ISW2|ERS) *& *)?(.+?)(:[=!]) *(.+?)(?:\((.+)\))?$', pat)
        if patMatch:
            patDictList.append({
                "family"     : patMatch.group(1),
                "description": patMatch.group(2).strip(),
                "match"      : patMatch.group(3),
                "pattern"    : patMatch.group(4).strip(),
                "remediate"  : patMatch.group(5)
            })
    debug("\nConfig patterns data =\n{}\n".format(json.dumps(patDictList, sort_keys=True, indent=4)))
    return patDictList

def ifFileReadFile(inputStr): # v1 - If a file path, read and return that file, else return inputStr
    lineList = map(str.rstrip, str(inputStr.encode('ascii', 'ignore')).splitlines()) # Force to ASCII without warnings, in case user pasted text with unicode
    lineList = [x for x in lineList if len(x) and x[0] != "#"] # Strip empty lines and commented lines out
    if len(lineList) == 1 and re.match(r'/.*', lineList[0]):
        try:
            with open(lineList[0], 'r') as file:
                return file.read()
        except:
            exitError("Unable to open file {} for data".format(lineList[0]))
    else:
        return inputStr

def parseCyphers(chainStr): # v2 - Parses the SSH Cyphers input and filters out empty lines and comment lines
    cypherList = map(str.strip, str(chainStr).splitlines())
    cypherList = filter(None, cypherList) # Filter out empty lines, if any
    cypherList = [x.split()[0] for x in cypherList if x[0] != "#"] # Strip commented lines out and keep only 1st word of each line
    return cypherList

def parseRadiusAttribute(templates, family): # v1 - Returns family template if templates in format VOSS|EXOS|ISW:<template-name>
    for line in templates.splitlines():
        templateMatch = re.match(r'^ *(VOSS|EXOS|ISW) *: *(.+?) *$', line)
        if templateMatch and templateMatch.group(1) == family:
            return templateMatch.group(2)
    return None

def takePolicyDomainLock(policyDomain, waitTime=10, retries=4, forceAfterRetries=2): # v2 - Take lock on opened policy domain
    # If we fail to get a lock initially, this could be due to a user holding a lock on the same policy domain
    # Or, it could be another instance of this same workflow running for another switch, doing the same thing
    # (but latter is no longer applicable if acquireLock() is used, so we don't cater for it anymore)
    # We try and take the lock up to number of retries input, waiting waitTime between every retry
    # Initially we try without forcing, but after forceAfterRetries we try by forcing
    forceFlag = False
    retriesCount = 0
    while not nbiMutation(NBI_Query['lockOpenedPolicyDomain'], FORCEFLAG=forceFlag): # Try take lock
        if LastNbiError == "Conflict":
            retriesCount += 1
            if retriesCount >= retries:
                exitLockError("Failed to place lock on Policy Domain '{}' after {} retries\n{}".format(policyDomain, retries, LastNbiError))
            print "Unable to acquire lock on Policy Domain '{}'; re-trying in {} secs".format(policyDomain, waitTime)
            time.sleep(waitTime)
            if retriesCount >= forceAfterRetries:
                print "Forcing lock on next try"
                forceFlag = True
        else: # Unexpected error
            exitLockError("Failed to place lock on Policy Domain '{}'\n{}".format(policyDomain, LastNbiError))
    print "Placed lock on Policy Domain '{}'".format(policyDomain)

def enforcePolicyDomain(policyDomain, deviceIds=None, waitTime=5, retries=2, checkTime=10): # v1 - Enforce Policy domain and wait for completion
    # deviceIds, if provided, must be either a single device ID, or a comma separated string of device id numbers
    # If deviceIds is provided the policy enforcement will be done only on those switches, not the whole domain
    # An initial waitTime is done, then repeated in between retries up to the number of retries provided
    # Once police enforce API call returns success, this only means that XIQ-SE has started the Policy Enforce
    # But a policy enforce could take several minutes, particularly if done on whole domain (no deviceIds) and EXOS switches present in domain
    # So the function then checks progress of the enforce, and only returns once it has completed (regardless of success or not)
    # To check if the policy enforce is completed, an API call is made every checkTime seconds
    if not deviceIds:
        deviceIds = ''
    pendingEnforce = True
    retryCount = 0
    while pendingEnforce and retryCount <= retries:
        # Take a nap before enforcing the Policy domain, otherwise the enforce can fail if done too quickly after a save..
        print "Waiting {} seconds before enforcing Policy Domain '{}'".format(waitTime, policyDomain)
        time.sleep(waitTime)
        retryCount += 1
        # Enforce the Policy Domain
        uniqueId = nbiMutation(NBI_Query['enforcePolicyDomain'], POLICYDOMAIN=policyDomain, DEVICEIDLIST=deviceIds) # Enforce the Policy Domain
        if uniqueId:
            print "Successfully enforced Policy Domain '{}'".format(policyDomain)
            pendingEnforce = False
        else:
            print "Failed to enforce Policy Domain '{}'\n{}\n".format(policyDomain, LastNbiError)
            if retryCount <= retries:
                print "- retry {}".format(retryCount)
    if pendingEnforce: # We failed to enforce after several retries...
        exitLockError("Failed to enforce Policy Domain '{}' after {} retries\nError message: {}".format(policyDomain, retries, LastNbiError))

    # Now wait until the policy enforce completes, before releasing the lock
    devicesRemaining = 1 # Init to non-zero
    while devicesRemaining > 0:
        print "Waiting {} seconds before checking if Policy Domain enforce completed".format(checkTime)
        time.sleep(checkTime)
        devicesRemaining = nbiQuery(NBI_Query['checkPolicyEnforceComplete'], UNIQUEID=uniqueId)
    print "Policy Domain '{}' enforce completed".format(policyDomain)

def sortNacIpList(ipList): # v1 - Given a list of IPs, returns same list with 1st IP the one set as "Primary" under UserData
    sortedIpList = []
    poolIpList = []
    for ip in ipList:
        userData = nbiQuery(NBI_Query['getDeviceUserData'], IP=ip)
        # Sample of what we should get back
        # "device": {
        #   "userData1": "Primary" | null,
        #   "userData2": null,
        #   "userData3": null,
        #   "userData4": null
        # }
        # Or we get null
        if userData and [x for x in userData if userData[x] and userData[x].lower() == 'primary']:
            sortedIpList.insert(0, ip) # Add to front of list
            poolIpRecord = [x for x in userData if userData[x] and re.match(r'pool *= *', userData[x].lower())]
            if poolIpRecord:
                poolIpList = map(str.strip, poolIpRecord[0].split("=")[-1].split(","))
        else:
            sortedIpList.append(ip)    # Append
    return sortedIpList, poolIpList

def sortNacClientList(nacIpList, poolIpList): # v1 - Parses the nacIpList and makes sure that IPs in poolIpList are listed first
    sortedIpList = []
    if poolIpList:
        for ip in poolIpList: # Parse the pool list and make sure these IPs get added first, if they exist
            if ip in nacIpList:
                sortedIpList.append(ip)
        for ip in nacIpList: # Then parse the NAC IP list and makes sure any other IPs also get added after
            if ip not in sortedIpList:
                sortedIpList.append(ip)
    else: # We don't care
        sortedIpList = nacIpList
    return sortedIpList

import csv
def writeCsvEmailAttachment(path, warnings, snNameIp): # v2 - Write warnings dict to CSV file
    csvFilePath = path + "/warnings.csv"
    with open(csvFilePath, 'w') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=["S/N", "Sysname", "IP", "Warning", "Remediation"], extrasaction='ignore')
        csv_writer.writeheader()
        for sn in warnings:
            for warning in warnings[sn]:
            	warning, fixedFlag = re.subn(' - FIXED!$', '', warning)
                if fixedFlag:
                    csv_writer.writerow({"S/N": sn, "Sysname": snNameIp[sn]["name"], "IP": snNameIp[sn]["ip"], "Warning": warning, "Remediation": "Successful"})
                else:
                    csv_writer.writerow({"S/N": sn, "Sysname": snNameIp[sn]["name"], "IP": snNameIp[sn]["ip"], "Warning": warning, "Remediation": ""})
    return csvFilePath
