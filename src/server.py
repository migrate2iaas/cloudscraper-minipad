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

    for development there is also a Restart action
    which puts the service back in a initial state.

After that, treat service as unavailable. 
User will create a new VM from the image in case new is needed. 

"""

# --------------------------------------------------------
__author__ = "James Munroe"
__copyright__ = "Copyright (C) 2014 Migrate2Iaas"
# --------------------------------------------------------

import logging
import traceback

import time
import datetime
from BaseHTTPServer import BaseHTTPRequestHandler
import requests
from lxml import etree
import tarfile
import shortuuid
import cgi
import re
import threading
#import psutil # for detecting disk usage
import os
import subprocess
import traceback


import linux
import windows

logger = logging.getLogger('minipad')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
logfilename = '/var/log/minipad.log'
if os.name == 'nt':
    logfilename = './minipad.log'
fh = logging.FileHandler(logfilename)
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
                         'Error',
                         'ReadyToTransfer',
                         'FinishedTransfer',
                         'FinishedConversion']

        self.status = 'NotConfigured'
        self.statusMessage = 'Service not configured'
        self.statusCode = '0'

        self.postprocess = False 

        if os.name == 'nt':
            self.hostInstance = windows.Windows()
        else:
            self.hostInstance = linux.Linux()

        self.restartEvent = threading.Event()
        self.workers = []

    def configure_import(self):
        """ 
        """

        logger.debug('Do the work of configuration')

        self.status = 'Initializing'
        self.statusMessage = 'Setting up for import'
        self.statusCode = '0'

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
        self.ImportManifestUrl = ''
        self.volumeSize = 0

        self.status = 'ReadyToTransfer'
        self.statusMessage = 'Ready to receive transfer request'
        self.statusCode = '0'

        # done
        logger.debug('ConfigureImport complete')

    def Restart(self, **kwargs):
        """
        Restart the service back into the initial unconfigured state

        Stops all worker threads.
        """

        # signal any alive workers to stop
        self.restartEvent.set()
        while len(self.workers) > 0:
            worker = self.workers.pop()

            # wait for worker to complete
            if worker.isAlive():
                worker.join()

        self.restartEvent.clear()

        self.status = 'NotConfigured'
        self.statusMessage = 'Service not configured'
        self.statusCode = '0'

        response = etree.Element("RestartResult")
        result = etree.SubElement(response, 'Result')
        result.text = "True"

        code = 200
        return (code, response)

    def ConfigureImport(self, 
                        SameDriveMode=None, 
                        UseBuiltInStorage=None,
                        Postproccess=None,
                        **kwargs):
        """Configure the appliance"""

        logger.debug('ConfigureImport called')

        response = etree.Element('Response')
        code = 500 # Server Error
        Errors = etree.SubElement(response, 'Errors')

        if self.status <> 'NotConfigured':
            logger.error('AlreadyConfigured')

            Error = etree.SubElement(Errors, 'Error')
            Code = etree.SubElement(Error, 'Code')
            Code.text = 'AlreadyConfigured'
            Message = etree.SubElement(Error, 'Message')
            Message.text = 'Import already configured'

            self.status = 'Error'
            self.statusMessage = Message.text
            self.statusCode = Code.text

            return (code, response)

        #Postprocess: if enable postprocess after ImportInstance is done
        self.postprocess = False
        if Postproccess == 'True':
            self.postprocess = True

        # SameDriveMode 
        # Switch to deploy the image to the system disk.
        if SameDriveMode == 'True':
            self.SameDriveMode = True
        elif SameDriveMode == 'False':
            self.SameDriveMode = False
        else:
            logger.debug('SameDriveMode missing or wrong value')
            code = 400

            Error = etree.SubElement(Errors, 'Error')
            Code = etree.SubElement(Error, 'Code')
            Code.text = 'BadSameDriveMode'
            Message = etree.SubElement(Error, 'Message')
            Message.text = 'SameDriveMode missing or wrong value'

            self.status = 'Error'
            self.statusMessage = Message.text
            self.statusCode = Code.text

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

            Error = etree.SubElement(Errors, 'Error')
            Code = etree.SubElement(Error, 'Code')
            Code.text = 'BadUseBuiltInStorage'
            Message = etree.SubElement(Error, 'Message')
            Message.text = 'BuiltInStorage missing or wrong value'

            self.status = 'Error'
            self.statusMessage = Message.text
            self.statusCode = Code.text

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

        self.workers.append(worker)

        worker.start()

        
        response = etree.Element("ConfigureImportResult")
        result = etree.SubElement(response, 'Result')
        result.text = "True"

        code = 200
        return (code, response)


    def GetImportTargetStatus(self, **kwargs):
        """Queries the target appliance status"""


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

        logger.debug('GetImportTargetStatus called')

        response = etree.Element("ImportTargetStatus")
        status = etree.SubElement(response, 'Status')
        status.text = self.status

        StatusMessage = etree.SubElement(response, 'StatusMessage')
        StatusMessage.text = self.statusMessage

        StatusCode = etree.SubElement(response, 'StatusCode')
        StatusCode.text = str(self.statusCode)

        return (200, response)

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
        self.workers.append(worker)
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
        self.ImportManifestUrl = kwargs['Image.ImportManifestUrl']
        self.ImportType = 'ImportVolume'

        # launch thread to go import volume
        worker = threading.Thread(target=self.handle_import,
                                  args=())
        self.workers.append(worker)
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

            ImportManifestUrl = etree.SubElement(image, 'importManifest')
            ImportManifestUrl.text = self.ImportManifestUrl

            volume = etree.SubElement(item, 'volume')
            size = etree.SubElement(volume, 'size')
            size.text = str(self.volumeSize)

            state = etree.SubElement(item, 'state')
            state.text = self.status

            statusMessage = etree.SubElement(item, 'statusMessage')
            statusMessage.text = self.statusMessage

        logger.debug('DescribeConversionTasks called')

        return (200, response)


    def FinalizeConversion(self, InjectDrivers = 'NoDrivers', MakeBoot = "False",
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

            MakeBoot
                Whether to change the default boot from MiniPad OS to the imported one
            Type: String
            Default: False
            Valid values: False|True

        Note: nothing should be done a stub for now.
        !NOTE: Drivers are injected in handle_import in postprocess function
        Here we just reset the boot options. 
        """
        
        logger.debug('FinalizeConversion called')

        # should probably throw an error if the conversion is still
        # in progress
        self.Status = 'Finalizing'

        error = False
        try:
            if MakeBoot=="True":
                self.hostInstance.setBootDisk()
        except Exception as ex:
            self.statusMessage = str(ex)
            self.Status = 'FinalizationFailed'
            self.statusCode = 500
            logger.error("Failed to finalize: " + str(ex));
            error = True

        if not error:
            self.statusCode = 200
            # When FinalizeConversion is complete.
            self.Status = 'FinishedConversion'

        response = etree.Element('Response')
        
        return (self.statusCode, response)

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
        try:
	        # parts are described in XML manifest. 
	        # XML manifest URL is passed via ImportInstance \ ImportVolume request.
	        # XML should be downloaded via URL and parsed. 
	        # XML contains list of URLs to image parts. 
	        logger.debug('downloading manifest')
	        
	        url = self.ImportManifestUrl
	        logger.debug(url)
	
	        r = requests.get(url , verify=False)
	        xml = r.content
	
	        manifest = etree.fromstring(xml)
	        import_ = manifest.find('import')
	        if not import_ :
                        # then it's kinda error
	        	logger.error("!!!ERROR: Cannot get the manifest in " + manifest.tag + " response")
	        	logger.debug(str(xml));
                        # should seek for AWS error here - it's mostly possible
	        	aws_error = manifest.find('Message')
	        	message = "Unknown Reason"
	        	if aws_error is not None:
	        		message = aws_error.text
	        	raise IOError("Bad Manifest: " + message)
	        # Size is in bytes
	        size = import_.find('size').text
	
	        # Volume is in GB
	        self.volumeSize = float(import_.find('volume-size').text)
	
	        # number of parts
	        parts = import_.find('parts')
	        count = parts.get('count')
	
	        # 2.2 Find a disk/volume in the system
	        device = self.GetDisk()

	        logging.info("Writing to device: " + device)
	
	        if device == '/dev/null':
	            # no device found
	            self.status = 'Error'
	            self.statusMessage = 'No available device/volume found'
	            self.statusCode = '405'
	
	            return
	
	        handle = open(device, 'r+b')
	
	        self.status = 'ReadyToTransfer'
	        self.statusMessage = 'Downloading'
	        self.statusCode = '0'
	
	        for part in parts.findall('part'):
	            
	            if self.restartEvent.isSet():
	                # stop early since restart has been signalled
	                break;
	
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
	            # TODO: move it to parms
                    tries = 0
                    retries = 5
                    while True:
                        try:
                            tries = tries + 1
                            r = requests.get(get_url , verify=False)
                            break
                        except Exception as e:
                            logger.warning("Download failed: " + str(e))
                            logger.debug("Attempt " + str(tries) + " of " + str(retries) + " failed");
                            if tries < retries:
                                time.sleep(5)
                                continue
                            else:
                                raise e
	            logger.debug('Downloaded %d bytes (expected %d bytes) at offset %d' % (len(r.content), end-start, start))
                    if not (r.status_code == 200):
                        logger.error("Failed to download part")
                        logger.debug(str(r.content))
                        r.raise_for_status()
	            # write to appropriate volume
	            handle.seek(start)
	            handle.write(r.content)
                    # calculate percent downloaded
                    self.statusMessage = 'Downloading '\
                                         + str(int((float(self.bytesConverted)/float(size))*100)) + \
                                         "%";
	
	            self.bytesConverted += (end-start)
	
	        # Every part of conversion task should be logged, 
	        # the current step and its status should be accessible via 
	        # DescribeConversionTasks command.
	        handle.close()
	        self.statusMessage = 'Downloaded'
	        self.statusCode = '0'
        except Exception as e:	
            self.status = "Error"
            self.statusMessage = "Error while downloading: " + str(e)
            self.statusCode = '500'
            logger.error("!!!ERROR: Exception while downloading: " + str(e) + "")
            logger.error(traceback.format_exc())
            return

        try:
            if self.postprocess and self.ImportType == 'ImportInstance':
                self.statusMessage = 'Postprocessing'
                self.hostInstance.postprocess(device)

	    self.status = 'FinishedTransfer'
	except Exception as e:
            self.status = "Error"
            self.statusMessage = "Error while postprocessing: " + str(e)
            self.statusCode = '500'
            logger.error("!!!ERROR: Exception while downloading: " + str(e) + "")
            logger.error(traceback.format_exc())
            return


        

    def GetDisk(self):
        """
        Find a block device with sufficient free space 

        use lsblk to deteck disks
        """

        logger.debug('GetDisk called')
        logger.debug('SameDriveMode: %s' % self.SameDriveMode)

        #2.2.1 If SameDriveMode was passed in ConfigureImport request, 
        # and ImportInstance command is being processed, partition the 
        # free space on the system drive
        
        if self.SameDriveMode and self.ImportType == 'ImportInstance':

            # what drive is the root system on?

            rootdev = self.hostInstance.getSystemDriveName()
            partition = self.hostInstance.createPrimaryPartition(rootdev)
            device = partition

            #TODO: set flag to skip part of disk data, should make it configurable

        else:
            # get list of all disks/volumes on system
            # find an appropriate free disk 
            # (criteria - size should be equal to "volume-size" in 
            # GBs set in the manifest) in the system. Note, disks are
            # added into the system dynamically.

            # Typical output from lsblk -r
            """
            NAME MAJ:MIN RM SIZE RO TYPE MOUNTPOINT
            xvda 202:0 0 3G 0 disk 
            xvda1 202:1 0 2.5G 0 part /
            xvda2 202:2 0 1K 0 part 
            xvda5 202:5 0 509M 0 part [SWAP]
            xvdf 202:80 0 20G 0 disk 
            xvdf1 202:81 0 19.1G 0 part 
            """
           

            logger.debug('Looking for disk of size %s' % (self.volumeSize*1024*1024))
            device = self.hostInstance.findDiskBySize(self.volumeSize*1024*1024*1024)
            

            


        logger.debug("Using device " + device)

        return device


service = Service()

class Handler(BaseHTTPRequestHandler):
    """Call method of Service() based on Action field in POST"""
    
    def do_GET(self):
	self.send_response(200)
	self.send_header('Content-type', 'plain/text')
	self.end_headers()
	self.wfile.write("Cloudscraper minipad target ready")
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


#sudo sed -i -e 's/archive.ubuntu.com\|security.ubuntu.com/old-releases.ubuntu.com/g' /etc/apt/sources.list && sudo apt-get update && sudo apt-get -y install gcc python-dev libxml2-dev libxslt-dev git python-setuptools zlib1g-dev && sudo easy_install pip && sudo pip install lxml && sudo pip install shortuuid && sudo pip install psutil && git clone https://git.assembla.com/cloudscraper.minpad.git
