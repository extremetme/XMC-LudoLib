#
# IP address processing functions
# ip.py v5
#
import re                           # Used by maskToNumber

def ipToNumber(dottedDecimalStr): # v1 - Method to convert an IP/Mask dotted decimal address into a long number; can also use for checking validity of IP addresses
    try: # bytearray ensures that IP bytes are valid (1-255)
        ipByte = list(bytearray([int(byte) for byte in dottedDecimalStr.split('.')]))
    except:
        return None
    if len(ipByte) != 4:
        return None
    debug("ipByte = {}".format(ipByte))
    ipNumber = (ipByte[0]<<24) + (ipByte[1]<<16) + (ipByte[2]<<8) + ipByte[3]
    debug("dottedDecimalStr {} = ipNumber {}".format(dottedDecimalStr, hex(ipNumber)))
    return ipNumber

def numberToIp(ipNumber): # v1 - Method to convert a long number into an IP/Mask dotted decimal address
    dottedDecimalStr = '.'.join( [ str(ipNumber >> (i<<3) & 0xFF) for i in range(4)[::-1] ] )
    debug("ipNumber {} = dottedDecimalStr {}".format(hex(ipNumber), dottedDecimalStr))
    return dottedDecimalStr

def maskToNumber(mask): # v1 - Method to convert a mask (dotted decimal or Cidr number) into a long number
    if isinstance(mask, int) or re.match(r'^\d+$', mask): # Mask as number
        if int(mask) > 0 and int(mask) <= 32:
            maskNumber = (2**32-1) ^ (2**(32-int(mask))-1)
        else:
            maskNumber = None
    else:
        maskNumber = ipToNumber(mask)
    if maskNumber:
        debug("maskNumber = {}".format(hex(maskNumber)))
    return maskNumber

def subnetMask(ip, mask): # v1 - Return the IP subnet and Mask in dotted decimal and cidr formats for the provided IP address and mask
    ipNumber = ipToNumber(ip)
    maskNumber = maskToNumber(mask)
    subnetNumber = ipNumber & maskNumber
    ipSubnet = numberToIp(subnetNumber)
    ipDottedMask = numberToIp(maskNumber)
    ipCidrMask = bin(maskNumber).count('1')
    debug("ipSubnet = {} / ipDottedMask = {} / ipCidrMask = {}".format(ipSubnet, ipDottedMask, ipCidrMask))
    return ipSubnet, ipDottedMask, ipCidrMask

def ipGateway(ip, mask, gw): # v1 - Return the gateway IP address, as first or last IP in subnet, based on own IP/mask
    ipNumber = ipToNumber(ip)
    maskNumber = maskToNumber(mask)
    subnetNumber = ipNumber & maskNumber
    if gw == 'first':
        gwNumber = subnetNumber + 1
        ip1numb = gwNumber + 1
        ip2numb = gwNumber + 2
    elif gw == 'last':
        gwNumber = subnetNumber + 2**(32-int(mask)) - 2
        ip1numb = gwNumber - 2
        ip2numb = gwNumber - 1
    else: # Error condition
        exitError('ipGateway(): invalid gw type {}'.format(gw))
    debug("gwNumber = {} / ip1numb = {} / ip2numb = {}".format(hex(gwNumber), hex(ip1numb), hex(ip2numb)))
    gatewayIP = numberToIp(gwNumber)
    ip1 = numberToIp(ip1numb)
    ip2 = numberToIp(ip2numb)
    debug("gatewayIP = {} / ip1 = {} / ip2 = {}".format(gatewayIP, ip1, ip2))
    return gatewayIP, ip1, ip2
