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
import time
import sys
import stat
import socket, struct

import re
from subprocess import *

logger = logging.getLogger('minipad')

class Linux(object):
    UnknownFamily = 0
    DebianFamily = 1
    RedhatFamily = 2 
    def __init__(self):
        self.linux_family = Linux.DebianFamily
        self.imported_sys_grub_path = "/boot/grub/grub.cfg"
        self.imported_sys_grub2_path = "/boot/grub2/grub.cfg"
        self.presaved_imported_sys_grub_path = "/boot/grub/imported-grub.cfg"
        self.local_grub_path = "/boot/grub/grub.cfg"
        # we also change old grub settings if they are present
        self.local_grub_legacy_path = "/boot/grub/grub.conf" 
        

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
        lsblk = Popen(['lsblk', '-rb'], stdout=PIPE, stderr=STDOUT)
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

                #todo: skip disks already fiiled

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

    def getNetworkSettingsPath(self):
      """Returns path to netowrk config"""
      if self.linux_family == Linux.RedhatFamily:
          return "/etc/sysconfig/network-scripts/ifcfg-eth0"
      if self.linux_family == Linux.DebianFamily:
          return "/etc/network/interfaces"
      raise NotImplementedError

    def setBootDisk(self):
        #backup of current grub config
        src = self.local_grub_path
        dest = self.local_grub_path + ".backup"
        #grub2 must be present
        if os.path.exists(self.local_grub_path):
            shutil.copyfile(src,dest)
        #replaces this pad system grub by imported one
        src = self.presaved_imported_sys_grub_path
        dest = self.local_grub_path
        shutil.copyfile(src,dest)
        #set grub1 if it's present to chainload grub2
        if os.path.exists(self.local_grub_legacy_path):
            config = "default 0\n\
            timeout 3\n\
            hiddenmenu\n\n\n\
            title Chainload grub2\n\
            rootnoverify (hd0)\n\
            chainloader +1\n\
            boot\n"
            #backup of existing grub config
            src = self.local_grub_legacy_path
            dest = self.local_grub_legacy_path + ".backup"
            #grub2 must be present
            shutil.copyfile(src,dest)
            os.chmod(self.local_grub_legacy_path, stat.S_IWRITE + stat.S_IREAD )
            with open(self.local_grub_legacy_path, "w") as f:
                f.write(config)


    def setNetworkSettings(self):
        network_cfg = self.getNetworkSettingsPath()
        dest = dir_path+network_cfg
        # check if configs are present there - we have same OS type there
        if os.path.exists(dest):
            logger.info("Applying Ubuntu network settings")
            src = network_cfg
            shutil.copyfile(src,dest)
        else:
            # the easiest way is to read ifconfig then
            logger.info("Applying RHEL network settings")
            device = "eth0"
            ipconf = Popen(['ip', '-f', 'inet', 'addr', 'show', device], stdout=PIPE, stderr=STDOUT)
            output = ipconf.communicate()[0]
            match = re.search("inet ([0-9.]+)/([0-9]+)",  output , re.MULTILINE )
            if not match:
                logger.error("Failed to find ip data in the command output: " + output)
            static_ip = match.group(1)
            mask_length = int(match.group(2))
            mask_bits = (1<<32) - (1<<32>>mask_length)
            mask = socket.inet_ntoa(struct.pack(">L", mask_bits))
            ipconf = Popen(['ip', '-f inet', 'route', 'list'], stdout=PIPE, stderr=STDOUT)
            output = ipconf.communicate()[0]
            match = re.search("default via ([0-9.]+)",  output , re.MULTILINE )
            if not match:
                logger.error("Failed to find ip data in the command output: " + output)
            gateway = match.group(0)
            
            #write config to default location for CentOS and RHEL
            retval = "DEVICE="+device+"\n"
            if static_ip:
              retval = retval + "BOOTPROTO=static\nDHCPCLASS=\nIPADDR="+static_ip+"\nNETMASK="+mask+"\nGATEWAY="+gateway+"\n" # not sure of gateway
            dest = dir_path+"/etc/sysconfig/network-scripts/ifcfg-eth0"
            with open(dest , "w") as f:
                f.write(retval)
            

            

    def postprocess(self, device):
        #-1: install grub
        logger.info("Installing GRUB2")
        root_dev = self.getSystemDriveName()
        grub = Popen(['grub-install', root_dev], stdout=PIPE, stderr=STDOUT)
        output = grub.communicate()[0]
	logger.debug(str(output))
        
        # 0. mount the partition
        dir_path = '/tmp/tempmount'+str(int(time.time()))
        os.makedirs(dir_path)
        if str(device[-1]).isdigit():
            dev_path = device
        else:
            hdparm = Popen(['hdparm', '-z', device], stdout=PIPE, stderr=STDOUT)
            output = hdparm.communicate()[0]
            logger.info(str(output))
            dev_path = device + "1"
        
        mount = Popen( ['mount', dev_path, dir_path], stdout=PIPE, stderr=STDOUT)
        output = mount.communicate()[0]
        logger.info(str(output))
        # 1. copy network configs
        self.setNetworkSettings();

        # 2. save target system grub options locally
        grub_path = self.imported_sys_grub_path
        if os.path.exists(dir_path+self.imported_sys_grub2_path):
            grub_path = self.imported_sys_grub2_path
        src = dir_path+grub_path
        dest = self.presaved_imported_sys_grub_path
        shutil.copyfile(src,dest)
        
        
