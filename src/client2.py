import requests
import time
from lxml import etree

# need to get this from VM
server_ip = '54.164.136.46'
server_port = 80

manifesturl = 'https://s3.amazonaws.com/minipad/1312-28801ECA87-Cmanifest.xml'

def post(payload):
    url = "http://%s:%d/" % (server_ip, server_port)

    r = requests.post(url, data = payload)
    try:
        e = etree.fromstring(r.content)
        print etree.tostring(e, pretty_print=True)
    except:
        print r.content

## Import an Instance
payload = {'Action' : 'ImportInstance',
           'Image.Format' : 'VMDK',
           'Image.ImportManifestUrl' : manifesturl,
          }
post(payload)

done = False
while True:
    ## DescribeConversionTasks
    payload = {'Action' : 'DescribeConversionTasks',}
    post(payload)

    # get status
    payload = {'Action' : 'GetImportTargetStatus',}
    post(payload)

    # wait for 5 seconds
    delay = 1
    print "Waiting %d seconds..." % delay
    print
    time.sleep(delay)

    # if import complete, break
    if done:
        break

    # check status
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
