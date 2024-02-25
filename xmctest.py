import sys
import json
import java.util
import emc_cli      # Own local replica
import emc_nbi      # Own local replica
import emc_results  # Own local replica
print "Offline syntax: py -2 XMC-Python-Ludo-Standard-Library_xxx.py [emc_vars.json|-] [deviceIP] [VSP Series|Summit Series]"
if len(sys.argv) > 1: # Json file as 1st argv
    emc_vars = json.load(open('emc_vars.json')) if sys.argv[1] == '-' else json.load(open(sys.argv[1]))
    if len(sys.argv) > 2: # override deviceIP as 2nd argv
        emc_vars["deviceIP"] = sys.argv[2]
    if len(sys.argv) > 3:
        emc_vars["family"] = sys.argv[3]
else:
    emc_vars = json.load(open('emc_vars.json'))
print "Offline pointing to deviceIP = {}".format(emc_vars["deviceIP"])
print "Offline Family Type = {}".format(emc_vars["family"])

# Main functions; always execute
execfile("XMC-Python-Ludo-Standard-Library.py")

# Thread functions; if needed
#execfile("XMC-Python-Ludo-Threads-Library.py")



Debug = True
Sanity = False

#Family = 'ERS Series'
Family = 'VSP Series'
#Family = 'ISW-Series'
#Family = 'ISW-Series-Marvell'

#vossSegMgmt = LooseVersion(emc_vars["deviceSoftwareVer"]) >= LooseVersion("8.2")
#debug("vossSegMgmt = {}".format(vossSegMgmt))


siteVarDict = {u'Site-Voice-isid': u'12990120', u'Sys-Name': u'ADMe-2615', u'Nick-Name': u'0.26.15', u'System-ID': u'020e.0026.0150', u'Ports': u'1/1', u'Mgmt Vlan IP': u'10.200.5.107', u'Site-Data-isid': u'12990666', u'Site-Voice-vlan': u'120', u'Site-Data-vlan': u'666', u'SourceIP': u'10.26.0.115', '__PATH__': u'/World/Development'}
autoSenseVoiceIsid = siteVarLookup('${Site-Voice-isid}', siteVarDict)
print "autoSenseVoiceIsid = {}".format(autoSenseVoiceIsid)
sys.exit(0)


#sendCLI_configCommand('snmp-server user snmpRO group read sha aes https:// CustomerSecretString// CustomerSecretString//CustomerSecretString // CustomerSecretString')
#sys.exit(0)


#vossSaveConfigRetry(waitTime=10, retries=3, aggressive=True)
#vossWaitNoUsersConnected(waitTime=10, retries=3, aggressive=True)
#cliSessions = sendCLI_showRegex(CLI_Dict[Family]['list_cli_sessions'], 'cliSessions')
#sys.exit(0)


#mgmtVlanIPMaskTuple = sendCLI_showRegex(CLI_Dict[Family]['get_mgmt_ip_vlan_and_mask'].format("20.0.202.11"), 'mgmtVlanIPMaskTuple')
#if mgmtVlanIPMaskTuple:
#    mgmtVlan,ipMaskLen = mgmtVlanIPMaskTuple
#    debug("mgmtVlan = {}".format(mgmtVlan))
#    debug("ipMaskLen = {}".format(ipMaskLen))


#maskGwList = sendCLI_showRegex(CLI_Dict[Family]['get_mgmt_ip_mask_and_gw'].format("202", "20.0.202.24"), 'maskGwList')
#if maskGwList:
#    ipMask,defaultGateway = maskGwList
#    debug("ipMask = {}".format(ipMask))
#    debug("defaultGateway = {}".format(defaultGateway))
#sys.exit(0)


#sendCLI_configChain(CLI_Dict[Family]['set_mgmt_ip'].format("202", "20.0.202.11", "255.255.255.0"))


#readCsvToDict("mgmtdata.csv", "19JP0300W34E")


#generatePortList(generatePortRange(["2/5", "2/6/1", "2/6/2", "2/6/3", "2/7"]))
#generatePortList(generatePortRange(["1", "2", "3", "4", "2/1", "2/2", "2/3", "2/6/1", "2/6/2", "2/6/3", "2/7"]))
#generatePortList("1-4")
#sys.exit(0)


#if ipAddr == '192.168.56.50':
#    restconfStart(host=ipAddr, tcpPort=8080, protocol='http', username="rwa", password="rwa") # VOSS
#elif ipAddr == '192.168.56.44':
#    restconfStart(host=ipAddr, protocol='http', username="admin")			  # EXOS
#sys.exit(0)


#restconfStart(protocol='http')
#restconfCall(RESTCONF["listVlans"])
#restconfCall(RESTCONF["createVlan"], NAME="test", VID="666")
#restconfCall(RESTCONF["getVlanConfig"], VID="666")
#restconfCall(RESTCONF["deleteVlan"], VID="666")
#restconfCall(RESTCONF["getVlanConfig"], VID="666")
#if LastRestconfError:
#    print "LastRestconfError = {}".format(LastRestconfError)



#isisAreaDict = sendCLI_showRegex(CLI_Dict[Family]['get_isis_area'], 'isisAreaDict')


#data = sendCLI_showRegex('show vm detail | include Memory|CPUs|Slot||(?:Memory size: +(\d+) MB|CPUs: +(\d)|Slot: +(\d))', 'data')
#slotVmDict = extractExosVmData()


#executionId = workflowExecute("Provisioning/Onboard VSP", deviceIP="20.0.48.13")
#print sendCLI_configChain("show users; show bonkers; show vlan basic", returnCliError=True, abortOnError=False)


#extractPortVlanData("1/19-1/23")
#portVlanDict = sendCLI_showRegex(CLI_Dict[Family]['list_port_vlans'].format("1/19-1/23"))


#figwCLI_showCommand(CLI_Dict['FIGW']['show_version'])

#vers = figwCLI_showRegex(CLI_Dict['FIGW']['get_version'], 'vers')

#checkFigwRunning = figwCLI_showRegex(CLI_Dict['FIGW']['check_vm_running'], 'checkFigwRunning')

#sendCLI_showCommand(CLI_Dict[Family]['figw_cli'].format(CLI_Dict['FIGW']['show_version_bad']))


#vossSaveConfigRetry(retries=0)

#vossWaitNoUsersConnected(retries=3)


#warpBuffer_execute('no router isis enable; router isis enable')
#warpBuffer_execute('create vlan 666; create vlan 667')
#warpBuffer_execute(CLI_Dict[Family]['enable_isis'], waitForPrompt=False)
#emc_cli.send('') # Empty send, to re-sync output buffer


#cmd = 'list://show isis spbm||(?:(B-VID) +PRIMARY +(NICK) +LSDB +(IP)(?: +(IPV6))?(?: +(MULTICAST))?|^\d+ +(?:(\d+)-(\d+) +\d+ +)?(?:([\da-f]\.[\da-f]{2}\.[\da-f]{2}) +)?(?:disable|enable) +(disable|enable)(?: +(disable|enable))?(?: +(disable|enable))?|^\d+ +(?:primary|secondary) +([\da-f:]+)(?: +([\da-f\.]+))?)'
#data = sendCLI_showRegex(cmd)
#check = sendCLI_showRegex(CLI_Dict[Family]['check_users_connected'])


#spbmGlobalDict = extractSpbmGlobal() # {'Nickname': u'0.00.75', 'SmltVirtBmac': u'82:bb:00:00:21:ff', 'SmltPeerBmac': u'82bb.0000.2200'}


# Get NAC rules
#nacConfigDomain = 'DataCenterConnect Configuration'
#nacRulesList = nbiQuery(NBI_Query['getNacRules'].replace('<CONFIGNAME>', nacConfigDomain), 'nacRulesList')
    # Sample of what we get back
    # "customRules": [
    #   {
    #     "enabled": true,
    #     "nacProfile": "GRT-100",
    #     "name": "GRT-100"
    #   },
    #   {
    #     "enabled": true,
    #     "nacProfile": "GRT-101",
    #     "name": "GRT-101"
    #   },
    # ]


#ersExtractMltAndPortData()
#xosExtractMltAndPortData()
#extractChassisMac()
#extractFAelements([])
#sendCLI_configCommand('source .script debug stop')
#warpBuffer_add('config term; snmp-server location test12')
#warpBuffer_execute('snmp-server contact ludo; end')


#mltDict, mltPortDict = extractMltData(['fa', 'vlacp', 'lacp-extra'])
#findUnusedPorts(mltPortDict)
#data = sendCLI_showRegex(CLI_Dict[Family]['get_mlt_type'])
#data = sendCLI_showRegex('list://show mlt||^(?:(\d+) +\d+.+?(?:access|trunk) +(norm|smlt) +(?:norm|smlt) +(\S+)|(\d+) +\d+ +\S+ +\S+ +\S+ +\S+ +\S+ +(enable|disable))')
#debug("data = {}".format(data))



