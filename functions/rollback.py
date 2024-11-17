#
# CLI/SNMP Rollback functions
# rollback.py v4
#
RollbackStack = [] # Format [ ['cli', <command>], ['snmp', [requestDict, instance, oldValue], ...]]

def rollbackStack(): # v2 - Execute all commands on the rollback stack
    if RollbackStack:
        print "\nApplying rollback commands to undo partial config and return device to initial state"
        while RollbackStack:
            cfgType, data = RollbackStack.pop()
            if cfgType == 'cli':
                sendCLI_configChain(data, returnCliError=True)
            elif cfgType == 'snmp':
                snmpSet(data[0], instance=data[1], value=data[2], returnError=True)
            else:
                print "Invalid rollback stack data entry: {}".format(cfgType)

def rollbackCommand(cmd): # v2 - Add a command to the rollback stack; these commands will get popped and executed should we need to abort
    global RollbackStack
    RollbackStack.append(['cli', cmd])
    cmdList = map(str.strip, re.split(r'[;\n]', cmd)) # cmd could be a configChain
    cmdList = [x for x in cmdList if x] # Weed out empty elements 
    cmdOneLiner = " / ".join(cmdList)
    print "Pushing onto rollback stack CLI: {}\n".format(cmdOneLiner)

def rollbackSnmp(requestDict, instance, oldValue): # v1 - Add SNMP request to rollback stack
    # These commands will get popped and executed as snmpSet should we need to abort
    global RollbackStack
    RollbackStack.append(['snmp', [requestDict, instance, oldValue]])
    oidList, instList, _, valueList = snmpInputLists("rollbackSnmp", requestDict, instance, oldValue)
    print "Pushing onto rollback stack SNMP:"
    for inOid, inst, currVal in zip(oidList, instList, valueList):
        displayOid, oid = separateOid(inOid)
        setOid = '.'.join([oid, str(inst)]) if inst != None else oid
        print " - {}{} revert to {}".format(displayOid, setOid, currVal)

def rollBackPop(number=0): # v1 - Remove entries from RollbackStack
    global RollbackStack
    if number == 0:
        RollbackStack = []
        print "Rollback stack emptied"
    else:
        del RollbackStack[-number:]
        print "Rollback stack popped last {} entries".format(number)
