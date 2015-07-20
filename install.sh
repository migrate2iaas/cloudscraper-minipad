echo Registering simple service
echo Please run from clone-d git directory

NODEBAT=./init.d.cloudscraper-minipad
CURDIR="`pwd`"
echo "#!/bin/bash" > ${NODEBAT}
echo \#chkconfig: 2345 95 20 >> ${NODEBAT}
echo \#description: cloudscraper minipad service >> ${NODEBAT}
echo \#processname: cloudscraper-minipad >> ${NODEBAT}
echo cd ${CURDIR} >> ${NODEBAT}
echo Setting autoupdate
echo "git reset --hard" >> ${NODEBAT}
echo git pull >> ${NODEBAT}
echo python ./src/server.py '&' >> ${NODEBAT}

cp  ${NODEBAT}  /etc/init.d/cloudscraper-minipad

# registering node.bat as a startup file
sudo chmod +x /etc/init.d/cloudscraper-minipad
sudo chown root:root /etc/init.d/cloudscraper-minipad

set +e

sudo update-rc.d cloudscraper-minipad defaults
sudo update-rc.d cloudscraper-minipad enable