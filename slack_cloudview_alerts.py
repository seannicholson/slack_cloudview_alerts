#
# Author: Sean Nicholson
# Purpose: Query Qualys API for list of CSA Failures by Cloud Account then post
#          report to Slack channel provided in CSV, Report will list control failures
#          and a list of resources per control
#
#----------------------------------------------------------
#  Script logic flow
#  1 - process a CSV of account info (CSV columns name,accountId,slackChannel,webHook).
#  2 - run the associated connectors
#  3 - pull list of CSA evaluations by account
#  4 - iterate list of evaluations and retrieve resources for control failures
#  5 - post findings to the designated slack channel
#----------------------------------------------------------
# Script Input parameters:
# --report allAccounts
# --report BU
# --report accountId
#----------------------------------------------------------
# version: 1.0.0
# date: 8.27.2019
#----------------------------------------------------------

import sys, requests, os, time, csv, getopt, logging, yaml, json, base64
#from slackclient import SlackClient
import logging.config


def setup_logging(default_path='./config/logging.yml',default_level=logging.INFO,env_key='LOG_CFG'):
    """Setup logging configuration"""
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)



def config():
    with open('./config/config.yml', 'r') as config_settings:
        config_info = yaml.load(config_settings)
        accountInfoCSV = str(config_info['defaults']['accountMap']).rstrip()
        URL = str(config_info['defaults']['apiURL']).rstrip()
        if URL == '' or accountInfoCSV == '':
            print "Config information in ./config.yml not configured correctly. Exiting..."
            sys.exit(1)
    return accountInfoCSV, URL


def post_to_slack(scope):
    accountInfoCSV, URL = config()
    username = os.environ["QUALYS_API_USERNAME"]
    password = base64.b64decode(os.environ["QUALYS_API_PASSWORD"])
    usrPass = str(username)+':'+str(password)
    b64Val = base64.b64encode(usrPass)
    headers = {
        'Accept': 'application/json',
        'content-type': 'application/json',
        'Authorization': "Basic %s" % b64Val
    }

    with open(accountInfoCSV,mode='r') as csv_file:
        accountInfo = csv.DictReader(csv_file)
            #print "{0}\n".format(json.dumps(row))
        if scope == "AllAccounts":
            for row in accountInfo:
                cloudviewReport(row['cloud'],row['accountId'], row['webHook'], URL, headers)
        else:
            for row in accountInfo:
                if row['accountId'] == scope:
                    cloudviewReport(row['cloud'],row['accountId'], row['webHook'], URL, headers)
                    break
                elif row['BU'] == scope:
                    cloudviewReport(row['cloud'],row['accountId'], row['webHook'], URL, headers)




def cloudviewReport(cloud, accountID, webhook, URL, headers):
    rURL = URL + "/cloudview-api/rest/v1/" + str(cloud) + "/evaluations/" + str(accountID) + "?evaluatedOn:now-8h...now-1s"
    rdata = requests.get(rURL, headers=headers)
    logger.info("ConnectorID %s - run status code %s", str(accountID), rdata.status_code)
    controlFailures = []
    controlText = {}
    slackData = {}
    controlList = json.loads(rdata.text)
    logger.debug("Length of control list content {}".format(len(controlList['content'])))
    for control in controlList['content']:
        controlText['text'] = ''
        if control['failedResources'] > 0:

            rURL2 = URL + "/cloudview-api/rest/v1/" + str(cloud) + "/evaluations/" + str(accountID) + "/resources/" + str(control['controlId']) + "?evaluatedOn:now-8h...now-1s&pageNo=0&pageSize=50"
            rdata2 = requests.get(rURL2, headers=headers)
            #print rdata2.status_code
            failedResources = []
            pageCount = 0
            resourceList = json.loads(rdata2.text)
            logger.info("Resource Details Control ID {0} for {1} Failures".format(str(control['controlId']), str(control['failedResources'])))
            while pageCount < resourceList['totalPages']:
                if pageCount == 0:
                    for resource in resourceList['content']:
                        if resource['result'] == "FAIL":
                            failedResources.append(str(resource['resourceId']))
                    pageCount += 1
                else:
                    rURL3 = URL + "/cloudview-api/rest/v1/" + str(cloud) + "/evaluations/" + str(accountID) + "/resources/" + str(control['controlId']) + "?evaluatedOn:now-8h...now-1s&pageNo=" + str(pageCount) +"&pageSize=50"
                    rdata3 = requests.get(rURL3, headers=headers)
                    for resource in resourceList['content']:
                        if resource['result'] == "FAIL":
                            failedResources.append(resource['resourceId'])
                    pageCount += 1


            controlText['text'] = "Failed Control CID {0}, Control Name: {1}, Failed Resources {2}\n Failed Resources: \n {3}".format(control['controlId'],control['controlName'], str(control['failedResources']), str(failedResources))
            #print controlText['text']
            controlFailures.append(dict(controlText))

    slackData['attachments'] = controlFailures
    logger.debug(slackData['attachments'])
    #sc.api_call("chat.postMessage",channel="#cloudview-alerts",text="Test test test :tada:")
    rdata3 = requests.post(webhook,json={"text": "CloudView CSA Results for {0}".format(str(accountID)),"attachments":slackData['attachments']}, headers={'Content-Type': 'application/json'})
    logger.debug("Slack post status code %s", str(rdata3.status_code))
    logger.debug("Slack response %s", rdata3.text)


def main(argv):
    try:
        opts, args = getopt.getopt(argv,"hr:",["report"])
    except getopt.GetoptError:
        print 'python slack_cloudview_alerts.py -r <scanTarget>, run python slack_cloudview_alerts.py -h '
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h','--help'):
            print 'Run report for all accounts: python slack_cloudview_alerts.py -r allAccounts or python slack_cloudview_alerts.py --report allAccounts'
            print 'Run report for a BU: python slack_cloudview_alerts.py -r <BUname> or python slack_cloudview_alerts.py --report <BUname>'
            print 'Run report for a cloud account: python slack_cloudview_alerts.py -r <accountId> or python slack_cloudview_alerts.py --report <accountId>'
            sys.exit()
        elif opt in ('-r','--report'):
            scanTarget = arg
            post_to_slack(scanTarget)
            #time.sleep(60)

        #elif opt in ('-sa','--scanAccount'):
        #    scanaccount = arg
        #    run_connectors(scanaccount)



if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger(__name__)
    main(sys.argv[1:])
