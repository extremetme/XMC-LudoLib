# Simulates the emc_nbi module present on an XMC, for testing offline

import sys
import json

Debug  = 1
Prompt = 'Prompt#'

def query(ignore):
	try:
		response = json.load(open('emc_nbi.json'))
		return response
	except ValueError as detail:
		print "ValueError:", detail
		print "Unable to read emc_nbi.json file!"
		sys.exit(1)

