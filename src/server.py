#!/usr/bin/python
"""
MiniPadTarget
~~~~~~~~~~~~~

This module implements an HTTP service accepting
data and writing it to disks on the VM

The service is "one-shot". It accepts 
    one ConfigureImport
    one ImportInstance
    [0..many] ImportVolume
    [0..many] DescribeConversionTasks
    one FinalizeConversion
After that, treat service as unavailable. 
User will create a new VM from the image in case new is needed. 

"""

# --------------------------------------------------------
__author__ = "James Munroe"
__copyright__ = "Copyright (C) 2014 Migrate2Iaas"
# --------------------------------------------------------

import logging
import time
import datetime
from BaseHTTPServer import BaseHTTPRequestHandler
import requests
from lxml import etree
import traceback
import tarfile
import shortuuid
import cgi
import threading
import psutil # for detecting disk usage
import os
import subprocess


logger = logging.getLogger('minipad')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('/var/log/minipad.log')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('[%(asctime)s] (%(threadName)-10s) %(message)s',)
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handers to logger
logger.addHandler(fh)
logger.addHandler(ch)


class Service(object):
    """the web service"""

    def __init__(self):
        """inits service"""

        logger.debug('Web Service initialized')

        self.Statuses = ['NotConfigured',
                         'Initializing',
                         'ReadyToTransfer',
                         'FinishedTransfer',
                         'FinishedConversion']
        self.status = 'NotConfigured'
                         

        self.Log = []

    def configure_import(self):
        """ """

        logger.debug('Do the work of configuration')

        self.status = 'Initializing'

        # how to return an error??

        # is there anything else to do to configure?
        #   move the body of ConfigureImport here?

        uuid = shortuuid.uuid()
        self.conversionTaskId = 'import-' + uuid

        # now + 1day
        now = datetime.datetime.utcnow()
        self.expirationTime = now + datetime.timedelta(days = 1)

        self.bytesConverted = 0

        self.availability = '' # e.g. us-east
        self.description = 'cloudscraper'

        #  these should be updated by ImportInstance/ImportVolume
        self.format = '' # e.g. VMDK
        self.size = 0
        self.importManifestUrl = ''
        self.volumeSize = 0

        self.status = 'ReadyToTransfer'

        # done
        logger.debug('ConfigureImport complete')

    def ConfigureImport(self, 
                        SameDriveMode=None, 
                        UseBuiltInStorage=None,
                        **kwargs):
        """Preconfigure the appliance"""

        logger.debug('ConfigureImport called')

        response = etree.Element('Response')
        code = 500 # Server Error
        Errors = etree.SubElement(response, 'Errors')

        if self.status <> 'NotConfigured':
            logger.error('AlreadyConfigured')

            error = "AlreadyConfigured"

            return (code, response)

        # SameDriveMode 
        # Switch to deploy the image to the system disk.
        if SameDriveMode == 'True':
            self.SameDriveMode = True
        elif SameDriveMode == 'False':
            self.SameDriveMode = False
        else:
            logger.debug('SameDriveMode missing or wrong value')
            code = 400
            return (code, response)

        #UseBuiltInStorage 
        # Switch to use build-in eucalyptus-cloud storage.
        if UseBuiltInStorage == 'True':
            self.UseBuiltInStorage = True

            # test for 
            #  BuiltInStorageUnavailable, 
            #  BuiltInStorageError, 
            #  BuiltInStorageNoDisk, 

        elif UseBuiltInStorage == 'False':
            self.UseBuiltInStorage = False

        else:
            logger.debug('UseBuiltInStorage or wrong value')
            code = 400
            return (code, response)
            
        """
<Response>
        <Errors>
        <Error>
        <Code>ResourceLimitExceeded</Code>
        <Message>Task failed to initialize - conversion task limit (5) exceeded.</Message>
        <StackTrace>
         Traceback (most recent call last):
          File "F:\cloudscraper\migrate\Migrate\Migrate\Migrator.py", line 114, in runFullScenario
            if self.createSystemTransferTarget() == False:
          File "F:\cloudscraper\migrate\Migrate\Migrate\Migrator.py", line 300, in createSystemTransferTarget
            self.__systemMedia = self.createImageMedia(self.__migrateOptions.getSystemImagePath() , self.__migrateOptions.getSystemImageSize() + self.__additionalMediaSize)
          File "F:\cloudscraper\migrate\Migrate\Migrate\Migrator.py", line 272, in createImageMedia
            media.open()
          File ".\Images\StreamVmdkMedia.py", line 222, in open
            self.__openExisting()
          File ".\Images\StreamVmdkMedia.py", line 685, in __openExisting
            raise VMDKStreamException("File is of wrong format or corrupted")
        VMDKStreamException: File is of wrong format or corrupted 
        </StackTrace>
        </Error>
        </Errors>
        <RequestID>4ea6bfd2-dc65-453e-ae23-7d22b9e50dc8</RequestID>
        </Response>
        """


        # launch thread to go initialize the import
        worker = threading.Thread(target=self.configure_import,
                                  args=())
        worker.start()

        response = etree.Element("ConfigureImportResult")
        result = etree.SubElement(response, 'Result')
        result.text = "True"

        return (code, response)


    def GetImportTargetStatus(self, **kwargs):
        """Queries the target appliance status"""

        logger.debug('GetImportTargetStatus called')

        response = etree.Element("ImportTargetStatus")
        status = etree.SubElement(response, 'Status')
        status.text = self.status

        StatusMessage = etree.SubElement(response, 'StatusMessage')
        StatusMessage.text = ''

        StatusCode = etree.SubElement(response, 'StatusCode')
        StatusCode.text = '0'

        return (200, response)

        """
    Response Elements:
    Type: ImportTargetStatus
    Contents:
        Status
            Type: String
            Valid values: NotConfigured|Initializing|ReadyToTransfer|
                          Error|FinishedTransfer|FinishedConversion
        StatusMessage
            The description of current step or error if any
            Type: String

        StatusCode
            Status or error code if any
            Type: Integer

    Errors:
        InternalError, BadParameters

    """

    def ImportInstance(self, **kwargs):
        """
        Creates import instance task.

        See http://docs.aws.amazon.com/AWSEC2/latest/APIReference/ApiReference-query-ImportInstance.html for description. 

        Note, only one volume is transferred in time.

        Asynchronous. The status is got via DescribeConversionTasks.

        Only Image.Format and Image.ImportManifestUrl parameters 
            are needed. Ignore other parms.
        """
        logger.debug('ImportInstance called')
        logger.debug('parms: %s' % kwargs)

        self.ImportManifestUrl = kwargs['Image.ImportManifestUrl']
        self.ImportType = 'ImportInstance'

        # launch thread to go import
        worker = threading.Thread(target=self.handle_import,
                                  args=())
        worker.start()

        response = etree.Element('Response')

        return (200, response)

    def ImportVolume(self, **kwargs):
        """
        Creates import volume task.
        http://docs.aws.amazon.com/AWSEC2/latest/APIReference/ApiReference-query-ImportVolume.html 
        Asynchronous. 

        Only Image.Format and Image.ImportManifestUrl parameters are 

        needed. Ignore other parms.
        """
        logger.debug('ImportVolume called')

        # launch thread to go import volume
        worker = threading.Thread(target=self.handle_import,
                                  args=())
        worker.start()

        response = etree.Element('Response')

        return (200, response)

    def DescribeConversionTasks(self, **kwargs):
        """
        Get info on conversion tasks (both volume and instance)

        See:
        http://docs.aws.amazon.com/AWSEC2/latest/APIReference/ApiReference-query-DescribeConversionTasks.html 
        """

        response = etree.Element('DescribeConversionTasksResponse')

        # only valid if ...
        if self.status in ['ReadyToTransfer', 'FinishedTransfer']:
            conversionTasks = etree.SubElement(response, 'conversionTasks')
            
            item = etree.SubElement(conversionTasks, 'item')
            conversionTaskId = etree.SubElement(item, 'conversionTaskId')
            conversionTaskId.text = self.conversionTaskId
            expirationTime = etree.SubElement(item, 'expirationTime')
            expirationTime.text = self.expirationTime.strftime('%Y-%m-%dT%H:%M:%SZ')
            importVolume = etree.SubElement(item, 'importVolume')
            importVolume.text = ''

            bytesConverted = etree.SubElement(item, 'bytesConverted')
            bytesConverted.text = str(self.bytesConverted)

            availability = etree.SubElement(item, 'availability')
            availability.text = self.availability

            description = etree.SubElement(item, 'description')
            description.text = self.description

            image = etree.SubElement(item, 'image')
            format = etree.SubElement(image, 'format')
            format.text = self.format

            size = etree.SubElement(image, 'size')
            size.text = str(self.size)

            importManifestUrl = etree.SubElement(image, 'importManifest')
            importManifestUrl.text = self.importManifestUrl

            volume = etree.SubElement(item, 'volume')
            size = etree.SubElement(volume, 'size')
            size.text = str(self.volumeSize)

            state = etree.SubElement(item, 'state')
            state.text = self.status

            statusMessage = etree.SubElement(item, 'statusMessage')
            statusMessage.text = 'Pending'

        logger.debug('DescribeConversionTasks called')

        return (200, response)


    def FinalizeConversion(self, InjectDrivers = 'NoDrivers',
                           **kwargs):
        """
        Finalizes conversion making sure the copied image will 
        boot on the reboot operation.

        Parms:
            InjectDrivers
                Whether or not insert specific drivers
            Type: String
            Default: NoDrivers
            Valid values: VMware|VirtIO|Xen|HyperV

        Note: nothing should be done a stub for now.
        """
        
        logger.debug('FinalizeConversion called')

        # should probably throw an error if the conversion is still
        # in progress

        # When FinalizeConversion is requested
        self.Status = 'FinishedTransfer'

        response = etree.Element('Response')

        return (200, response)

        # When FinalizeConversion is complete.
        self.Status = 'FinishedConversion'

    def GetImportTargetLogs(self, **kwargs):
        """
        Returns logs of the import target appliance.

        Parms:
            Type: LogsDate
                Contents:
                    StartDate
                        Type: Date
                    EndDate 
                        Type: Date
            AllLogs
                Default: False 
                Valid values: True|False

        Response Elements:
            Log tar.gz file stream

        Errors:
            InternalError, BadParameters
        """
            
        # TODO: handle parameters
        # TODO: select only a date range from the log file

        # compress log file
        logfilename = '/var/log/minipad.log'
        out = tarfile.open('minipad.log.tar.gz', mode='w:gz')
        try:
            out.add(logfilename)
        finally:
            out.close()

        log_tarball = open('minipad.log.tar.gz', 'rb')

        response = log_tarball.read()

        return (200, response)

    def handle_import(self):
        """
        Conversion Task Handling Requirements

        The image to be converted split into 10 MB parts. 
        """
        
        # parts are described in XML manifest. 
        # XML manifest URL is passed via ImportInstance \ ImportVolume request.
        # XML should be downloaded via URL and parsed. 
        # XML contains list of URLs to image parts. 
        logger.debug('downloading manifest')
        
        url = self.ImportManifestUrl
        logger.debug(url)

        r = requests.get(url)
        xml = r.content

        manifest = etree.fromstring(xml)
        import_ = manifest.find('import')

        # Size is ??
        size = import_.find('size').text

        # Volume is in GB
        self.volumeSize = float(import_.find('volume-size').text)

        # number of parts
        parts = import_.find('parts')
        count = parts.get('count')

        # 2.2 Find a disk/volume in the system

        device = self.GetVolume()

        if device == '':
            # no device found
            return

        handle = open(device, 'wb')

        for part in parts.findall('part'):
            index = int(part.get('index'))
            logger.debug('part index %d' % index)

            byte_range = part.find('byte-range')
            start = int(byte_range.get('start'))
            end = int(byte_range.get('end'))
            key = part.find('key').text
            get_url = part.find('get-url').text

            """
            Every image part should be read and then written to 
            an appropriate volume. 
            """

            # 2.3 For every part download it into memory and write 
            # to the found disk device (e.g. /dev/sdb)

            #r = requests.get(get_url)
            #logger.debug('Downloaded %d bytes' % len(r.content))

            # write to appropriate volume
            handle.write(r.content)

        # Every part of conversion task should be logged, 
        # the current step and its status should be accessible via 
        # DescribeConversionTasks command.
        handle.close()

    def GetVolume(self):
        """
        Find a block device with sufficient free space and
        create a new partition

        The command line program 'parted' is used to
        do most of the heavy lifting here
        """

        logger.debug('Finding a free region of size %s' % self.volumeSize)

        logger.debug('SameDriveMode: %s' % self.SameDriveMode)

        #2.2.1 If SameDriveMode was passed in ConfigureImport request, 
        # and ImportInstance command is being processed, partition the 
        # free space on the system drive

        if self.SameDriveMode and self.ImportType == 'ImportInstance':
	    # what drive is the root system on?

            # partition free space on system drive

            pass
        else:
            # get list of all disks/volumes on system
            # find an appropriate free disk 
            # (criteria - size should be equal to "volume-size" in 
            # GBs set in the manifest) in the system. Note, disks are
            # added into the system dynamically.

            pass


        # TODO: log parted subprocess calls

        # get a list of all the possible block devices to consider
        # on this system
        parted_list = subprocess.check_output(['parted', '-sml'])
        # parted returns output stanzas of the form:
        """
        BYT;
        /dev/sda:3221MB:scsi:512:512:msdos:ATA VBOX HARDDISK;
        1:1049kB:256MB:255MB:ext2::boot;
        2:257MB:3220MB:2963MB:::;
        5:257MB:3220MB:2963MB:::lvm;
        """

        block_devices = []
        block = {}
        for line in parted_list.split(';'):
            line = line.strip()
            if line == 'BYT':
                if len(block) > 0:
                    block_devices.append(block)
                    # new block device
                    block = {}
            elif len(block) == 0:
                # first line after BYT;
                device, size, device_type, block_size, _, part_type, flag = line.split(':')
                block['device'] = device
                block['size'] = size
                block['device_type'] = device_type
                block['block_size'] = block_size
                block['part_type'] = part_type
                block['flag'] = flag

                block['partitions'] = []
            elif line == '':
                pass
            else:
                # partition information
                part_number, start, stop, part_size, fs_type, _, flag = line.split(':')
                partition = {'part_number' : part_number,
                             'start' : start,
                             'stop' : stop,
                             'part_size' : part_size,
                             'fs_type' : fs_type,
                             'flag' : flag }
                block['partitions'].append(partition)

        if len(block) > 0:
            block_devices.append(block)

        for block in block_devices:
            logger.debug('found: %s (%sMB)' % (block['device'], block['size']))

        # As well, let's get a list of paritions with their mountpoints
        # we are searching for the system drive
        system_drive = ''
        for partition in psutil.disk_partitions(all=True):
            usage = psutil.disk_usage(partition.mountpoint)

            # detect system drive by search for the partition mounted as /boot
            if partition.mountpoint == '/boot':
                system_drive = partition.device[:-1]


        if system_drive == '':
            # if system_drive can not be determined
            logger.warning('system drive cannot be determined')
        else:
            logger.debug('system drive is %s' % system_drive)

        # sentinal to detect when a suitable free space has been found
        region = {}

        # what are all of the free regions on each block device?
        for block in block_devices:
            
            if len(region) > 0:
                # we've already found a suitable free region
                break

            # if system_drive, only look there
            if self.SameDriveMode:
                if block['device'] <> system_drive:
                    continue

            # find all of the free regions on this block device:
            response = subprocess.check_output(['parted', 
                '-sm', block['device'],
                'unit', 'MB',
                'print', 'free', 
                ])

            for line in response.split(';'):
                line = line.strip()
                if line == 'BYT':
                    continue
                elif line == '':
                    continue
                else:
                    p = line.split(':')
                    if p[4] == 'free':
                        foundSize = float(p[3][:-2])
                        logger.debug('free region: %s' % p)
                        if foundSize >= self.volumeSize*1024:

                            region = { 'device' : block['device'],
                                       'start' : float(p[1][:-2]),
                                       'end' : float(p[2][:-2]),
                                       'size' : float(p[3][:-2]) , } 
                            break

        if len(region) > 0:
            # create partition 
            logger.debug('found a suitable region on %s' % region['device'])

            # get a list of all the existing partition numbers on this 
            # block device
            response = subprocess.check_output( [ 'parted', '-sm', 
                                            region['device'],
                                            'print'] )
            old_numbers = set()
            for partition in response.splitlines()[2:]:
                p = partition.split(':')
                old_numbers.add(p[0])
            logger.debug('existing partition numbers: %s' % old_numbers)

            start = '%.1fMB' % region['start']
            end = '%.1fMB' % (self.volumeSize*1024 + region['start'])
            # make the partition
            try:
                response = subprocess.check_output( ['parted',
                              '-sm',
                              region['device'],
                              'mkpart',
                              # can we make an assumption here about
                              'primary', # extended? logical?
                              start,
                              end]
                              )

                # so what partition number was created?

                # get a list of all the new partition numbers on this 
                # block device
                response = subprocess.check_output( [ 'parted', '-sm', 
                                                region['device'],
                                                'print'] )
                new_numbers = set()
                for partition in response.splitlines()[2:]:
                    p = partition.split(':')
                    new_numbers.add(p[0])
                logger.debug('new partition numbers: %s' % new_numbers)

                number = new_numbers.difference(old_numbers).pop()

                # TODO: set partition flag?

                device = region['device'] + number
                logger.debug('new partition is %s' % device)

                # this is the device to write content to:
                return device
         
            except subprocess.CalledProcessError as e:
                logger.error('Error with parted')
                logger.error(e.cmd)
                logger.error(e.output)

        else:
            # no suitable region found
            logger.error('No suitable region found!')
            # throw an error
            return ''


service = Service()

class Handler(BaseHTTPRequestHandler):
    """Call method of Service() based on Action field in POST"""
    
    def do_GET(self):
	logger.debug('unsupported GET recieved')

    def do_POST(self):
        # Parse the form data posted
        form = cgi.FieldStorage(
            fp=self.rfile, 
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })

        logger.debug('response received')
        for key, value in [(key, form[key].value) for key in form]:
            logger.debug('  %s: %s' % (key, value))

        # Depending on Action, call method
        # test for Action? # 'Action' in form?
        try:
            action = form['Action'].value
            parms = dict( [(key, form[key].value) for key in form] )

            action_call = getattr(service, action)

            code, response = action_call(**parms)
        except:
            # handle exceptions here...

            code = 500 # Internal Server Error
            response = etree.Element('Response')

            Errors = etree.SubElement(response, 'Errors')
            Error = etree.SubElement(Errors, 'Error')

            StackTrace = etree.SubElement(Error, 'StackTrace')
            StackTrace.text =  traceback.format_exc()
        

        """
        6. Appendix: Error response samples
        Note: In the example StackTrace data is missing decorations for special symbols.
        <?xml version="1.0" encoding="UTF-8"?>
        <Response>
        <Errors>
        <Error>
        <Code>ResourceLimitExceeded</Code>
        <Message>Task failed to initialize - conversion task limit (5) exceeded.</Message>
        <StackTrace>
         Traceback (most recent call last):
          File "F:\cloudscraper\migrate\Migrate\Migrate\Migrator.py", line 114, in runFullScenario
            if self.createSystemTransferTarget() == False:
          File "F:\cloudscraper\migrate\Migrate\Migrate\Migrator.py", line 300, in createSystemTransferTarget
            self.__systemMedia = self.createImageMedia(self.__migrateOptions.getSystemImagePath() , self.__migrateOptions.getSystemImageSize() + self.__additionalMediaSize)
          File "F:\cloudscraper\migrate\Migrate\Migrate\Migrator.py", line 272, in createImageMedia
            media.open()
          File ".\Images\StreamVmdkMedia.py", line 222, in open
            self.__openExisting()
          File ".\Images\StreamVmdkMedia.py", line 685, in __openExisting
            raise VMDKStreamException("File is of wrong format or corrupted")
        VMDKStreamException: File is of wrong format or corrupted 
        </StackTrace>
        </Error>
        </Errors>
        <RequestID>4ea6bfd2-dc65-453e-ae23-7d22b9e50dc8</RequestID>
        </Response>
        """

        # Send response
        self.send_response(code)
        logger.debug('code: %d' % code)

        # need to detect if response is xml or not...
        try:
            xml = etree.tostring(response, 
                                 xml_declaration=True, 
                                encoding = "utf-8")

            logger.debug('response: %s' % xml)
            self.end_headers()
            self.wfile.write(xml)
        except:
            self.send_header('Content-type', 'application/x-gzip')
            self.end_headers()
            self.wfile.write(response)
            logger.debug('response: sending log file')
            
"""
    Errors should contain code, description and error stack trace if any (see appendix below)
     Calls are coming sequentially. No task queues needed. 
     The verb is 'POST'
     No auth (v1)
"""

def main():

    from BaseHTTPServer import HTTPServer
    server = HTTPServer(('0.0.0.0', 80), Handler)
    print 'Starting server, use <Ctrl-C> to stop'
    server.serve_forever()

if __name__ == '__main__':
    main()
