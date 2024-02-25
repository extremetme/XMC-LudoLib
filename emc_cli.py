# Simulates the emc_cli module present on an XMC, for testing offline

import re
import sys
import json

Debug  = 1
Prompt = 'Prompt#'

class send(object):

    def __init__(self, cmd, promptWait=True):
        self.output = None
        self.error = None
        self.success = False
        try:
            emc_cliDb = json.load(open('emc_cli.json'))
        except ValueError as detail:
            print "ValueError:", detail
            print "Unable to read emc_cli.json file!"
            sys.exit(1)
        cmdDb = None
        if cmd in emc_cliDb: # Clean match
            cmdDb = cmd
        else:
            for c in emc_cliDb.keys():
                if c and re.match(c, cmd): # Regex match
                    cmdDb = c
                    break
        if cmdDb:
            self.output = self.error = ''
            self.output += cmd + "\n" + emc_cliDb.get(cmdDb).get('output') + Prompt
            self.error += emc_cliDb.get(cmdDb).get('error')
            self.success = True
        elif not re.match('^show ', cmd):
            self.error = ''
            self.output = Prompt
            self.success = True
        if not self.success:
            raise RuntimeError("Error, no such command '" + cmd + "' in emc_cli.json!")
        if Debug:
            print "EMC_CLI> {}".format(cmd)
            if cmdDb:
                print self.output

    def isSuccess(self):
        return self.success

    def getError(self):
        return self.error

    def getOutput(self):
        return self.output


class setIpAddress(object):

    def __init__(self, ipaddr):
        self.ipaddr = ipaddr


class close:
    pass
