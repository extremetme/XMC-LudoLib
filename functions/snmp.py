#
# SNMP functions - (use of rollback requires rollback.py)
# snmp.py v3
#
import re
from xmclib.snmplib import SnmpRequest
from xmclib.snmplib import SnmpVarbind
from xmclib.snmplib import ASN_INTEGER, ASN_OCTET_STR, ASN_OCTET_STR_DEC, ASN_OCTET_STR_HEX, ASN_OCTET_STR_PRINTABLE, \
                           ASN_OBJECT_ID, ASN_IPADDRESS, ASN_COUNTER, ASN_UNSIGNED, ASN_GAUGE, ASN_TIMETICKS, ASN_COUNTER64, \
                           ASN_OPAQUE_FLOAT, ASN_OPAQUE_DOUBLE, ASN_OPAQUE_U64, ASN_OPAQUE_I64
SnmpTarget = None
SnmpTimeout = 3
SnmpRetries = 3
LastSnmpError = None

def snmpTarget(ipAddress=emc_vars["deviceIP"], timeout=None, retries=None): # v1 - Sets SNMP target IP
    global SnmpTarget
    SnmpTarget = SnmpRequest(ipAddress)
    if timeout:
        global SnmpTimeout
        SnmpTimeout = timeout
    if retries:
        global SnmpRetries
        SnmpRetries = retries


def separateOid(inOid): # v1 - Separates the OID name from the OID value
    if re.search(r':', inOid):
        displayOid, oid = map(str.strip, inOid.split(':', 1))
        displayOid += ':'
    else:
        displayOid = ''
        oid = inOid
    return displayOid, oid


def snmpInputLists(caller, requestDict, instance=None, value=None): # v1 - Validate inputs and prepare input lists
    if not SnmpTarget:
        exitError("{}() cannot be called without first setting up an SNMP target with snmpTarget()".format(caller))
    if not requestDict:
        exitError("{}() no request dictionary definition supplied".format(caller))

    if caller in ('snmpSet', 'snmpCheckSet') and value == None:
        if 'set' in requestDict:
            value = requestDict['set']
        else:
            exitError("{}() no value to set".format(caller))

    if isinstance(requestDict['oid'], str): # If a string.. i.e. single OID
        if isinstance(requestDict['asn'], list):
            exitError("{}() single OID provided but list of {} ASN types".format(caller, len(requestDict['asn'])))
        if isinstance(instance, list):
            oidList = [requestDict['oid']] * len(instance) # Make it a list of same size as instances with all the same OID value
            asnList = [requestDict['asn']] * len(instance) # Do the same for ASN types
        else:
            oidList = [requestDict['oid']] # Make it a 1 element list
            asnList = [requestDict['asn']] # Do the same for ASN type
    else:
        oidList = requestDict['oid']

    if isinstance(requestDict['asn'], list): # List of ASN types provided
        if len(requestDict['asn']) != len(oidList):
            exitError("{}() supplied list of {} OIDs but list of {} ASN types".format(caller, len(oidList), len(requestDict['asn'])))
        asnList = requestDict['asn']

    if instance == None:
        instList = [None] * len(oidList)
    elif isinstance(instance, list): # List of instances provided
        if len(instance) != len(oidList):
            exitError("{}() supplied list of {} OIDs but list of {} instances".format(caller, len(oidList), len(instance)))
        instList = instance
    else: # Single instance provided
        instList = [instance] * len(oidList) # Make a list of same size as OIDs with all the same value

    if value == None:
        valueList = []
    if isinstance(value, list): # List of values provided
        if len(value) != len(oidList):
            exitError("{}() supplied list of {} OIDs but list of {} values".format(caller, len(oidList), len(value)))
        for val in value:
            if 'map' in requestDict and val in requestDict['map']:
                valueList.append(requestDict['map'][value])
            else:
                valueList.append(val)
    else: # Single value provided
        if 'map' in requestDict and value in requestDict['map']:
            valueList = [requestDict['map'][value]] * len(oidList) # Make a list of same size as OIDs with all the same value
        else:
            valueList = [value] * len(oidList) # Make a list of same size as OIDs with all the same value

    debug("{} snmpInputLists:\n - oidList = {}\n - instList = {}\n - asnList = {}\n - valueList = {}".format(caller, oidList, instList, asnList, valueList))
    return oidList, instList, asnList, valueList


def snmpGet(requestDict, instance=None, timeout=None, retries=None, debugVal=None, returnError=False): # v2 - Performs SNMP get
    # RequestDict oid key can be a single OID, or it can be a list of OIDs
    # If a list of OIDs, then instance can either be a single value or a list
    #    - if single instance, then the instance will be applied to all OIDs
    #    - if list of instances, then these need to be of same size as the list of OIDs
    # If a single OID, then instance can again either be a single value or a list
    # Returns either single value (for single OID)
    # or a list of values (for multiple OIDs) in same order

    global LastSnmpError

    # Validate and prepare input lists
    oidList, instList, _, _ = snmpInputLists("snmpGet", requestDict, instance)

    # Prepare SNMP varbinds
    varbinds = []
    for inOid, inst in zip(oidList, instList):
        displayOid, oid = separateOid(inOid)
        getOid = '.'.join([oid, str(inst)]) if inst != None else oid
        varbinds.append(SnmpVarbind(oid=getOid))
        debug("snmpGet request {}{}".format(displayOid, getOid))
    timeout = timeout if timeout else SnmpTimeout
    retries = retries if retries else SnmpRetries

    # Perform SNMP request
    response = SnmpTarget.snmp_get(varbinds, timeout=timeout, retries=retries)
    if response.ok:
        LastSnmpError = None
        retValue = []
        for binding in response.vars:
            retValue.append(binding.val)
            debug("snmpGet response {} = {}".format(binding.var, binding.val))
        if len(retValue) == 1:
            retValue = retValue[0]
        if debugVal:
            debug("snmpGet response {} = {}".format(debugVal, retValue))
        else:
            debug("snmpGet response retValue = {}".format(retValue))
        return retValue

    # In case of error
    if returnError: # If we asked to return upon SNMP error, then the error message will be held in LastSnmpError
        LastSnmpError = response.error
        return None
    abortError("snmpGet for\n{}".format(requestDict['oid']), response.error)


def snmpWalk(requestDict, timeout=None, retries=None, returnError=False): # v2 - Performs SNMP walk
    # RequestDict oid key can be a single OID, or it can be a list of OIDs
    # Returns a dict with format:
    # {
    #     instance1: {oid1: value, oid2: value, ...},
    #     instance2: {oid1: value, oid2: value, ...},
    #     ...
    # }

    global LastSnmpError

    # Validate and prepare input lists
    oidList, _, _, _ = snmpInputLists("snmpWalk", requestDict)

    # Prepare SNMP varbinds
    varbinds = []
    for inOid in oidList:
        displayOid, oid = separateOid(inOid)
        varbinds.append(SnmpVarbind(oid=oid))
        debug("snmpWalk request {}{}".format(displayOid, oid))
    timeout = timeout if timeout else SnmpTimeout
    retries = retries if retries else SnmpRetries

    # Perform SNMP request
    response = SnmpTarget.snmp_get_next(varbinds, timeout=timeout, retries=retries)
    if response.ok:
        LastSnmpError = None
        if Debug:
            for instance in response.data:
                for oid in response.data[instance]:
                    debug("snmpWalk response {} = {}".format(oid, response.data[instance][oid]))
        return response.data

    # In case of error
    if returnError: # If we asked to return upon SNMP error, then the error message will be held in LastSnmpError
        LastSnmpError = response.error
        return None
    abortError("snmpGetNext for\n{}".format(requestDict['oid']), response.error)


def snmpSet(requestDict, instance=None, value=None, timeout=None, retries=None, returnError=False): # v3 - Performs SNMP set
    # RequestDict oid key can be a single OID, or it can be a list of OIDs
    # If a list of OIDs, then instance, ASN & value can either be a single value or lists
    #    - if single value, then the instance|ASN|value will be applied to all OIDs
    #    - if list of values, then these need to be of same size as the list of OIDs
    # If a single OID, then instance can again either be a single value or a list
    #    - if instance is a list, then values can also be a list, but of same length

    global LastSnmpError
    if Sanity:
        print "SANITY - SNMP Set:"
    else:
        print "SNMP Set:"

    # Validate and prepare input lists
    oidList, instList, asnList, valueList = snmpInputLists("snmpSet", requestDict, instance, value)

    # Prepare SNMP varbinds
    varbinds = []
    for inOid, inst, asn, val in zip(oidList, instList, asnList, valueList):
        displayOid, oid = separateOid(inOid)
        setOid = '.'.join([oid, str(inst)]) if inst != None else oid
        print " - {}{} = {}".format(displayOid, setOid, val)
        varbinds.append(SnmpVarbind(oid=setOid, asn_type=asn, value=str(val)))
        debug("snmpSet request {}{} = {}".format(displayOid, setOid, val))
    if Sanity:
        LastNbiError = None
        return True
    timeout = timeout if timeout else SnmpTimeout
    retries = retries if retries else SnmpRetries

    # Perform SNMP request
    response = SnmpTarget.snmp_set(varbinds, timeout=timeout, retries=retries)
    valueSetFlag = True # Assume all good
    if response.ok:
        for binding, val in zip(response.vars, valueList): # Then check
            debug("snmpSet response {} = {}".format(binding.var, binding.val))
            if binding.val != str(val):
                valueSetFlag = False
        if valueSetFlag: # All good
            LastSnmpError = None
            return True
        # Else fall through

    # In case of error
    LastSnmpError = "Values not set as expected" if not valueSetFlag else response.error
    if returnError: # If we asked to return upon SNMP error, then the error message will be held in LastSnmpError
        debug("snmpSet snmpError = {}".format(LastSnmpError))
        return False
    abortError("snmpSet for\n{}".format(requestDict['oid']), LastSnmpError)


def snmpCheckSet(requestDict, instance=None, value=None, timeout=None, retries=None, returnError=False, returnNoSuchObj=True, rollback=False): # v1 - Performs SNMP set based on get value
    # Essentially same as snmpSet(), except that snmpGet() is first called to check whether the OID(s) are writable and if they are already set to same value
    # So an snmpSet() is only performed if the OID is writeable and the OID is not currently set to the desired value
    # Also implements rollback: in case of workflow failure, OID wich were set, are restored to their initial values
    # RequestDict oid key can be a single OID, or it can be a list of OIDs
    # If a list of OIDs, then instance, ASN & value can either be a single value or lists
    #    - if single value, then the instance|ASN|value will be applied to all OIDs
    #    - if list of values, then these need to be of same size as the list of OIDs
    # If a single OID, then instance can again either be a single value or a list
    #    - if instance is a list, then values can also be a list, but of same length

    print "SNMP Check:"

    # Validate and prepare input lists
    oidList, instList, asnList, valueList = snmpInputLists("snmpCheckSet", requestDict, instance, value)

    # Get current value of OID(s)
    currentValue = snmpGet(requestDict, instance=instance, timeout=timeout, retries=retries, returnError=True)

    # In list format
    if isinstance(currentValue, (str, unicode)): # If a string.. i.e. single value
        currValueList = [currentValue] # Make it a 1 element list
    else: # Is a list, make copy
        currValueList = currentValue

    noSuchObjFlag = False
    sameValueFlag = True
    for inOid, inst, currVal, val in zip(oidList, instList, currValueList, valueList):
        displayOid, oid = separateOid(inOid)
        setOid = '.'.join([oid, str(inst)]) if inst != None else oid
        print " - {}{} = {}".format(displayOid, setOid, currVal)
        if re.match(r'No Such Object', currVal): # OID not supported on device
            noSuchObjFlag = True
        elif currVal != str(val): # OID not set to desired value
            sameValueFlag = False
        else: # OID already set to desired value(s); nothing to do
            debug("snmpCheckSet already-set {}{} = {}".format(displayOid, setOid, val))

    if noSuchObjFlag:
        if returnNoSuchObj: # Ignore (note, enough to get No Such object on one OID, and all OIDs will be skipped)
            return False
        else: # Bomb
            abortError("snmpCheckSet for\n{}".format(requestDict['oid']), "No Such Object")

    if sameValueFlag: # Values already set as desired
        return True

    else: # We need to set desired value(s)
        snmpSet(requestDict, instance=instance, value=value, timeout=timeout, retries=retries, returnError=returnError)
        if rollback:
            rollbackSnmp(requestDict, instance, currentValue)
