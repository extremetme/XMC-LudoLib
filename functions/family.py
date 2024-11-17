#
# Family functions
# family.py v3
#
Family = None # This needs to get set by setFamily()
FamilyChildren = { # Children will be rolled into parent family for these scripts
    'Extreme Access Series' : 'VSP Series',
    'Unified Switching VOSS': 'VSP Series',
    'Unified Switching EXOS': 'Summit Series',
    'Universal Platform VOSS': 'VSP Series',
    'Universal Platform EXOS': 'Summit Series',
    'Universal Platform Fabric Engine': 'VSP Series',
    'Universal Platform Switch Engine': 'Summit Series',
    'ISW-24W-4X': 'ISW-Series-Marvell',
}

def setFamily(cliDict={}, family=None): # v3 - Set global Family variable; automatically handles family children, as far as this script is concerned
    global Family
    if family:
        Family = family
    elif emc_vars["family"] in FamilyChildren:
        Family = FamilyChildren[emc_vars["family"]]
    elif emc_vars["deviceType"] in FamilyChildren:
        Family = FamilyChildren[emc_vars["deviceType"]]
    else:
        Family = emc_vars["family"]
    print "Using family type '{}' for this script".format(Family)
    if cliDict and Family not in cliDict:
        exitError('This scripts only supports family types: {}'.format(", ".join(list(cliDict.keys()))))
    return Family
