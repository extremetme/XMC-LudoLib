#
# Workflow execution functions (requires apiXmc.py and apiXmcDict.py calls: getWorkflowIds + executeWorkflow + getWorkflowExecutionStatus)
# apiXmcWorkflow.py v7
#
import re
import json

def getWorkflowId(worflowPathName): # v2 - Returns the workflow id, or None if it does not exist or cannot be found
                                    # Syntax: workflowExists("Provisioning/Onboard VSP")
    # Get the name and category separately
    worflowCategory, worflowName = worflowPathName.split('/') 
    debug("getWorkflowId() worflowCategory = {} / worflowName = {}".format(worflowCategory, worflowName))
    # Get full list of workflows and their ids
    workflowsList = nbiQuery(NBI_Query['getWorkflowIds'], debugKey='workflowsList', returnKeyError=True)
    if LastNbiError:
        printLog("getWorkflowId() unable to extract workflowList; query:\n{}\nFailed with: {}".format(NBI_Query['getWorkflowIds'], LastNbiError))
        return None
    if not workflowsList:
        printLog("getWorkflowId() unable to extract workflowList; query:\n{}\nReturned None".format(NBI_Query['getWorkflowIds']))
        return None
    # Make a Dict of workflow names (keys) for workflow ids (values)
    worflowId = None
    workflowPath = None
    for wrkfl in workflowsList:
        if worflowCategory == wrkfl['category'] and worflowName == wrkfl['name']:
            if worflowId:
                printLog("getWorkflowId() duplicate workflow '{}' found in paths: {} and {}".format(worflowName, workflowPath, wrkfl['path']))
                return None
            worflowId = wrkfl['id']
            workflowPath = wrkfl['path']
    debug("getWorkflowId() workflowId = {}".format(worflowId))
    if not worflowId:
        printLog("getWorkflowId() workflow '{}' in category '{}' not found".format(worflowName, worflowCategory))
        return None
    return worflowId

def workflowExecute(worflowPathNameOrId, **kwargs): # v5 - Execute named workflow with inputs key:values
                                                    # Syntax: workflowExecute("Provisioning/Onboard VSP", deviceIP="10.10.10.10")
    # Get the workflow id
    if str(worflowPathNameOrId).isdigit():
        worflowId = worflowPathNameOrId
    else:
        worflowId = getWorkflowId(worflowPathNameOrId)
    debug("workflowExecute() workflowId = {}".format(worflowId))

    # Execute the workflow with inputs hash provided
    executionId = nbiMutation(NBI_Query['executeWorkflow'], ID=str(worflowId), JSONINPUTS=re.sub(r'"(\w*?)"(?=:)',r'\1',json.dumps(kwargs, sort_keys=True, indent=4)))
    return executionId

def workflowExecutionStatus(executionId): # v1 - Returns execution status of workflow with execution id provided
    # Returns:
    # - None  if workflow status is RUNNING
    # - True  if workflow status is SUCCESS
    # - False if workflow status is FAILED (this status also means non-existent executionId)
    execStatus = nbiQuery(NBI_Query['getWorkflowExecutionStatus'], EXECUTIONID=executionId)
    if execStatus == "RUNNING":
        return None
    elif execStatus == "SUCCESS" or execStatus == "COMPLETED":
        return True
    else: # execStatus == "FAILED"
        return False
