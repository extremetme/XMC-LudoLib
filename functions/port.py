#
# Port processing functions
# port.py v6
#
RegexPort = re.compile('^(?:[1-9]\d{0,2}[/:])?\d+(?:[/:]\d)?$')
RegexPortRange = re.compile('^(?:([1-9]\d{0,2})([/:]))?(\d+)(?:[/:](\d))?-(?:([1-9]\d{0,2})[/:])?(\d+)(?:[/:](\d))?$')
RegexStarRange = re.compile('^([1-9]\d{0,2})(:)\*$') # XOS only
SlotPortRange = None # Gets set to dict by getSlotPortRanges()

def portValue(port): # v1 - Function to pass to sorted(key) to sort port lists
    slotPort = re.split('[/:]', port)
    if len(slotPort) == 3: # slot/port/chan format
        idx = int(slotPort[0])*400 + int(slotPort[1])*4 + int(slotPort[2])
    elif len(slotPort) == 2: # slot/port format
        idx = int(slotPort[0])*400 + int(slotPort[1])*4
    else: # standalone port (no slot)
        idx = int(slotPort[0])*4
    return idx

def getSlotPortRanges(): # v1 - Populates the SlotPortRange dict
    global SlotPortRange
    slotCommand = {'Summit Series': 'dict://show slot||^Slot-(\d+) +\S+ +\S+ +\S+ +(\d+)'} # Only XOS supported
    if Family not in slotCommand:
        SlotPortRange = {}
        return
    SlotPortRange = sendCLI_showRegex(slotCommand[Family])
    debug("getSlotPortRanges = {}".format(SlotPortRange))

def generatePortList(portStr, debugKey=None): # v3 - Given a port list/range, validates it and returns an ordered port list with no duplicates (can also be used for VLAN-id ranges)
    # This version of this function will not handle port ranges which span slots
    debug("generatePortList IN = {}".format(portStr))
    portDict = {} # Use a dict, will ensure no port duplicate keys
    for port in portStr.split(','):
        port = re.sub(r'^[\s\(]+', '', port) # Remove leading spaces  [ or '(' ]
        port = re.sub(r'[\s\)]+$', '', port) # Remove trailing spaces [ or ')' => XMC bug on ERS standalone units]
        if not len(port): # Skip empty string
            continue
        rangeMatch = RegexPortRange.match(port)
        starMatch = RegexStarRange.match(port)
        if rangeMatch: # We have a range of ports
            startSlot = rangeMatch.group(1)
            separator = rangeMatch.group(2)
            startPort = int(rangeMatch.group(3))
            startChan = int(rangeMatch.group(4)) if rangeMatch.group(4) else None
            endSlot = rangeMatch.group(5)
            endPort = int(rangeMatch.group(6))
            endChan = int(rangeMatch.group(7)) if rangeMatch.group(4) else None
            if endSlot and startSlot != endSlot:
                print "ERROR! generatePortList no support for ranges spanning slots: {}".format(port)
            elif (startChan or endChan) and endPort and startPort != endPort:
                print "ERROR! generatePortList no support for ranges spanning channelized ports: {}".format(port)
            elif not (startChan or endChan) and startPort >= endPort:
                print "ERROR! generatePortList invalid range: {}".format(port)
            elif (startChan or endChan) and startChan >= endChan:
                print "ERROR! generatePortList invalid range: {}".format(port)
            else: # We are good
                if startChan:
                    for portCount in range(startChan, endChan + 1):
                        portDict[startSlot + separator + str(startPort) + separator + str(portCount)] = 1
                else:
                    for portCount in range(startPort, endPort + 1):
                        if startSlot: # slot-based range
                            portDict[startSlot + separator + str(portCount)] = 1
                        else: # simple port range (no slot info)
                            portDict[str(portCount)] = 1
        elif starMatch: # We have a slot/* range
            slot = starMatch.group(1)
            separator = starMatch.group(2)
            if SlotPortRange == None: # Structure not populated
                getSlotPortRanges()
            if SlotPortRange:
                if slot in SlotPortRange:
                    for portCount in range(1, int(SlotPortRange[slot]) + 1):
                        portDict[slot + separator + str(portCount)] = 1
                else:
                    print "Warning: no range for slot {}; skipping: {}".format(slot, port)
            else:
                print "Warning: generatePortList skipping star range as not supported on this switch type: {}".format(port)
        elif RegexPort.match(port): # Port is in valid format
            portDict[port] = 1
        else: # Port is in an invalid format; don't add to dict, print an error message, don't raise exception 
            print "Warning: generatePortList skipping unexpected port format: {}".format(port)

    # Sort and return the list as a comma separated string
    portList = sorted(portDict, key=portValue)

    if Debug:
        if debugKey: debug("{} = {}".format(debugKey, portList))
        else: debug("generatePortList OUT = {}".format(portList))
    return portList

def generatePortRange(portList, debugKey=None): # v3 - Given a list of ports, generates a compacted port list/range string for use on CLI commands
    # Ported from acli.pl; this version of this function only compacts ranges within same slot
    debug("generatePortRange IN = {}".format(portList))
    rangeMode = {'VSP Series': 2, 'ERS Series': 1, 'Summit Series': 1}
    elementList = []
    elementBuild = None
    currentType = None
    currentSlot = None
    currentPort = None
    currentChan = None
    rangeLast = None

    # First off, sort the list
    portList = sorted(portList, key=portValue)
    for port in portList:
        slotPort = re.split("([/:])", port) # Split on '/' (ERS/VSP) or ':'(XOS)
        # slotPort[0] = slot / slotPort[1] = separator ('/' or ':') / slotPort[2] = port / slotPort[4] = channel
        if len(slotPort) == 5: # slot/port/chan
            if elementBuild:
                if currentType == 's/p' and slotPort[0] == currentSlot and slotPort[2] == currentPort and currentChan and slotPort[4] == str(int(currentChan)+1):
                    currentChan = slotPort[4]
                    if rangeMode[Family] == 1:
                        rangeLast = currentChan
                    else: # rangeMode = 2
                        rangeLast = currentSlot + slotPort[1] + currentPort + slotPort[1] + currentChan
                    continue
                else: # Range complete
                    if rangeLast:
                        elementBuild += '-' + rangeLast
                    elementList.append(elementBuild)
                    elementBuild = None
                    rangeLast = None
                    # Fall through below
            currentType = 's/p'
            currentSlot = slotPort[0]
            currentPort = slotPort[2]
            currentChan = slotPort[4]
            elementBuild = port

        if len(slotPort) == 3: # slot/port
            if elementBuild:
                if currentType == 's/p' and slotPort[0] == currentSlot and slotPort[2] == str(int(currentPort)+1) and not currentChan:
                    currentPort = slotPort[2]
                    if rangeMode[Family] == 1:
                        rangeLast = currentPort
                    else: # rangeMode = 2
                        rangeLast = currentSlot + slotPort[1] + currentPort
                    continue
                else: # Range complete
                    if rangeLast:
                        elementBuild += '-' + rangeLast
                    elementList.append(elementBuild)
                    elementBuild = None
                    rangeLast = None
                    # Fall through below
            currentType = 's/p'
            currentSlot = slotPort[0]
            currentPort = slotPort[2]
            currentChan = None
            elementBuild = port

        if len(slotPort) == 1: # simple port (no slot)
            if elementBuild:
                if currentType == 'p' and port == str(int(currentPort)+1):
                    currentPort = port
                    rangeLast = currentPort
                    continue
                else: # Range complete
                    if rangeLast:
                        elementBuild += '-' + rangeLast
                    elementList.append(elementBuild)
                    elementBuild = None
                    rangeLast = None
                    # Fall through below
            currentType = 'p'
            currentPort = port
            elementBuild = port

    if elementBuild: # Close off last element we were holding
        if rangeLast:
            elementBuild += '-' + rangeLast
        elementList.append(elementBuild)

    portStr = ','.join(elementList)
    if Debug:
        if debugKey: debug("{} = {}".format(debugKey, portStr))
        else: debug("generatePortRange OUT = {}".format(portStr))
    return portStr
