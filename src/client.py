import requests
import time
from lxml import etree
import sys

# need to get this from VM
server_ip = '37.209.208.186'
server_port = 80


manifesturl = 'https://cloudscraper-4d.s3-eu-west-1.amazonaws.com/ip-10-0-0-170-xvdamanifest.xml?Signature=e%2BXoVD%2BnikyiIO7k2nMi59IOuPs%3D&Expires=1442882306&AWSAccessKeyId=AKIAIY2X62QVIHOPEFEQ'




def post(payload):
    url = "http://%s:%d/" % (server_ip, server_port)

    r = requests.post(url, data = payload)
    try:
        e = etree.fromstring(r.content)
        print etree.tostring(e, pretty_print=True)
        return e
    except:
        # save log files to disk
        log = open('minipad.log.tar.gz', 'wb')
        log.write(r.content)
        log.close()

        print 'Log Received: saved as minipad.log.tar.gz'

        return None

if len(sys.argv) > 1:
	server_ip = sys.argv[1]

# reset the service into its initial state
payload = {'Action' : 'Restart'}
post(payload)

# configure instance
payload = {'Action' : 'ConfigureImport',
           'Postprocess' : 'True',
           'SameDriveMode' : 'False',
           'UseBuiltInStorage' : 'False',
           'Postproccess' : 'True'
          }
post(payload)

# wait for ConfigurInstance
time.sleep(2)

# get status
payload = {'Action' : 'GetImportTargetStatus',}
r = post(payload)

## Import an Instance
payload = {'Action' : 'ImportInstance',
           'Image.Format' : 'VMDK',
           'Image.ImportManifestUrl' : manifesturl,
          }
post(payload)

done = False
while not done:
    # wait for 5 seconds
    delay = 5
    print "Waiting %d seconds..." % delay
    print
    time.sleep(delay)

    ## DescribeConversionTasks
    payload = {'Action' : 'DescribeConversionTasks',}
    post(payload)

    # get status
    payload = {'Action' : 'GetImportTargetStatus',}
    r = post(payload)

    # check status
    Status = r.find('Status')
    if Status.text in ['Error', 'FinishedTransfer']:
        done = True


# get status
payload = {'Action' : 'GetImportTargetStatus',}
post(payload)

# get log file
payload = {'Action' : 'GetImportTargetLogs',}
post(payload)

# finalizeimport
payload = {'Action' : 'FinalizeConversion'}
post(payload)

# get status
payload = {'Action' : 'GetImportTargetStatus',}
post(payload)
