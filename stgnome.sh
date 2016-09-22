#! /usr/bin/env bash
# ----- Settings -----
IFS=$'\n'				# Set the internal field separator

# ----- Constants ----
LOGFILE="gnome$(date +%Y%m%d%H%M%S).out"
S3BUCKET="derenhansen.com.test"

# ----- Check the command line arguments -----
echo "usage: stgnome.sh {org} {access token} [list|all]"
ORG=$1					# Get the organization name
if [[ "${ORG}" == "" ]]; then echo "    Error: Missing organization"; echo ""; exit 1; fi
AT=$2					# Get the personal access token	
if [[ "${AT}" == "" ]]; then echo "    Error: Missing access token"; echo""; exit 1; fi
LIST=$3					# Set the optional list argument to true
echo ""					# echo a blank line

# ----- Print the optional list headers -----
if [[ ${LIST} == "all" ]]; then 
	printf '\tOrganization Members (Login, Name, Email)\n'
	printf '\t-----------------------------------------\n'
fi
if [[ ${LIST} == "list" ]]; then
	printf '\tMembers without Names (Login, Email)\n'
	printf '\t------------------------------------\n'
fi

# ----- Get the GitHub organization membership list -----
memlist=( $(curl -s "https://api.github.com/orgs/"${ORG}"/members?access_token="${AT} | jq -r '.[].login') )

# ----- For each member, get their name and email address from their GitHub profile -----
for mem in ${memlist[@]}; do 
	user=( $(curl -s "https://api.github.com/users/"${mem}"?access_token="${AT} | jq -r '.login, .name, .email') )

	# ----- Handle the optional member list -----
	if [[ ${LIST} == "all" ]]; then
		printf '\t%-20s%-20s%s\n' "${user[0]}" "${user[1]}" "${user[2]}"
	fi

	# ----- Check for members missing their full name -----
	if [ "${user[1]}" == "null" ]; then
		echo "\"${user[0]}\",\"${user[2]}\"" >> "${LOGFILE}"

		# ----- eMail a notice to the use with the incomplete profile -----
#		if [ "${user[2]}" != "null" ]; then
#			NOTICE="Subject: Please Update Your GitHub Profile\r\n\r\nDear "${user[0]}",\r\n\r\nThanks for joining our us at "${ORG}".\r\n\r\nWe noticed you haven't completed your GitHub profile.\r\nPlease go to https://github.com/settings/profile and enter at least your name.\r\n\r\nThanks for working with us.\r\n\r\n\r\nGNOME-bot"
#			echo -e ${NOTICE} | msmtp -a default ${user[2]}
#		fi

		# ----- Handle the optional missing name list -----
		if [[ ${LIST} == "list" ]]; then
			printf '\t%-20s%s\n' "${user[0]}" "${user[2]}"
		fi
	fi
done
echo ""					# echo a blank line

# ----- Upload the list of users with incomplete profiles to AWS S3 -----
#echo "Copying CSV list of users with incomplete profiles to  AWS S3"
#aws s3 cp "${LOGFILE}" s3://"${S3BUCKET}"/stgnome/"${LOGFILE}"
#echo ""					# echo a blank line

# ----- Cleanup -----
for file in ./*.out; do			# for each matching file
	echo "Cleanup: ${file}"		# report it was cleaned up
	rm  ${file}			# remove the file
done

echo ""					# echo a blank line
echo "STGNOME Finished\n"		# normal exit
