#
# CSV data input
# varsCsv.py v17
#
import os.path
import csv
import json
import re
import io

def readCsvToDict(csvFilePath, lookup=None, delimiter=','): # v8 - Read CSV data file, return dict with data
    # It is expected that the 1st CSV row has the column value keys
    # And that the index to data are the values in column 0
    # Row0 Column0 is returned as 2nd value
    # Example CSV:
    #    ip,      var1, var2, var3
    #    1.1.1.1, 11,   21,   10
    #    2.2.2.2, 12,   22,   10
    #    3.3.3.3, 13,   23,   11
    # With lookup=None returns csvVarDict:
    # {
    #    "1.1.1.1": { "var1": 11, "var2": 21, "var3": 10 },
    #    "2.2.2.2": { "var1": 12, "var2": 22, "var3": 10 },
    #    "3.3.3.3": { "var1": 13, "var2": 23, "var3": 11 },
    #    "__PATH__": csvFilePath,
    #    "__INDEX__": "ip",
    # }
    # With lookup="1.1.1.1" returns csvVarDict:
    # {
    #    "1.1.1.1": { "var1": 11, "var2": 21, "var3": 10 },
    #    "__PATH__": csvFilePath,
    #    "__INDEX__": "ip",
    #    "__LOOKUP__": "1.1.1.1",
    # }
    # Example2 CSV:
    #    ip:var3, var1, var2, var3
    #    1.1.1.1, 11,   21,   10
    #    2.2.2.2, 12,   22,   10
    #    3.3.3.3, 13,   23,   11
    # With lookup="1.1.1.1" returns csvVarDict and also peer which has same value in var3:
    # {
    #    "1.1.1.1": { "var1": 11, "var2": 21, "var3": 10 },
    #    "2.2.2.2": { "var1": 12, "var2": 22, "var3": 10 },
    #    "__PATH__": csvFilePath,
    #    "__INDEX__": "ip",
    #    "__LOOKUP__": "1.1.1.1",
    #    "__PEER__": "2.2.2.2",
    # }

    # First check existence of the input csv file
    if not os.path.exists(csvFilePath):
        exitError("readCsvToDict: CSV file {} not found!".format(csvFilePath))
    # Read in the CSV file
    csvVarDict = {}
    with io.open(csvFilePath, mode='r', encoding='utf-8-sig') as csv_file:
        csv_reader = list(csv.reader(csv_file, delimiter=delimiter))
        firstRow = True
        for row in csv_reader:
            if len(row) > 0: # Skip empty lines
                if firstRow:
                    indexPeerList = re.sub(r'^\\ufeff', '', row.pop(0)).split(":", 2)
                    indexKey = indexPeerList[0]
                    peerVar = indexPeerList[1] if len(indexPeerList) == 2 else None
                    debug("readCsvToDict() indexKey = {}, peerVar = {}".format(indexKey, peerVar))
                    valueKeys = map(str.strip, row)
                    firstRow = False
                else:
                    rowcopy = list(row)
                    key = rowcopy.pop(0)
                    if not lookup or key == lookup:
                        while len(rowcopy) < len(valueKeys): # In case CSV row is missing last values
                            rowcopy.append('') # Add empty values so that we get all keys in the zip below
                        csvVarDict[key] = dict(zip(valueKeys, [re.sub(r'^"|"$', '', x.strip()) for x in rowcopy])) # Remove double quotes if these were used
                        if lookup:
                            csvVarDict['__LOOKUP__'] = key

        if firstRow:
            exitError("readCsvToDict: CSV file {} seems to be empty!".format(csvFilePath))

        if lookup and peerVar and lookup in csvVarDict and csvVarDict[lookup][peerVar]:
            # For also returning the peer entry which has same value in peerVar, we re-parse the CSV data a 2nd time
            firstRow = True
            for row in csv_reader:
                if len(row) > 0: # Skip empty lines
                    if firstRow:
                        firstRow = False
                    else:
                        rowcopy = list(row)
                        key = rowcopy.pop(0)
                        if key == lookup:
                            continue
                        while len(rowcopy) < len(valueKeys): # In case CSV row is missing last values
                            rowcopy.append('') # Add empty values so that we get all keys in the zip below
                        rowDict = dict(zip(valueKeys, [re.sub(r'^"|"$', '', x.strip()) for x in rowcopy])) # Remove double quotes if these were used
                        if rowDict[peerVar] == csvVarDict[lookup][peerVar]:
                            if '__PEER__' in csvVarDict:
                                exitError("readCsvToDict: CSV file {} intended to have unique peer for variable {}, but 3 found: {}, {}, {}".format(csvFilePath, peerVar, csvVarDict['__LOOKUP__'], csvVarDict['__PEER__'], key))
                            csvVarDict[key] = rowDict
                            csvVarDict['__PEER__'] = key

    csvVarDict['__INDEX__'] = indexKey
    csvVarDict['__PATH__'] = csvFilePath
    debug("readCsvToDict() csvVarDict =\n{}".format(json.dumps(csvVarDict, indent=4, sort_keys=True)))
    return csvVarDict

def csvVarLookup(inputStr, csvVarDict, lookup): # v11 - Replaces embedded $<csv-variables> or $(csv-variables) in the input string
    csvVarsUsed = {x.group(1):1 for x in list(re.finditer(r'\$<((?:peer:)?[\w -]+)>', inputStr)) + list(re.finditer(r'\$\(((?:peer:)?[\w -]+)\)', inputStr))}
    outputStr = inputStr
    if csvVarsUsed:
        debug("csvVarLookup csvVarsUsed = {}".format(csvVarsUsed))
        peerVarList = [x for x in csvVarsUsed if re.match(r'peer:', x)]
        if peerVarList and '__PEER__' not in csvVarDict:
            if '__PATH__' in csvVarDict:
                exitError("csvVarLookup for {}: the following peer variables are used but no peer node found in CSV file {}:\n{}".format(lookup, csvVarDict['__PATH__'], peerVarList))
            else:
                exitError("csvVarLookup for {}: the following peer variables are used but no peer node found in database data:\n{}".format(lookup, peerVarList))
        missingVarList = [x for x in csvVarsUsed if not re.match(r'peer:', x) and (lookup not in csvVarDict or x not in csvVarDict[lookup])]
        debug("csvVarLookup missingVarList = {}".format(missingVarList))
        if missingVarList:
            if csvVarDict:
                if '__PATH__' in csvVarDict:
                    exitError("csvVarLookup for {}: the following variables were not found in the CSV file {}:\n{}".format(lookup, csvVarDict['__PATH__'], missingVarList))
                else:
                    exitError("csvVarLookup for {}: the following variables were not found in database data:\n{}".format(lookup, missingVarList))
            else:
                exitError("csvVarLookup for {}: no CSV file provided but the following variables were found requiring CSV lookup:\n{}".format(lookup, missingVarList))
        for csvVar in csvVarsUsed:
            if re.match(r'peer:', csvVar):
                outputStr = re.sub(r'(?:\$<' + csvVar + '>|\$\(' + csvVar + '\))', csvVarDict[csvVarDict['__PEER__']][csvVar.split(":")[1]], outputStr)
            else:
                outputStr = re.sub(r'(?:\$<' + csvVar + '>|\$\(' + csvVar + '\))', csvVarDict[lookup][csvVar], outputStr)
        if "\n" in inputStr:
            debug("csvVarLookup input: {}\n{}\n".format(type(inputStr), inputStr))
            debug("csvVarLookup output: {}\n{}\n".format(type(outputStr), outputStr))
        else:
            debug("csvVarLookup {} {} =  {} {}".format(type(inputStr), inputStr, type(outputStr), outputStr))
    return outputStr
