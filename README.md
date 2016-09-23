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
1 | {org} | (Required) The URL-friendly name of the GitHub organization.
2 | {token} | (Required) Your GitHub **personal access token** (Your account should be an organization administrator).
3 | {cmd} | The optional commands, **list** and **all**, which list, respectively, users with missing profile information or all members o f the organization on the console.

#### Dependencies and Installation Notes
* **Linux** (It might be interesting to see what can be done with the Linux subsystem in the Windows 10 Anniversary Update (1607).)
* **Bash 3.x+**
* **curl** - The workhorse for retrieving remote content via the command line,
* **jq** - A light-weight, flexible command-line JSON parser [*sudo apt-get install jq*].
* **pip** - The Python package installer (for the AWS CLI tools) [*sudo apt-get install python-pip*].
* **AWSCLI** - The Amazon Web Service Command Line Interface tools [*sudo pip install awscli --ignore-installed six*].
* **msmtp** - A small but powerful SMTP client. [*sudo apt-get install msmtp ca-certificates*]. (See [Stack Overflow](http://stackoverflow.com/questions/16756305/how-to-configure-msmtp-with-amazon-ses) for guidance on configuring msmtp to use AWS SES.)

The committed Bash script has both email notification and the call to copy the 
list of users to AWS S3 commented out. If that code is commented out, the last 
three dependencies can be ommitted to test the script's interactions wtih GitHub.

The S3 bucket name is declared on line 7 of the script. It should be changed 
if the S3 upload capabilites are enabled.

The list of users with profile issues is formatted as a simple CSV file with
the GitHub login in the first column and the email address in the second. 

The Bash script has no file system dependencies. I can be copied to and run
from any suitable directory.

## STGNOME - Python
#### Usage
The Python program (stgnome.py) has two required and several optional arguments.

    python stgnome.py org={organization} at={access token} bucket={S3 bucket}[help list all mail]

Argument | Mode |Description
---------|------|------------
org={organization} | **Required** | The URL-friendly name of the GitHub organization.
at={access token} | **Required** | Your GitHub **personal access token** (Your account should be an organization administrator).
bucket={S3 bucket} | Optional | The name of the S3 bucket to which the CSV list of users with profile problems will be written.
mail | Optional | If specified, an email notice will be sent to each user with profile problems.
list | Optional | List only the users with missing profile information on the console.
all | Optional | List all members of the organization on the console.

Notes:
* Arguments may be specified in any order. 
* If the **bucket=** argument is omitted, no data will be written to S3.
* If the **mail** argument is omitted, no email notifications will be sent to users with profile problems.
* **list** is a subset of **all**. Specifying both arguments is equivalent to specifying **all** (that is, **list** is ignored).

#### Dependencies and Installation Notes
* **Python 2.7+** - The code was developed and tested on Python 2.7
* **pip** - The Python package installer [*sudo apt-get install python-pip*].
* **requests** module - [*pip install requests*]
* **boto3** module - The S3 Python API [*pip install boto3*]

This program uses system calls to interact with the host's SMTP client.
It assumes **msmtp** is available for that purpose. See the Bash script
dependencies for information on installing and configuring msmtp.

## Discussion
#### Approach
* The general approach was start with the simplest possible solution (hence the Bash script).
* Consistent with that approach, neither implementation makes any attempt to handle large datasets. That is, basic buffers and collections are assumed to have ample space for retreived data and that no GitHub responses would required handling paged data.
* While the Python implemenation has some generalization, the task was constrained enough that there was little scope for further generalization.
* While the Bash script is limited to Linux (and perhaps Windows 10) hosts, the Python code should run on multiple platforms. The biggest issue in the latter case would be the specifics of configuring and interacting with an SMTP client on each platform. 

#### Security 
Passing the GitHub personal access token as an argument is sufficient if the host system is secure 
(a questionable assumption). It would be more consistent with standard practice to store the token
as an environment variable (which would require an additional configuration step). We could also 
improve our security by storing the token in an encrypted file, accessed either directly (via the 
Python program) or indirectly (invoking a utility in the Bash script), so the token isn't available 
as plain text in the system. 

The AWS credentials are stored in the environment where they can be access by both applications and the
AWS CLI tools. Again, this assumes the host is secure.

Of course, if we want other users to be able to authorize the application to use their account, 
GitHub requires us to implement the [OAuth2 Protocol](https://developer.github.com/v3/oauth/). This 
requires registering the application with GitHub, and implementing a web protocol with a series of 
redirects.

## Coding Conventions
In brief:

* Vertical Whitespace - Use single blank lines to separate logical blocks of code within functions. Typically each such block will begin with a comment, indented to match the following block. Use two blank lines between functions to help visually separate them from one another.
* Horizontal Whitespace - Use whitespace within statements using the same style as normal English.
* Names - Use a single character type prefix for variable names (e.g., s = string, a=array, o=object; this is helpful in an untyped language like Python).
* Names and comments - Prefer full words over contractions
* Comments - Use vertically aligned (col 57) end-of-line comments to decribe structures and complex code.

