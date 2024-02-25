import re
import os

Debug = True

nick = '0.aa.01'
nmask = '0.ff.00'
sysid = '02aa.0000.8182'
mask = '00ff.0000.0000'
value = '99'

def debug(debugOutput): # v1 - Use function to include debugging in script; set above Debug variable to True or False to turn on or off debugging
    if Debug:
        print debugOutput


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
    inIdNumber = idToNumber(sysid)
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
    return numberToSystemId(idReplMask(sysid, mask, value))

def macReplMask(mac, mask, value): # v1 - Replaces MAC address masked bits with value provided
    return numberToMacAddr(idReplMask(sysid, mask, value))


print systemIdReplMask(sysid, mask, value)

print macReplMask(sysid, mask, value)

print nicknameReplMask(nick, nmask, value)

mylist = ['2', '1', '5']
print "list1 = {}".format(mylist)
mylist.sort(key=int)
print "list2 = {}".format(mylist)

print os.getcwd()

import re
inputStr = '$<var1> and $(var2)'
csvVarsUsed = {x.group(1):1 for x in list(re.finditer(r'\$<([\w -]+)>', inputStr)) + list(re.finditer(r'\$\(([\w -]+)\)', inputStr))}
print csvVarsUsed
