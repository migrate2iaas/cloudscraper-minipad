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

    def findDiskBySize(self, minsize):
        # get a list of all the possible block devices to consider
        device = "/dev/null"
        lsblk = subprocess.Popen(['wmic', 'diskdrive', 'list' , 'brief' ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in lsblk.stdout:
            if 'PHYSICALDRIVE' in line:
                logger.debug(line)
                logger.debug('name:%s size:%s' % (name, size))
                match = re.search("PHYSICALDRIVE[0-9]+" , line)
                if match:
                    name = match.group()
                else:
                    logger.debug("Bad line, skipping")
                    continue

                match = re.search("[0-9][0-9][0-9][0-9]+" , line)
                size = match.group()

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
