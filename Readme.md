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

0. (Only if the release is not latest) sudo sed -i -e 's/archive.ubuntu.com\|security.ubuntu.com/old-releases.ubuntu.com/g' /etc/apt/sources.list
1. sudo apt-get update
2. sudo apt-get -y install gcc python-dev libxml2-dev libxslt-dev git python-setuptools zlib1g-dev
3. sudo easy_install pip
4. sudo pip install lxml
5. sudo pip install shortuuid
6. sudo pip install psutil

7. TODO: how to enavle initclt\upstart?