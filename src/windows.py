"""
Code extracted from the Linux singleton class

Originally found in:

/Migrate/Windows/Windows.py

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

class Windows(object):

  
    def getSystemDriveName(self):
        return "PHYSICALDRIVE0"

    def createPrimaryPartition(self):
        raise NotImplemented

    def setDiskPrimary(self , disk):
        # points bootloader to another drive
        
        return

    def callBatch(self , batname , environment = os.environ):
        cmd =  Popen(['cmd', '/C', batname ], stdout=PIPE, stderr=STDOUT, env=environment)
        returncode = cmd.wait()
        if cmd.stdout:
            logger.debug(cmd.stdout.read())
        logger.debug(batname + " returned " + str(returncode))
        return returncode

    def postprocess(self , device):
        #TOOD: add some specific parms
        
        # set the disk number - the last digit of device (works for 10 disks only)
        diskn = device[-1]
        curdir = os.path.dirname(os.path.realpath(__file__))
        if self.callBatch(curdir+'\\postprocess\\discover_new_drive.bat ' + str(diskn)) <> 0 or \
           self.callBatch(curdir+'\\postprocess\\change_boot.bat') <> 0 or \
           self.callBatch(curdir+'\\postprocess\\add_virtio.bat') <> 0 or \
           self.callBatch(curdir+'\\postprocess\\set_ip.bat') <> 0:
            
            logger.error("Error postprocessing the instance image")
            raise Exception("Cannot postprocess the image")

    def findDiskBySize(self, minsize):
        # get a list of all the possible block devices to consider
        device = "/dev/null"
        lsblk = Popen(['wmic', 'diskdrive', 'list' , 'brief' ], stdout=PIPE, stderr=STDOUT)
        logger.info("Looking for drive ofsize  " + str(minsize))
        
        for line in lsblk.stdout:
            logger.debug(line)
            if 'PHYSICALDRIVE' in line:
                logger.debug(line)
                match = re.search("PHYSICALDRIVE[0-9]+" , line)
                if match:
                    name = match.group()
                else:
                    logger.debug("Bad line, skipping")
                    continue
                
                match = re.search("[0-9]" , line)
                partitions = match.group()
                                
                match = re.search("[0-9][0-9][0-9][0-9]+" , line)
                size = match.group()

                logger.debug('name:%s size:%s partitions:%s' % (name, size, partitions))
                # skipping drives having a partition
                if int(partitions) > 0:
                    logger.debug('Skipping disk with partitions')
                    continue
                
                # skip system drive
                if name == self.getSystemDriveName():
                    continue

                if long(size) >= long(minsize):
                    device = "\\\\.\\"+name
                    break
        returncode = lsblk.wait()

        if returncode:
            logger.error("Error with wmic program.")

        return device
