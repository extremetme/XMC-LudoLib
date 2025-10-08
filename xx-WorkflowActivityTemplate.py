# BEGIN *** WorkflowActivityTemplate_xx ***
__version__ = '1.00'
try:
    workflowVersion = emc_vars["wrkfl_VERSION"]
except:
    workflowVersion = None
# Written by Ludovico Stevens, Solution Engineering Extreme Networks
# Library of functions used in this script can be found here:
# https://github.com/extremetme/XMC-LudoLib

# What this script does

Debug = False    # Enables debug messages
Sanity = False   # If enabled, config commands are not sent to host (show commands are operational)
#Family = 'VSP Series'


#
# Functions, replace with sections required...
#



#
# Variables:
#

CLI_Dict = {
    'VSP Series': {
        'disable_more_paging'        : 'terminal more disable',
        'enable_context'             : 'enable',
        'config_context'             : 'config term',
        'exit_config_context'        : 'exit',
        'end_config'                 : 'end',
    },
    'Summit Series': {
        'disable_more_paging'        : 'disable cli paging',
        'disable_cli_prompting'      : 'disable cli prompting',
        'save_config'                : 'save configuration',
    },
}

Shell_Dict = { # Dictionary of all Linux shell commands used by this script
}

NBI_Query = { # GraphQl query / outValue = nbiQuery(NBI_Query['getDeviceUserData'], IP=deviceIp)
}

SNMP_Request = { # outValue = snmpGet|snmpSet|snmpWalk(SNMP_Request['<name>'], [instance=<instance>], [value=<value>])
# SAMPLE Syntax:
#   'queryName|mibName': {
#       'oid': <singleOid> | [<listOfOids>],      # For get & set; no leading dot
#       'asn': <ASN_?>,                           # Only for set, mandatory
#       'set': <value> | [<listOfValues>],        # Only for set, optional
#       'map': {'key1': <val1>, 'key2': <val2> }  # Mapping ascii values to int values
#   },
}


#
# INIT: Init Debug & Sanity flags based on input combos
#
try:
    if emc_vars['userInput_sanity'].lower() == 'enable':
        Sanity = True
    elif emc_vars['userInput_sanity'].lower() == 'disable':
        Sanity = False
except:
    pass
try:
    if emc_vars['userInput_debug'].lower() == 'enable':
        Debug = True
    elif emc_vars['userInput_debug'].lower() == 'disable':
        Debug = False
except:
    pass

#
# Other Imports:
#
#import re
#import json

#
# Main:
#
def main():

#    setupDebugFileLogging() # Debugging to /dev/shm/<exec-id>_<workflow-path>/<activity>
    printLog("Workflow version {} on XIQ-SE/XMC version {}".format(workflowVersion, emc_vars["serverVersion"]))
    printLog("Activity: WorkflowActivityTemplate_xx version {}".format(__version__))

#    if emc_vars["inst_device_success"].lower() != 'true': # For multi-device workflows, on all activities but the first
#        exitError("Failing this activity for device {} as previous activity failed for same device".format(emc_vars['deviceIP']))

    setFamily(CLI_Dict) # Sets global Family variable

    # Get inputs
    ipAddress                = emc_vars['deviceIP']
    siteVarDict              = readSiteCustomVariables(ipAddress)
    variable                 = siteVarLookup(emc_vars['input_variable'], siteVarDict)
    try:
        cliRetries           = emc_vars['const_CLI_RETRIES']
    except:
        cliRetries           = 6
    try:
        cliRetryDelay        = emc_vars['const_CLI_RETRY_DELAY']
    except:
        cliRetryDelay        = 10
    try:
        flag                 = True if emc_vars['const_cliCmdsFailOnError'].lower() == 'true' else False
    except:
        flag                 = True


    # Display all input data
    printLog
    printLog("Input Data:")
    printLog(" - Selected Switch IP = {}".format(ipAddress))
    printLog(" - CLI retries = {}".format(cliRetries))
    printLog(" - CLI retry delay = {}".format(cliRetryDelay))
    printLog


    # Disable more paging
    sendCLI_showCommand(CLI_Dict[Family]['disable_more_paging'], retries=cliRetries, retryDelay=cliRetryDelay)

    # Enter privExec
    if 'enable_context' in CLI_Dict[Family]:
        sendCLI_showCommand(CLI_Dict[Family]['enable_context'])

    # Enter Config context
    sendCLI_configCommand(CLI_Dict[Family]['config_context'])

# ...

    # Exit Config context
    sendCLI_configCommand(CLI_Dict[Family]['end_config'])

    # Set workflow variables
    emc_results.put("wrkfl_vmImage", vmImage)

    # Print summary of config performed
    printConfigSummary()

    # Set workflow messages
    workflow_DeviceMessage("Configured RADIUS and EAPoL on device(s) <>")

    # Exit code will be success if we get here
#    emc_results.put("inst_device_success",  "true") # For multi-device workflows
    emc_results.setStatus(emc_results.Status.SUCCESS)
    printLog("Exit code SUCCESS")

try:
    main()
except Exception:
    emc_results.setStatus(emc_results.Status.ERROR)
    printLog(traceback.format_exc())

# END *** WorkflowActivityTemplate_xx ***
