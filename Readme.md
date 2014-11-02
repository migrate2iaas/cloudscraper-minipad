Cloudscraper MiniPad Web service

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


