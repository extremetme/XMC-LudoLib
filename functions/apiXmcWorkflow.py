#
# Workflow execution functions (requires apiXmc.py and apiXmcDict.py calls: getWorkflowIds + executeWorkflow)
# apiXmcWorkflow.py v4
#
import re
import json

def getWorkflowId(worflowPathName): # v1 - Returns the workflow id, or None if it does not exist or cannot be found
                                    # Syntax: workflowExists("Provisioning/Onboard VSP")
    # Get the name and category separately
    worflowCategory, worflowName = worflowPathName.split('/') 
    debug("getWorkflowId() worflowCategory = {} / worflowName = {}".format(worflowCategory, worflowName))
    # Get full list of workflows and their ids
    workflowsList = nbiQuery(NBI_Query['getWorkflowIds'], debugKey='workflowsList', returnKeyError=True)
    if LastNbiError:
        print "getWorkflowId() unable to extract workflowList; query:\n{}\nFailed with: {}".format(NBI_Query['getWorkflowIds'], LastNbiError)
        return None
    if not workflowsList:
        print "getWorkflowId() unable to extract workflowList; query:\n{}\nReturned None".format(NBI_Query['getWorkflowIds'])
        return None
    # Make a Dict of workflow names (keys) for workflow ids (values)
    worflowId = None
    workflowPath = None
    for wrkfl in workflowsList:
        if worflowCategory == wrkfl['category'] and worflowName == wrkfl['name']:
            if worflowId:
                print "getWorkflowId() duplicate workflow '{}' found in paths: {} and {}".format(worflowName, workflowPath, wrkfl['path'])
                return None
            worflowId = wrkfl['id']
            workflowPath = wrkfl['path']
    debug("getWorkflowId() workflowId = {}".format(worflowId))
    if not worflowId:
        print "getWorkflowId() workflow '{}' in category '{}' not found".format(worflowName, worflowCategory)
        return None
    return worflowId

def workflowExecute(worflowPathNameOrId, **kwargs): # v3 - Execute named workflow with inputs key:values
                                                    # Syntax: workflowExecute("Provisioning/Onboard VSP", deviceIP="10.10.10.10")
    # Get the workflow id
    if str(worflowPathNameOrId).isdigit():
        worflowId = worflowPathNameOrId
    else:
        worflowId = getWorkflowId(worflowPathNameOrId)
    debug("workflowExecute() workflowId = {}".format(worflowId))

    # Execute the workflow with inputs hash provided
    executionId = nbiMutation(NBI_Query['executeWorkflow'], ID=str(worflowId), JSONINPUTS=re.sub(r'"(.*?)"(?=:)',r'\1',json.dumps(kwargs)))
    return executionId
