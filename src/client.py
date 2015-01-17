import requests
import time
from lxml import etree

# need to get this from VM
server_ip = '67.43.162.99'
server_port = 80

#manifesturl = 'https://s3.amazonaws.com/minipad/1312-28801ECA87-Cmanifest.xml'
manifesturl = 'http://cloudscraper-1420955437-eu-west-1.s3.amazonaws.com/WIN-9RJUUDQ3A9F-Cmanifest.xml'

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

# reset the service into its initial state
payload = {'Action' : 'Restart'}
post(payload)

# configure instance
payload = {'Action' : 'ConfigureImport',
           'SameDriveMode' : 'False',
           'UseBuiltInStorage' : 'False',
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
