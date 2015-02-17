Cloudscraper MiniPad Web service
--------------------------------

The service is launched on startup using Ubuntu's upstart system.  
There should be a process running called 'minipad'. The service is 
configured using the configuration file /etc/init/minipad.conf

To start/stop/restart the service:

sudo initctl start minipad
sudo initctl stop minipad
sudo initctl restart minipad

The server itself is located in 
/home/minipad/cloudscraper.minpad/src/server.py 
since it is currently under development.  

log file is saved in
/var/log/minipad.log


--------------------------------
To install on Ubuntu:

0. (Only if the release is not latest, 14.04) sudo sed -i -e 's/archive.ubuntu.com\|security.ubuntu.com/old-releases.ubuntu.com/g' /etc/apt/sources.list
1. sudo apt-get update
2. sudo apt-get -y install gcc python-dev libxml2-dev libxslt-dev git python-setuptools zlib1g-dev
3. sudo easy_install pip
4. sudo pip install lxml
5. sudo pip install shortuuid
6. sudo pip install psutil
7. git clone https://git.assembla.com/cloudscraper.minpad.git


8. TODO: how to enable initclt\upstart?
alternatively: python ~/cloudscraper.minpad/src/server.py


To install on Windows:
1. Install https://www.python.org/ftp/python/2.7.8/python-2.7.8.msi (check "Add python.exe to path" when prompted) 
2. Install Git https://github.com/msysgit/msysgit/releases/download/Git-1.9.5-preview20141217/Git-1.9.5-preview20141217.exe (Select use git from Windows command prompt)
3. download https://bootstrap.pypa.io/get-pip.py
4. python get-pip.py
5. python -m pip install lxml
6. python -m pip install shortuuid
7. python -m pip install psutil
8. python -m pip install requests
9. cd c:\ && git clone https://git.assembla.com/cloudscraper.minpad.git
To Run: 
10. schtasks /create /F /tn "Minipad" /tr "cmd /C %CD%\cloudscraper.minpad\start_server.cmd" /sc onstart /ru System
11. schtasks /run /tn "Minipad" 
(TODO: check logs place)
12. Open port 
netsh advfirewall firewall add rule name="Open HTTP port 80" dir=in action=allow protocol=TCP localport=80

Notes (to boot from the same VM like on onApp):
1.Windows would require to have bootmgr of newer version in order to boot
2.The tcpip interface should be named "Local Area Network"
3.To add Deployment Tools , install the latest ADK and copy <ADK install Path>\Assessment and Deployment Kit\Deployment Tools\ to C:\Deployment Tools\
4.The tcpip interface should be named "VirtualNetworkAdapter"
to rename exec
netsh interface set interface name="Local Area Network" newname="VirtualNetworkAdapter"
(at the moment it's renamed during postprocess set_ip.bat step)
