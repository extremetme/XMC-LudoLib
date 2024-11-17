#
# Base functions
# base.py v8
#
import re                           # Used by scriptName
import time                         # Used by debug & exitError
ExitErrorSleep = 10

def debug(debugOutput): # v2 - Use function to include debugging in script; set above Debug variable to True or False to turn on or off debugging
    if Debug:
        print "[{}] {}".format(time.ctime(), debugOutput)

def exitError(errorOutput, sleep=ExitErrorSleep): # v3 - Exit script with error message and setting status appropriately
    if 'workflowMessage' in emc_vars: # Workflow
        time.sleep(sleep) # When workflow run on multiple devices, want ones that error to be last to complete, so THEY set the workflow message
        emc_results.put("deviceMessage", errorOutput)
        emc_results.put("activityMessage", errorOutput)
        emc_results.put("workflowMessage", errorOutput)
    emc_results.setStatus(emc_results.Status.ERROR)
    raise RuntimeError(errorOutput)

def abortError(cmd, errorOutput): # v1 - A CLI command failed, before bombing out send any rollback commands which may have been set
    print "Aborting script due to error on previous command"
    try:
        rollbackStack()
    finally:
        print "Aborting because this command failed: {}".format(cmd)
        exitError(errorOutput)

def scriptName(): # v1 - Returns the assigned name of the Script or Workflow
    name = None
    if 'workflowName' in emc_vars: # Workflow
        name = emc_vars['workflowName']
    elif 'javax.script.filename' in emc_vars: # Script
        nameMatch = re.search(r'\/([^\/\.]+)\.py$', emc_vars['javax.script.filename'])
        name = nameMatch.group(1) if nameMatch else None
    return name

def workflow_DeviceMessage(msg): # v1 - Set workflow messages appropriately; '<>' is replaced with device IP or list
    singleDeviceMsg = manyDevicesMsg = msg
    if '<>' in msg:
        devicesListStr = emc_vars['devices'][1:-1]
        singleDeviceMsg = msg.replace('<>', emc_vars['deviceIP']).replace('(s)', '').replace('(es)', '')
        if len(devicesListStr.split(',')) > 1:
            manyDevicesMsg = msg.replace('<>', devicesListStr).replace('(s)', 's').replace('(es)', 'es')
        else:
            manyDevicesMsg = singleDeviceMsg
    emc_results.put("deviceMessage", singleDeviceMsg)
    emc_results.put("activityMessage", manyDevicesMsg)
    emc_results.put("workflowMessage", manyDevicesMsg)
