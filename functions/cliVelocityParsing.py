#
# Parsing of config template for #if/#elseif/#else/#end velocity type statements & #eval
# cliVelocityParsing.py v6
#
import re
RegexIfElse = re.compile('^#(if|elseif|else|end) *(?:\((.+?)\) *$|(\S+))?')
RegexEval = re.compile('#eval *\((.+)\)')

def preParseIfElseBlocks(config): # v4 - Pre-parses config for embedded ${}/$<>/$()/$UD1-4 variables used on #if/#elseif/#else/#end/#eval velocity type statements
    # Since the #if/#elseif conditionals will be eval()-ed, any variable replacement will need to be quoted for a string

    def preParseEvalString(match):
        return re.sub(r'(\$\{.+?\}|\$<.+?>|\$\(.+?\)|\$UD\d)', r'"\1"', match.group(0))

    parsedConfig = []
    for line in config.splitlines():
        regexMatch = RegexIfElse.match(line)
        if regexMatch: #if/#elseif/#else/#end
            line = re.sub(r'(\$\{.+?\}|\$<.+?>|\$\(.+?\)|\$UD\d)', r'"\1"', line)
        else: #eval
            line = re.sub(RegexEval, preParseEvalString, line)
        parsedConfig.append(line)
    finalConfig = "\n".join(parsedConfig)
    debug("preParseIfElseBlocks finalConfig:\n{}\n".format(finalConfig))
    return finalConfig

def parseIfElseBlocks(config): # v3 - Parses config for embedded #if/#elseif/#else/#end velocity type statements

    def replaceEvalString(match):
        return str(eval(match.group(1), {}))

    parsedConfig = []
    includeLines = True
    ifMatch = False
    expectedStatements = []
    lineNumber = 0
    for line in config.splitlines():
        lineNumber += 1
        regexMatch = RegexIfElse.match(line)
        if regexMatch:
            statement = regexMatch.group(1).lower()
            evalString = regexMatch.group(2)
            invalidArg = regexMatch.group(3)
            if invalidArg:
                exitError("Error parsing config file line number {}: invalid syntax for statement '#{}'".format(lineNumber, statement))
            try:
                condition = bool(eval(evalString, {})) if evalString else False
            except Exception as err:
                exitError("Error parsing config file line number {}: cannot Python eval() conditional: '({})'\nError: {}".format(lineNumber, evalString, err))
            if statement == "if":
                if condition == True:
                    ifMatch = True
                else:
                    includeLines = False
                expectedStatements = ["elseif", "else", "end"]
                continue
            elif statement not in expectedStatements:
                exitError("Error parsing config file line number {}: found unexpected statement '#{}'".format(lineNumber, statement))
            elif statement == "elseif":
                if ifMatch == False and condition == True:
                    includeLines = True
                    ifMatch = True
                else:
                    includeLines = False
                continue
            elif statement == "else":
                if evalString:
                    exitError("Error parsing config file line number {}: statement '#{}' should have no arguments".format(lineNumber, statement))
                includeLines = True if ifMatch == False else False
                expectedStatements = ["end"]
                continue
            elif statement == "end":
                if evalString:
                    exitError("Error parsing config file line number {}: statement '#{}' should have no arguments".format(lineNumber, statement))
                includeLines = True
                expectedStatements = []
                continue
            else:
                exitError("Error parsing config file line number {}: found unsupported statement '#{}'".format(lineNumber, statement))
        if includeLines:
            line = re.sub(RegexEval, replaceEvalString, line) #eval
            parsedConfig.append(line)
    if expectedStatements:
        exitError("Error parsing config file line number {}: never found expected statement '#{}'".format(lineNumber, expectedStatements[0]))
    finalConfig = "\n".join(parsedConfig)
    debug("parseIfElseBlocks finalConfig:\n{}\n".format(finalConfig))
    return finalConfig
