#
# Parsing of config template for #if/#elseif/#else/#end velocity type statements & #eval/#last
# cliVelocityParsing.py v9
#
import re
RegexEmbeddedIfElse  = re.compile('^[ \t]*#(if|elseif|else|end) *(?:\((.+?)\) *$|(\S+))?')
RegexEmbeddedEval    = re.compile('#eval *\((.+)\)')
RegexEmbeddedEvalSet = re.compile('^[ \t]*#eval +([\w -]+?) *= *\((.+)\) *$')
RegexEmbeddedEvalVar = re.compile('\$\[([\w -]+)\]')
RegexEmbeddedLast    = re.compile('[ \t]*#last *$')


def preParseIfElseBlocks(config): # v5 - Pre-parses config for embedded ${}/$<>/$()/$[]/$UD1-4 variables used on #if/#elseif/#else/#end/#eval velocity type statements
    # Since the #if/#elseif conditionals and #eval command will be eval()-ed, any variable replacement will need to be quoted for a string

    def preParseEvalString(match):
        return re.sub(r'(\$\{.+?\}|\$<.+?>|\$\(.+?\)|\$\[.+?\]|\$UD\d)', r'"\1"', match.group(0))

    parsedConfig = []
    for line in config.splitlines():
        regexMatch = RegexEmbeddedIfElse.match(line)
        if regexMatch: #if/#elseif/#else/#end
            line = re.sub(r'(\$\{.+?\}|\$<.+?>|\$\(.+?\)|\$\[.+?\]|\$UD\d)', r'"\1"', line)
        else: #eval
            line = re.sub(RegexEmbeddedEval, preParseEvalString, line)
            line = re.sub(RegexEmbeddedEvalSet, preParseEvalString, line)
        parsedConfig.append(line)
    finalConfig = "\n".join(parsedConfig)
    debug("preParseIfElseBlocks finalConfig:\n{}\n".format(finalConfig))
    return finalConfig

def parseIfElseBlocks(config): # v6 - Parses config for embedded #if/#elseif/#else/#end velocity type statements

    def replaceEvalString(match):
        try:
            replaceStr = str(eval(match.group(1), {}))
        except Exception as err:
            exitError("Error parsing config file line number {}: cannot Python eval({})\nError: {}".format(lineNumber, match.group(1), err))
        debug("replaceEvalString eval({}) = {}".format(match.group(1), replaceStr))
        return replaceStr

    def varSetEvalString(match):
        evalVarDict[match.group(1)] = str(eval(match.group(2), {}))
        debug("varSetEvalString evalVarDict = {}".format(evalVarDict))
        return ''

    def evalVarReplace(match):
        if match.group(1) not in evalVarDict:
            exitError("evalVarReplace: the following eval variable in line {} was not found: $[{}]".format(lineNumber, match.group(1)))
        return evalVarDict[match.group(1)]

    evalVarDict = {}
    parsedConfig = []
    ifDictStack = []
    ifDict = {
        'includeLines'       : True,  # Only if true do we append config lines
        'ifMatch'            : False, # Keeps track if a match has occurred
        'expectedStatements' : [],    # Expected next if/elseif/else/end statements
        'active'             : True,  # Will be False for nexted if-end blocks in sections being skipped
    }
    lastFlag = False
    waitForPromptLastLine = True
    lineNumber = 0
    for line in config.splitlines():
        lineNumber += 1
        regexMatch = RegexEmbeddedIfElse.match(line)
        if regexMatch:
            statement = regexMatch.group(1).lower()
            evalString = regexMatch.group(2)
            invalidArg = regexMatch.group(3)
            if invalidArg:
                exitError("Error parsing config file line number {}: invalid syntax for statement '#{}'".format(lineNumber, statement))
            if evalString:
                evalString = re.sub(RegexEmbeddedEvalVar, evalVarReplace, evalString) # Replaces embedded $[<eval-variable>] in evalString
            try:
                condition = bool(eval(evalString, {})) if evalString else False
            except Exception as err:
                exitError("Error parsing config file line number {}: cannot Python eval({}) conditional\nError: {}".format(lineNumber, evalString, err))
            if statement == "if":
                if ifDict['expectedStatements']: # Nested IF block
                    ifDictStack.append(ifDict.copy())
                    ifDict['active'] = True if ifDict['includeLines'] else False
                ifDict['expectedStatements'] = ["elseif", "else", "end"]
                if ifDict['active']:
                    if condition == True:
                        ifDict['ifMatch'] = True
                        ifDict['includeLines'] = True
                    else:
                        ifDict['ifMatch'] = False
                        ifDict['includeLines'] = False
                    debug("parseIfElseBlocks line{} IF    : {}\neval({}) = {}\nnesting = {}, blockData = {}\n".format(lineNumber, line, evalString, condition, len(ifDictStack), ifDict))
                else:
                    debug("parseIfElseBlocks line{} IF    : {}\nnesting = {}, blockData = {}\n".format(lineNumber, line, len(ifDictStack), ifDict))
                continue
            elif statement not in ifDict['expectedStatements']:
                exitError("Error parsing config file line number {}: found unexpected statement '#{}'".format(lineNumber, statement))
            elif statement == "elseif":
                if ifDict['active']:
                    if ifDict['ifMatch'] == False and condition == True:
                        ifDict['ifMatch'] = True
                        ifDict['includeLines'] = True
                    else:
                        ifDict['includeLines'] = False
                    debug("parseIfElseBlocks line{} ELSEIF: {}\neval({}) = {}\nnesting = {}, blockData = {}\n".format(lineNumber, line, evalString, condition, len(ifDictStack), ifDict))
                else:
                    debug("parseIfElseBlocks line{} ELSEIF: {}\nnesting = {}, blockData = {}\n".format(lineNumber, line, len(ifDictStack), ifDict))
                continue
            elif statement == "else":
                if evalString:
                    exitError("Error parsing config file line number {}: statement '#{}' should have no arguments".format(lineNumber, statement))
                if ifDict['active']:
                    ifDict['includeLines'] = True if ifDict['ifMatch'] == False else False
                ifDict['expectedStatements'] = ["end"]
                debug("parseIfElseBlocks line{} ELSE  : {}\nnesting = {}, blockData = {}\n".format(lineNumber, line, len(ifDictStack), ifDict))
                continue
            elif statement == "end":
                if evalString:
                    exitError("Error parsing config file line number {}: statement '#{}' should have no arguments".format(lineNumber, statement))
                if ifDict['active']:
                    ifDict['includeLines'] = True
                ifDict['expectedStatements'] = []
                debug("parseIfElseBlocks line{} END   : {}\nnesting = {}, blockData = {}\n".format(lineNumber, line, len(ifDictStack), ifDict))
                if ifDictStack: # Nested IF block
                    ifDict = ifDictStack.pop()
                continue
            else:
                exitError("Error parsing config file line number {}: found unsupported statement '#{}'".format(lineNumber, statement))
        if ifDict['includeLines']:
            if not line: # Skip empty lines
                continue
            line = re.sub(RegexEmbeddedEvalVar, evalVarReplace, line) # Replaces embedded $[<eval-variable>] in line
            debug("parseIfElseBlocks line{} retaining: {}".format(lineNumber, line))
            if RegexEmbeddedLast.match(line):
                lastFlag = True
            else:
                line = re.sub(r'^\t+', '', line) # Remove tab indentation
                line = re.sub(RegexEmbeddedEval, replaceEvalString, line) #eval ()
                line = re.sub(RegexEmbeddedEvalSet, varSetEvalString, line) #eval var=()
                if line: #eval var=() will set the variable and obliterate the line
                    parsedConfig.append(line)
                    if lastFlag:
                        if re.match(r'#block execute', line) or not re.match(r'#', line):
                            waitForPromptLastLine = False
                        lastFlag = False
                    else:
                        waitForPromptLastLine = True
    if ifDict['expectedStatements']:
        exitError("Error parsing config file line number {}: never found expected statement '#{}'".format(lineNumber, ifDict['expectedStatements'][0]))
    finalConfig = "\n".join(parsedConfig)
    debug("parseIfElseBlocks finalConfig:\n{}\n".format(finalConfig))
    debug("parseIfElseBlocks waitForPromptLastLine = {}".format(waitForPromptLastLine))
    return finalConfig, waitForPromptLastLine
