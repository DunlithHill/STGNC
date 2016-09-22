#!/usr/bin/python
'''
stgnome.py - GitHub Named Organization Member Enforcer
Scans the list of members in a GitHub organization to find and notify those
accounts whose profile does not include a full name.

Usage: stgnome.py org={organization} at={access token}
'''


# ----- Imports -----
import sys
import requests


# ----- Constants -----
g_sBanner = """
GitHub Named Organization Member Enforcer (GNOME)
    Find and notify members whose profiles are incomplete.
"""

g_sUsage = """    Usage: stgnome.py org={organization} at={access token} [help list all]
""" 

g_sHelp = """
    Required Arguments
        org=<name>        GitHub organization name
        at=<token>        GitHub personal access token

    Optional Arguments
        help              Print this information
        all               List all organization members 
        list              List members with profile problems
"""


# ----- Globals -----
g_sAccessToken = None
g_aArgs = {}
g_aNotify = []


# ----- Utility Functions -----

def reportHaltingError(sErrorMsg, bUsage=False):
    if bUsage:
        print g_sUsage
    print "\tError: %s\n" % sErrorMsg
    sys.exit()


# Extract "key=value" args to a dictionary for easy lookup. 
def getCommandLineArgs():
    for arg in sys.argv:
        if '=' in arg:
            key, val = arg.split('=', 1)
            g_aArgs[key.lower()] = val
        else:
            argl = arg.lower()
            if argl == 'help':
                print g_sUsage + g_sHelp
                sys.exit()
            elif argl == 'list':
                g_aArgs['list'] = True 
            elif argl == 'all':
                g_aArgs['all'] = True 


# ----- Console Reporting Functions -----

def listPrepare():
    if g_aArgs.get('list', None):
        print '    Members with Incomplete Profiles (login, email)'
        print '    -----------------------------------------------'
    elif g_aArgs.get('all', None):
        print '    Organization Members (login, name, email)'
        print '    -----------------------------------------'


def listProcess(oUser):
    if g_aArgs.get('list', None):
        print '    {0:20s}{1}'.format(oUser['login'], oUser['name'], oUser['email'])
    elif g_aArgs.get('all', None):
        print '    {0:20s}{1:20s}{2}'.format(oUser['login'], oUser['name'], oUser['email'])


def listFinalize():
    if g_aArgs.get('list', None) or g_aArgs.get('all', None):
        print ""										# Echo a blank line at the end of the list


# ----- GitHub Request Functions -----

def handleHTTPResultCode(oResponse):
    if oResponse.status_code == 200:
        return
    else:
        oResponse.raise_for_staus()
        # TODO: Handle GitHub redirects not handled by response module


def generateRequestURL(sFormat, sSpecialization):
    sCMDPath = sFormat % (sSpecialization)
    return "https://api.github.com/%s?access_token=%s" % (sCMDPath, g_aArgs.get('at', None))


def requestGHUser(sLogin):
    sURL = generateRequestURL('users/%s', sLogin)		# Generate the user-specific URL
    oResponse = requests.get(sURL)						# Call the GitHub API
    handleHTTPResultCode(oResponse)						# Handle non-200 HTTP response codes
    oUser = oResponse.json()							# Get the user information
    listProcess(oUser)									# Process optional listing directives
    if not oUser['name']:								# For all users without a full name
        g_aNotify.append({'login':oUser['login'], 'email':oUser['email']}) # Collect their login and email

    
def requestGHMembers():
    sURL = generateRequestURL('orgs/%s/members', g_aArgs.get('org', None)) # Generate the organization-specific URL
    oResponse = requests.get(sURL)						# Call the GitHub API
    handleHTTPResultCode(oResponse)						# Handle non-200 HTTP response codes
    for member in oResponse.json():						# Iterate the member list
        requestGHUser(member['login'])					# Request user information for each member
    print ''											# Echo a blank line


# ----- Main -----
if __name__ == "__main__":
    print g_sBanner										# Print the application banner
    
    # ----- Handle command-line arguments -----
    getCommandLineArgs()								# Process command line arguments
    if not g_aArgs.get('org', None):					# Validate the require 'org' argument
        reportHaltingError('Missing GitHub organization', True)
    if not g_aArgs.get('at', None):						# Validate the required 'at' argument
        reportHaltingError('Missing authentication token', True)

    # ----- Get Organization Membership Information -----
    listPrepare()										# Print optional list header
    requestGHMembers()									# Get membership info
    listFinalize()										# Print optional list footer

    # ----- Handle notifications for users missing profile information -----
    if len(g_aNotify) > 0:
        print '    Notifications'
        print '    -------------'
        for oUser in g_aNotify:
            print "    Notifying %s at %s" % (oUser['login'], oUser['email'])
        print ''

