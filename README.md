# STGNOME
(Skill Test) GitHub Named Organization Member Enforcer [20160922]

The GitHub Named Organization Member Enforcer (GNOME) retrieves the 
membership list from a GitHub organization and identifies those members 
whose profiles do not contain full names.

Following the introductory section and usage and installation 
documentation for each implementation of the tool, there is a 
discussion of security and authentication, and notes on coding
conventions.

## Architectural Context
The presumptive motivation for this tool is that we are hosting one
or more open source projects and we want our contributors to have at
least their full names in their profiles. Further, the project attracts 
enough new contributors on an on-going basis that we want to automate
this administrative review.

Taking that as given, it's still not clear which of several approaches
would be most expedient, so I've provided two: a Bash shell script
(which assumes a properly configued Linux server), and a Python 
program.

#### Bash Script
In all but the most wildly popular open-source projects, it's hard to 
imagine we would need to run the tool more than once a week. Given a
Linux server configured with an SMTP host like Postfix, the remaining
dependencies are either present in common Linux distros or are easily
installed. And if the third-party services (GitHub and AWS) were also
already set up, a developer familiar with Bash should be able to pull
the basic functionality (i.e., get the member list, check profiles,
and send notices) in less than a day.

#### Python
Bash scripts, however, are liable to be brittle. Moreover, if we wanted
to share a more polished version of the tool with the GitHub community,
we would be better served by an application.

## Limitations
The GitHub documentation for the API to get the information for a single
user [*GET /users/:username*] it states:

> Note: The returned email is the user's publicly visible email address (or null if the user has not specified a public email address in their profile). 

In other words, GitHub user email is not available via the API (and 
consequently there is no way to notify them) if the user has not made 
their email address public--something that seems likely if they have 
also not bothered to fill in their name.

## STGNOME - Bash
#### Usage
The Bash script (stgnome.sh) has two required and one optional positional
arguments.

    ./stgnome.sh {org} {token} ['list' | 'all']

Position | Argument | Description
---------|----------|------------
1 | {org} | (Required) The URL-friendly name of the GitHub organization
2 | {token} | (Required) Your personal access token as an organization administrator
3 | {cmd} | The optional commands, **list** and **all**, which list, respectively, users with missing profile information or all members on the console.

#### Dependencies and Installation Notes
* **Linux** (It might be interesting to see what can be done with the Linux subsystem in the Windows 10 Anniversary Update (1607).)
* **Bash 3.x+**
* **curl** - The workhorse for retrieving remote content via the command line,
* **jq** - A light-weight, flexible command-line JSON parser [*sudo apt-get install jq*].
* **pip** - The Python package installer (for the AWS CLI tools) [*sudo apt-get install python-pip*].
* **AWSCLI** - The Amazon Web Service Command Line Interface tools [*sudo pip install awscli --ignore-installed six*].
* **msmtp** - A small but powerful SMTP client. [*sudo apt-get install msmtp ca-certificates*]. (See [Stack Overflow](http://stackoverflow.com/questions/16756305/how-to-configure-msmtp-with-amazon-ses) for guidance on configuring msmtp to use AWS SES.)

The committed code has both email notification and the call to copy the list 
of uses to AWS S3 commented out. The last three dependencies can be ommitted 
to test the script's interactions wtih GitHub.

The S3 bucket name is declared on line 7 of the script. It should be changed 
if the S3 upload capabilites are enabled.

The list of users with profile issues is formatted as a simple CSV file with
the GitHub login in the first column and the email address in the second. 

The Bash script has no file system dependencies. I can be copied to and run
from any suitable directory.

## STGNOME - Python
#### Usage
The Python program (stgnome.py) has two required and one optional positional
arguments.

    ./stgnome.sh {org} {token} ['list' | 'all']

Position | Argument | Description
---------|----------|------------
1 | {org} | The URL-friendly name of the GitHub organization
2 | {token} | Your personal access token as an organization administrator
3 | {cmd} | The optional commands, **list** and **all**, which list, respectively, users with missing profile information or all members on the console.

