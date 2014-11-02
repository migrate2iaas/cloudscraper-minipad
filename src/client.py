import requests
import time
from lxml import etree

# connect to server
#host = 'localhost'
#port = 8080

server_ip = '192.168.2.20'
server_port = 80

# IP is localhost. Can make this more dynamic
client_ip = '192.168.2.17:8000'
manifest = 'M2IAAS-256EBF9F-Cmanifest.xml'
manifest = '1312-28801ECA87-Cmanifest.xml'

def post(payload):
    url = "http://%s:%d/" % (server_ip, server_port)

    r = requests.post(url, data = payload)
    e = etree.fromstring(r.content)
    print etree.tostring(e, pretty_print=True)

## Call a non-existant Action
payload = {'Action' : 'FakeAction'}
post(payload)

## Configure Import ####
payload = {'Action' : 'ConfigureImport',
           'SameDriveMode' : 'False',
           'UseBuiltInStorage' : 'True' }
post(payload)

# get status
payload = {'Action' : 'GetImportTargetStatus',}
post(payload)
## Import an Instance
payload = {'Action' : 'ImportInstance',
           'Image.Format' : 'VMDK',
           'Image.ImportManifestUrl' :
           'http://%s/%s' % (client_ip, manifest)
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
    delay = 5
    print "Waiting %d seconds..." % delay
    print
    time.sleep(delay)

    # if import complete, break
    if done:
        break

    # check status
    done = True

payload = {'Action' : 'GetImportTargetLogs', }
post(payload)

# finalizeimport
payload = {'Action' : 'FinalizeConversion'}
post(payload)

# get status
payload = {'Action' : 'GetImportTargetStatus',}
post(payload)
