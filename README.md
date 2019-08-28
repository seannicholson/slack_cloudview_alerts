# slack_cloudview_alerts

# License
THIS SCRIPT IS PROVIDED TO YOU "AS IS."  TO THE EXTENT PERMITTED BY LAW, QUALYS HEREBY DISCLAIMS ALL WARRANTIES AND LIABILITY FOR THE PROVISION OR USE OF THIS SCRIPT.  IN NO EVENT SHALL THESE SCRIPTS BE DEEMED TO BE CLOUD SERVICES AS PROVIDED BY QUALYS

# Summary
Python script for pulling CloudView CSA Report from Qualys API and send report of
control failures to a Slack Channel with list of resource IDs per failed control

To run the script you will need:

1. Credentials for the Qualys user name and password - stored in the form of environment variables

The Script is configured to read environmental variables for user name and password
> QUALYS_API_USERNAME stores the Qualys API User Name

> QUALYS_API_PASSWORD stores the base64 encoded password for Qualys API
to encode the password using base64 encoding execute the following command substituting the API Account Password for "APIpassword" - make sure the password is in '' or ""
export $QUALYS_API_PASSWORD = `echo -n "APIpassword" | base64`


2. Qualys CloudView API endpoint URL for your Qualys Platform

3. Config file accountMap  - Requirements defined below

# Prerequisites
This script is written in Python 2.7.
The script relies on the following Python modules to execute: sys, requests, datetime, os, time, csv, getopt, logging, yaml, json, base64, logging.config

For module missing warnings/errors use PIP to install modules
> for Linux

`pip install pyyaml`

> for Windows

`python -m pip install pyyaml`



# Parameters:

  apiURL:

    Default: Qualys API URL for CloudView API endpoint. See https://www.qualys.com/docs/qualys-cloud-view-user-guide.pdf page 27    

  accountMap:

    File location of the Cloud Account map. This provide the information for the script to send CloudView CSA Reports to the specified Slack Channel for each Cloud account. Default value is specified as "./cloud-accounts.csv"

    *CSV File Requirements*
    *CSV columns* - cloud,name,accountId,BU,slackChannel,webHook
    The script uses the columns cloud, accountId, and webHook by those column names. The other columns are not used in this version of the script. If the columns headers for *cloud, accountId, and webHook are not included in the CSV*, the script will *error* and not execute.

# Slack Requirements
Incoming webhook to receive the CloudView CSA Report
For information on setting up an App Incoming Webhook check the Slack knowledge base site - https://get.slack.help/hc/en-us/articles/115005265063-Incoming-WebHooks-for-Slack

# Running slack_cloudview_alerts.py
This script is written in Python 2.7. It requires a command line argument to run and can be executeed using the following command
    > python slack_cloudview_alerts.py -r scope

or

    > python slack_cloudview_alerts.py --report scope

scope - accepts one of three input types

AllAccount (case sensitive) - create report per account / slack channel defined in cloud_accounts.csv

BU - create report per account / slack channel  for the specified Business Unit defined in cloud_accounts.csv

Account - create a report for a single account ID specified in cloud_accounts.csv


# Logging
Logging configuration files is located in ./config/logging.yml. To change logging behavior, make changes in this file. For information on Python 2.7 logging visit https://docs.python.org/2/library/logging.html
Logging configuration
File Handler writes to ./log/cloudviewreports.log
Maximum Log size = 10 MB ( logging.yml line 18 - maxBytes: 10485760 # 10MB)
Backup file count = 5 (logging.yml line 19 - backupCount: 5)
Log Level = INFO (Change to WARNING or higher for production - logging.yml line 15 - level: INFO)
