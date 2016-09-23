#!/usr/bin/python
'''
stgnome.py - GitHub Named Organization Member Enforcer
Scans the list of members in a GitHub organization to find and notify those
accounts whose profile does not include a full name.

Usage: stgnome.py org={organization} at={access token}
'''


# ----- Imports -----
import os
import sys
import datetime
import requests
import boto3


# ----- Constants -----
g_sBanner = """
GitHub Named Organization Member Enforcer (GNOME)
    Find and notify members whose profiles are incomplete.
"""

g_sUsage = """    Usage: stgnome.py org={organization} at={access token} bucket={S3 bucket} 
        [help list all]
""" 

g_sHelp = """
    Required Arguments
        org=<name>        GitHub organization name
        at=<token>        GitHub personal access token

    Optional Arguments
        bucket=<name>     Specify an S3 bucket (no upload if missing)
        mail              Email a notice to users with profile problems
        help              Print this information
        all               List all organization members 
        list              List members with profile problems
"""


# ----- Globals -----
g_sAccessToken = None
g_aArgs = {}											# Dict of command line arguments
g_aNotify = []											# Array of users to be notified
g_oS3 = None											# Master S3 API object
g_oS3Bucket = None										# S3 bucket API object


# ----- Utility Functions -----

def reportHaltingError(sErrorMsg, bUsage=False):
    if bUsage:											# If the usage flag is set ...
        print g_sUsage									# ... print the usage message
    print "\tError: %s\n" % sErrorMsg					# Report the error
    sys.exit()											# Always exit


def getCommandLineArgs():
    for arg in sys.argv:
        if '=' in arg:									# Handle structured arguments
            key, val = arg.split('=', 1)				# Split on the '=' character
            g_aArgs[key.lower()] = val					# Assign the value to the key in the argument dict
        else:											# Handle keyword (flag) arguments
            argl = arg.lower()							# Force the argument to lowercase	
            if argl == 'help':
                print g_sUsage + g_sHelp				# Print the help information
                sys.exit()								# Special case: exit after displaying information 
            elif argl == 'list':
                g_aArgs['list'] = True 					# Keyword arguments are simply tested for existence
            elif argl == 'all':
                g_aArgs['all'] = True  					# Keyword arguments are simply tested for existence
            elif argl == 'mail':
                g_aArgs['mail'] = True  				# Keyword arguments are simply tested for existence


# ----- Console Reporting Functions -----

def listPrepare():
    if g_aArgs.get('list', None):						# Header for the users with profile problems list
        print '    Members with Incomplete Profiles (login, email)'
        print '    -----------------------------------------------'
    elif g_aArgs.get('all', None):						# Header for the organization member list
        print '    Organization Members (login, name, email)'
        print '    -----------------------------------------'


def listProcess(oUser):
    if g_aArgs.get('list', None):						# Row for the users with profile problems list
        print '    {0:20s}{1}'.format(oUser['login'], oUser['name'], oUser['email'])
    elif g_aArgs.get('all', None):						# Row for the organization member list
        print '    {0:20s}{1:20s}{2}'.format(oUser['login'], oUser['name'], oUser['email'])


def listFinalize():
    if g_aArgs.get('list', None) or g_aArgs.get('all', None):
        print ""										# Echo a blank line at the end of the list


# ----- GitHub Request Functions -----

def handleHTTPResultCode(oResponse):
    if oResponse.status_code == 200:
        return
    else:
        oResponse.raise_for_staus()						# TODO: Handle GitHub redirects not handled by response module


def generateRequestURL(sFormat, sSpecialization):
    sCMDPath = sFormat % (sSpecialization)				# Assemble the GitHub API command
    return "https://api.github.com/%s?access_token=%s" % (sCMDPath, g_aArgs.get('at', None)) # Assemble the request URL


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


# ----- Notification Functions -----

def handleNotifications(sLogin, sEMail):
    if not g_aArgs.get('mail', None):					# If the mail flag argument has NOT been set ...
        return											# ... return immediately
    with open('mail.tmp', 'w') as oTempFile:			# Write the email message to a temporary file
        oTempFile.write("Subject: Please Update Your GitHub Profile\r\n\r\nDear %s,\r\n\r\nThanks for joining our us at %s.\r\n\r\nWe noticed you haven't completed your GitHub profile.\r\nPlease go to https://github.com/settings/profile and enter at least your name.\r\n\r\nThanks for working with us.\r\n\r\n\r\nGNOME-bot" % (sLogin, g_aArgs.get('org', None)))
    os.system("cat mail.tmp | msmtp -a default " + sEMail) # Invoke the host mail system
    os.remove('mail.tmp')							 	# Clean up the temporary file
    

# ----- Main -----
if __name__ == "__main__":
    print g_sBanner										# Print the application banner
    
    # ----- Handle command-line arguments -----
    getCommandLineArgs()								# Process command line arguments
    if not g_aArgs.get('org', None):					# Validate the require 'org' argument
        reportHaltingError('Missing GitHub organization', True)
    if not g_aArgs.get('at', None):						# Validate the required 'at' argument
        reportHaltingError('Missing authentication token', True)
    if g_aArgs.get('bucket', None):						# Set the global bucket
        g_oS3 = boto3.resource('s3')					# Initialize the S3 master object only if we have a bucket argument
        g_oS3Bucket = g_oS3.Bucket(g_aArgs.get('bucket', None)) # Initialize the S3 bucke object only if we have a bucket argument

    # ----- Get Organization Membership Information -----
    listPrepare()										# Print optional list header
    requestGHMembers()									# Get membership info
    listFinalize()										# Print optional list footer

    # ----- Handle notifications for users missing profile information -----
    if len(g_aNotify) > 0:								# Determine whether there are users to notify
    	sNotifyCSV = ""									# Initialize the CSV file accumulation buffer
    	
    	# ----- Report notifications -----
        print '    Notifications'						# Print the notification header
        print '    -------------'
        for oUser in g_aNotify:
            print "    Notifying %s at %s" % (oUser['login'], oUser['email'])
            if oUser['email']:							# Validate the email address
                handleNotifications(oUser['login'], oUser['email'])
            if g_oS3Bucket:								# Accumlate data for the upload list if the S3 bucket was specified
                sNotifyCSV += "\"%s\",\"%s\"\n" % (oUser['login'], oUser['email'])
        
        # ----- Upload the notification list to S3 -----
        if g_oS3Bucket:									# Upload a file if the S3 bucket name was specified 
            oDTNow = datetime.datetime.now()			# Get the current datetime
            sKey = 'stgnome/pygnome' + oDTNow.strftime("%Y%m%d%H%M%S") + '.out' # Assemble the S3 key (path + filename)
            g_oS3Bucket.put_object(Key=sKey, Body=sNotifyCSV) # Upload the CSV data to an S3 file
    else:
        print "    No users found with profile issues."	# Report that there are no users to notify

    # ----- Finish -----
    print "\nNotified %d users\n" % (len(g_aNotify))

