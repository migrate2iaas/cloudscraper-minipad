Cloudscraper MiniPad Web service
--------------------------------

TODO: add docs link
TODO: add use cases


--------------------------------
To install on Ubuntu:

(Only if the release is not latest, 14.04) sudo sed -i -e 's/archive.ubuntu.com\|security.ubuntu.com/old-releases.ubuntu.com/g' /etc/apt/sources.list
sudo apt-get install grub2 
(click ok on installation, then pick maintainer configuration when prompted)
sudo apt-get update
sudo apt-get -y install gcc python-dev libxml2-dev libxslt-dev git python-setuptools zlib1g-dev python-lxml
sudo easy_install pip & sudo pip install shortuuid & sudo pip install psutil
git clone -b 642_onapp_release http://git.assembla.com/cloudscraper.minpad.git



TODO: how to enable initclt\upstart?
To add to autorun: 

cd ~/cloudscraper.minpad && chmod +x install.sh && bash install.sh
service cloudscraper-minipad start
One-time test run:
python ~/cloudscraper.minpad/src/server.py


_________________________________________
To install on Windows:
1. Install https://www.python.org/ftp/python/2.7.10/python-2.7.10.msi (check "Add python.exe to path" when prompted) 
2. Install Git https://github.com/msysgit/msysgit/releases/download/Git-1.9.5-preview20141217/Git-1.9.5-preview20141217.exe (Select use git from Windows command prompt)
3. python -m pip install lxml==3.4.4 && python -m pip install shortuuid && python -m pip install psutil && python -m pip install requests
4. cd c:\ && git clone -b 642_onapp_release  https://git.assembla.com/cloudscraper.minpad.git
(For AWS Xen): cd c:\ && git clone -b 908_xen  https://git.assembla.com/cloudscraper.minpad.git

To Run: 
10. schtasks /create /F /tn "Minipad" /tr "cmd /C %CD%\cloudscraper.minpad\start_server.cmd" /sc onstart /ru System
11. schtasks /run /tn "Minipad" 
(TODO: check logs place)
12. Open port 
netsh advfirewall firewall add rule name="Open HTTP port 80" dir=in action=allow protocol=TCP localport=80


Notes (to boot from the same VM like on onApp):
1.Windows would require to have bootmgr of newer version in order to boot (get the bootmgr from misc\WIN12R2\bootmgr)

2.The tcpip interface should be named "Local Area Connection"
3.To add Deployment Tools , install the latest ADK (Deployment Tools only) and copy <ADK install Path>\Assessment and Deployment Kit\Deployment Tools\ to C:\Deployment Tools\

4.The tcpip interface should be named "VirtualNetworkAdapter"
to rename exec
netsh interface set interface name="Local Area Connection" newname="VirtualNetworkAdapter"
(at the moment it's renamed during postprocess set_ip.bat step)
(Not needed for AWS XEN)

5. Add Xen drivers
http://migrate2iaas.blob.core.windows.net/cloudscraper/aws_v2v.zip
extract \Citrix\XenTools contents to C:\Xen\amd64
extract ec2copy\Citrix_xensetup.exe to C:\Xen
