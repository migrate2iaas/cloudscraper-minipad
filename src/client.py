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
           'http://54.165.199.59/gumbo-disk1.vmdkmanifest.xml'
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
