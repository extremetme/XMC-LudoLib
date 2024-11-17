#
# Syslog functions
# syslog.py v1
#
import socket

def addXmcSyslogEvent(severity, message, ip=None): # v1 - Adds a syslog event to XMC (only needed for Scripts)
    severityHash = {'emerg': 0, 'alert': 1, 'crit': 2, 'err': 3, 'warning': 4, 'notice': 5, 'info': 6, 'debug': 7}
    severityLevel = severityHash[severity] if severity in severityHash else 6
    session = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    session.connect(('127.0.0.1', 514))
    if ip:
        session.send("<{}> XMC Script {} / Device: {} / {}".format(severityLevel,scriptName(),ip,message))
    else:
        session.send("<{}> XMC Script {} / {}".format(severityLevel,scriptName(),ip,message))
    session.close()
