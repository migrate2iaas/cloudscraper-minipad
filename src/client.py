import requests
import time

# connect to server
host = 'localhost'
port = 8080

url = "http://%s:%d/" % (host, port)

payload = {'Action' : 'ConfigureImport',
           'SameDriveMode' : 'True',
           'UseBuiltInStorage' : 'True' }
r = requests.post(url, data = payload)
print r.text


payload = {'Action' : 'ImportInstance',
           'Image.Format' : 'VMDK',
           'Image.ImportManifestUrl' :
           'https://cloudscraper-1407147346-us-east-1.s3.amazonaws.com/12312RCF2-Jmanifest.xml'
          }
r = requests.post(url, data = payload)
print r.text



for i in range(1):
    payload = {'Action' : 'GetImportTargetStatus',}
    r = requests.post(url, data = payload)
    print r.text
    time.sleep(2)

# post request

#configureimport

#finalizeimport
