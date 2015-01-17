"""
Code extracted from the Linux singleton class

Originally found in:

/Migrate/Linux/__init__.py

"""

# --------------------------------------------------------
__author__ = "Vladimir Fedorov"
__copyright__ = "Copyright (C) 2013 Migrate2Iaas"
#---------------------------------------------------------

import logging
import traceback


import filecmp
import unittest
import shutil
import os

import re
from subprocess import *

logger = logging.getLogger('minipad')

class Linux(object):

    def findDeviceForPath(self , path):
        p1 = Popen(["df" , path], stdout=PIPE)
        output = p1.communicate()[0]
        lastline = output.split("\n")[1]
        voldev = lastline[:lastline.find(" ")]
        return voldev

    def __findLvmDev(self , volgroup):
        p1 = Popen(["lvdisplay" , "-m", volgroup], stdout=PIPE)
        output = p1.communicate()[0]

        if str(output).count("Physical volume") > 1:
            logger.error("!!!ERROR: LVM config is too complex to parse!")
            raise LookupError()

        match = re.search( "Physical volume([^\n]*)", output )
        if match == None:
            logger.error("!!!ERROR: Couldn't parse LVM config! ")
            logger.error("Config " + output)
            raise LookupError()

        volume = match.group(1)
        return volume.strip()

    def getSystemDriveName(self):
        rootdev = self.findDeviceForPath("/")
        bootdev = self.findDeviceForPath("/boot")


        logger.info("The root device is " + rootdev);
        logger.info("The boot device is " + bootdev);

        # try to see where it resides. it's possible to be an lvm drive
        if rootdev.count("mapper/VolGroup-") > 0:
             volgroup = str(rootdev).replace('mapper/VolGroup-', 'VolGroup/')
             rootdev = self.__findLvmDev(volgroup)
             logger.info("LVM " + volgroup + " resides on " + rootdev);

        #substract the last number making /dev/sda from /dev/sda1.
        rootdrive = rootdev[:-1]
        bootdrive = bootdev[:-1]


        if rootdrive != bootdrive:
            logger.warn("!Root and boot drives are on different physical disks. The configuration could lead to boot failures.")

        try:
            # In the current impl we do full disk backup
            if os.stat(rootdrive):
                return rootdrive
        except Exception as e:
            #supper-floppy like disk then
            logger.info("There is no " + rootdrive + " device, treating " +  rootdev+ " as system disk")
            return rootdev

    def createPrimaryPartition(self):
        raise NotImplemented

    def setDiskPrimary(self , disk):
        # points bootloader to another drive
        
        return

    def findDiskBySize(self, minsize):
        # get a list of all the possible block devices to consider
        device = '/dev/null'
        lsblk = subprocess.Popen(['lsblk', '-rb'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in lsblk.stdout:
            if 'disk' in line:
                parts = re.split(r'\s+', line.strip())
                name, majmin, rm, size, ro, devtype = parts[:6]
                if len(parts) > 6:
                    mountpoint = parts[6]
                else:
                    mountpoint = None

                logger.debug(line)
                logger.debug('name:%s size:%s' % (name, size))

                # skip system drive
                if name == self.getSystemDriveName():
                    continue

                if long(size) >= long(minsize):
                    device = '/dev/' + name
                    break
        returncode = lsblk.wait()

        if returncode:
            logger.error("Error with lsblk program.")

        return device
