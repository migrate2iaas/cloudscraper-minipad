import requests
import time
from lxml import etree

# connect to server
host = 'localhost'
port = 8080


def post(payload):
    url = "http://%s:%d/" % (host, port)

    r = requests.post(url, data = payload)
    e = etree.fromstring(r.content)
    print etree.tostring(e, pretty_print=True)

## Configure Import ####
payload = {'Action' : 'ConfigureImport',
           'SameDriveMode' : 'True',
           'UseBuiltInStorage' : 'True' }
post(payload)

# get status
payload = {'Action' : 'GetImportTargetStatus',}
post(payload)

## Import an Instance
payload = {'Action' : 'ImportInstance',
           'Image.Format' : 'VMDK',
           'Image.ImportManifestUrl' :
           'http://54.165.199.59/gumbo-disk1.vmdkmanifest.xml'
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
    time.sleep(5)

    # if import complete, break
    if done:
        break

    # check status
    done = True

# finalizeimport
payload = {'Action' : 'FinalizeConversion'}
post(payload)

# get status
payload = {'Action' : 'GetImportTargetStatus',}
post(payload)
