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
execfile("XMC-Python-Ludo-Threads-Library.py")



Debug = True
Sanity = False

#Family = 'ERS Series'
Family = 'VSP Series'
#Family = 'ISW-Series'
#Family = 'ISW-Series-Marvell'

print "Before calling emc_threads_put()"
emc_threads_put(test = 'bogus')
print "After calling emc_threads_put()"

print "Before calling emc_threads()"
threads = emc_threads(returnOnError = True)
#threads = emc_threads()
print "After calling emc_threads()"

print "Number of threads = {}".format(len(threads))
print "Thread IPs = {}".format(threads)

print "Name of every device in every script instance:"
for ip in threads:
    print " - switch {} has name {}".format(ip, emc_threads_vars(ip, "deviceName"))


sendCLI_showCommand(CLI_Dict[Family]['disable_more_paging'])
if 'enable_context' in CLI_Dict[Family]:
    sendCLI_showCommand(CLI_Dict[Family]['enable_context'])
mymac = sendCLI_showRegex(CLI_Dict[Family]['get_mac_address'])[0]
print "My mac = {}".format(mymac)


emc_threads_put(mymac = mymac)

print "MAC address of every device in every script instance:"
for ip in threads:
    print " - switch {} has mac {}".format(ip, emc_threads_vars(ip, "mymac", True))
