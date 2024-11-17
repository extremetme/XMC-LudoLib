'''
This script is provided free of charge by Extreme. We hope such scripts are
helpful when used in conjunction with Extreme products and technology and can
be used as examples to modify and adapt for your ultimate requirements.
Extreme will not provide any official support for these scripts. If you do
have any questions or queries about any of these scripts you may post on
Extreme's community website "The Hub" (https://community.extremenetworks.com/)
under the scripting category.

ANY SCRIPTS PROVIDED BY EXTREME ARE HEREBY PROVIDED "AS IS", WITHOUT WARRANTY
OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL EXTREME OR ITS THIRD PARTY LICENSORS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE USE OR DISTRIBUTION OF SUCH
SCRIPTS.
'''

# --> Insert here script description, version and metadata <--

##########################################################
# XMC Script: <name of script>                           #
# Written by Ludovico Stevens, TME Extreme Networks      #
##########################################################

__version__ = '0.1'

'''
#@MetaDataStart
#@DetailDescriptionStart
#######################################################################################
# 
# <description, over multiple lines>
#
#######################################################################################
#@DetailDescriptionEnd
# ( = &#40;
# ) = &#41;
# , = &#44;
# < = &lt;
# > = &gt;
#@SectionStart (description = "Sanity / Debug")
#    @VariableFieldLabel (
#        description = "Sanity: enable if you do not trust this script and wish to first see what it does. In sanity mode config commands are not executed",
#        type = string,
#        required = no,
#        validValues = [Enable, Disable],
#        name = "userInput_sanity",
#    )
#    @VariableFieldLabel (
#        description = "Debug: enable if you need to report a problem to the script author",
#        type = string,
#        required = no,
#        validValues = [Enable, Disable],
#        name = "userInput_debug",
#    )
#@SectionEnd
#@MetaDataEnd
'''

Debug = False    # Enables debug messages
Sanity = False   # If enabled, config commands are not sent to host (show commands are operational)



# --> Insert required functions <--



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
# MAIN:
#
def main():
    print "{} version {} on XIQ-SE/XMC version {}".format(scriptName(), __version__, emc_vars["serverVersion"])
    nbiAccess = nbiQuery(NBI_Query['nbiAccess'], returnKeyError=True)
    if nbiAccess == None:
        exitError('This XMC Script requires access to the GraphQl North Bound Interface (NBI). Make sure that XMC is running with an Advanced license and that your user profile is authorized for Northbound API.')

    # Obtain Info on switch and from XMC
    setFamily(CLI_Dict) # Sets global Family variable

    # Disable more paging
    sendCLI_showCommand(CLI_Dict[Family]['disable_more_paging'])

    # Enter privExec
    sendCLI_showCommand(CLI_Dict[Family]['enable_context'])

    # Enter Config context
    sendCLI_configCommand(CLI_Dict[Family]['config_context'])


    # Save config & exit
    sendCLI_configChain(CLI_Dict[Family]['end_save_config'])

    # Print summary of config performed
    printConfigSummary()

    # Make XMC re-discover the switch
    if nbiMutation(NBI_Query['rediscover_device'].replace('<IP>', emc_vars['deviceIP'])):
        print "Initiated XMC rediscovery of switch"
    else:
        print "Failed to trigger XMC rediscovery of switch; perform manually"


main()
