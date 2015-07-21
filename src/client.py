import requests
import time
from lxml import etree
import sys

# need to get this from VM
server_ip = '67.43.162.101'
server_port = 80

#manifesturl = 'https://s3.amazonaws.com/minipad/1312-28801ECA87-Cmanifest.xml'
manifesturl = 'https://s3.amazonaws.com/cloudscraper-1436845841-us-east-1/static-ububtu14-sdamanifest.xml?AWSAccessKeyId=AKIAIY2X62QVIHOPEFEQ&Expires=1437642545&Signature=WNJwA9blDAn%2BNTSXTnm2TxJ5Vgo%3D'




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
