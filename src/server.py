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

sample_manifest =  """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<manifest>
    <version>2010-11-15</version>
    <file-format>VHD</file-format>
    <importer>
        <name>ec2-upload-disk-image</name>
        <version>1.0.0</version>
        <release>2010-11-15</release>
    </importer>
    <self-destruct-url>https://feoff3vm.s3.amazonaws.com/testmanifest.xml?AWSAccessKeyId=AKIAIY2X62QVIHOPEFEQ&amp;Expires=1362428650&amp;Signature=zdgn78E99Wuhi%2FZF%2F99jjwcBOF0%3D</self-destruct-url>
    <import>
        <size>1765801984</size>
        <volume-size>20</volume-size>
        <parts count="169">
            <part index="0">
                <byte-range end="10485759" start="0"/>
                <key>test.part100500</key>
                <head-url>https://feoff3vm.s3.amazonaws.com/test.part0?AWSAccessKeyId=AKIAIY2X62QVIHOPEFEQ&amp;Expires=1362428650&amp;Signature=RwwzYCXjREZiUbDnuZqQreY%2B2Jc%3D</head-url>
                <get-url>https://feoff3vm.s3.amazonaws.com/test.part0?AWSAccessKeyId=AKIAIY2X62QVIHOPEFEQ&amp;Expires=1362428650&amp;Signature=Gjh0vtUBjN%2FNOAYTfqqTPyBN4kE%3D</get-url>
                <delete-url>https://feoff3vm.s3.amazonaws.com/test.part0?AWSAccessKeyId=AKIAIY2X62QVIHOPEFEQ&amp;Expires=1362428650&amp;Signature=Q03co7PVLjlNTqirk6cz7C1k5ps%3D</delete-url>
            </part>

<!--cut to reduce the space-->

            <part index="167">
                <byte-range end="1761607679" start="1751121920"/>
                <key>test.part167</key>
                <head-url>https://feoff3vm.s3.amazonaws.com/test.part167?AWSAccessKeyId=AKIAIY2X62QVIHOPEFEQ&amp;Expires=1362428650&amp;Signature=NDJm1eXefw00YmHGio9AFP9M5h0%3D</head-url>
                <get-url>https://feoff3vm.s3.amazonaws.com/test.part167?AWSAccessKeyId=AKIAIY2X62QVIHOPEFEQ&amp;Expires=1362428650&amp;Signature=GZizd7Oiff2bmHo3Jeq74truSp0%3D</get-url>
                <delete-url>https://feoff3vm.s3.amazonaws.com/test.part167?AWSAccessKeyId=AKIAIY2X62QVIHOPEFEQ&amp;Expires=1362428650&amp;Signature=ietgYBHS05F7J66V1zOS%2BCHEB%2Bo%3D</delete-url>
            </part>
            <part index="168">
                <byte-range end="1765801983" start="1761607680"/>
                <key>test.part168</key>
                <head-url>https://feoff3vm.s3.amazonaws.com/test.part168?AWSAccessKeyId=AKIAIY2X62QVIHOPEFEQ&amp;Expires=1362428650&amp;Signature=tqW%2FTkpE7UvS%2FbXx5fZmUf%2B2tLw%3D</head-url>
                <get-url>https://feoff3vm.s3.amazonaws.com/test.part168?AWSAccessKeyId=AKIAIY2X62QVIHOPEFEQ&amp;Expires=1362428650&amp;Signature=pzt8Zndp5zJ2ZYyujx7sgIe%2FvQo%3D</get-url>
                <delete-url>https://feoff3vm.s3.amazonaws.com/test.part168?AWSAccessKeyId=AKIAIY2X62QVIHOPEFEQ&amp;Expires=1362428650&amp;Signature=l28q3mQwhq3RLnFEf2CvG0eFU6Y%3D</delete-url>
            </part>
        </parts>
    </import>
</manifest>
"""

import logging
import time
from BaseHTTPServer import BaseHTTPRequestHandler
import requests
from lxml import etree
import cgi
import threading

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',)

class Service(object):
    """the web service"""

    def __init__(self):
        """inits service"""

        logging.debug('Web Service initialized')

        self.Statuses = ['NotConfigured',
                         'Initializing',
                         'ReadyToTransfer',
                         'FinishedTransfer',
                         'FinishedConversion']
        self.Status = 'NotConfigured'
                         
        self.Log = []

    def configure_import(self):
        """ """

        logging.debug('Do the work of configuration')

        # how do I return a error??

        # do some work
        for i in range(5):
            logging.info('Working ...')
            time.sleep(1)

        # done
        logging.debug('ConfigureImport complete')
        self.Status = 'ReadyToTransfer'

    def ConfigureImport(self, 
                        SameDriveMode=None, 
                        UseBuiltInStorage=None,
                        **kwargs):
        """Preconfigure the appliance"""

        logging.debug('ConfigureImport called')

        response = etree.Element('Response')
        code = 500 # Server Error
        Errors = etree.SubElement(response, 'Errors')

        if self.Status <> 'NotConfigured':
            logging.error('AlreadyConfigured')

            error = "AlreadyConfigured"

            return (code, response)

        # SameDriveMode 
        # Switch to deploy the image to the system disk.
        if SameDriveMode == 'True':
            self.SameDriveMode = True
        elif SameDriveMode == 'False':
            self.SameDriveMode = False
        else:
            logging.debug('SameDriveMode missing or wrong value')
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
            logging.debug('UseBuiltInStorage or wrong value')
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

        self.Status = 'Initializing'

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

        logging.debug('GetImportTargetStatus called')

        response = etree.Element("ImportTargetStatus")
        Status = etree.SubElement(response, 'Status')
        Status.text = self.Status

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
        logging.debug('ImportInstance called')
        logging.debug('parms: %s' % kwargs)

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
        logging.debug('ImportVolume called')

        # put something on a queue for processing

        response = etree.Element('Response')

        return (200, response)

    def DescribeConversionTasks(self, **kwargs):
        """
        Get info on conversion tasks (both volume and instance)

        See:
        http://docs.aws.amazon.com/AWSEC2/latest/APIReference/ApiReference-query-DescribeConversionTasks.html 
        """
        response = etree.Element('DescribeConversionTasksResponse')
        conversionTasks = etree.SubElement(response, 'conversionTasks')
        
        # loop?
        item = etree.SubElement(conversionTasks, 'item')
        conversionTaskId = etree.SubElement(item, 'conversionTaskId')
        conversionTaskId = 'import-vol-ffhnobo8'
        expriationTime = etree.SubElement(item, 'expriationTime')
        expriationTime = '2014-08-11T10:16:50Z'
        importVolume = etree.SubElement(item, 'importVolume')

        """
            <bytesConverted>0</bytesConverted>
                    <availabilityZone>us-east-1a</availabilityZone>
                    <description>cloudscraper2014-08-04</description>
                    <image>
                        <format>VMDK</format>
                        <size>292352</size>
                        <importManifestUrl>https://cloudscraper-1407147346-us-east-1.s3.amazonaws.com/12312RCF2-Jmanifest.xml?Signature=ViK6rfYTLfghuip0u0IQ5bdmNLg%3D&amp;Expires=1408443410&amp;AWSAccessKeyId=AKIAIY2X62QVIHOPEFEQ</importManifestUrl>
                    </image>
                    <volume>
                        <size>1</size>
                    </volume>
        """
         
        state = etree.SubElement(item, 'state')
        state.text = 'active'
        statusMessage = etree.SubElement(item, 'statusMessage')
        statusMessage.text = 'Pending'

        logging.debug('DescribeConversionTasks called')

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
        
        logging.debug('FinalizeConversion called')

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
        response = etree.Element('Response')

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
        logging.debug('downloading manifest')
        
        url = self.ImportManifestUrl
        logging.debug(url)

        r = requests.get(url)
        xml = r.content

        # for testing::
        xml = sample_manifest        

        manifest = etree.fromstring(xml)
        import_ = manifest.find('import')
        size = import_.find('size').text
        volume_size = import_.find('volume-size').text
        parts = import_.find('parts')
        count = parts.get('count')

        # 2.2 Find a disk/volume in the system
        # get list of all disks/volumes on system
        # os.

        #2.2.1 If SameDriveMode was passed in ConfigureImport request, 
        # and ImportInstance command is being processed, partition the 
        # free space on the system drive
        if self.SameDriveMode and self.ImportType == 'ImportInstance':
            # partition free space on system drive
            pass
        else:
            # find an appropriate free disk 
            # (criteria - size should be equal to "volume-size" in 
            # GBs set in the manifest) in the system. Note, disks are
            # added into the system dynamically.
            pass

        for part in parts.findall('part'):
            index = int(part.get('index'))
            logging.debug('part index %d' % index)

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

            r = requests.get(get_url)
            print r.raw

            # save it...
            time.sleep(1)
        
        # Every part of conversion task should be logged, 
        # the current step and its status should be accessible via 
        # DescribeConversionTasks command.


service = Service()

class Handler(BaseHTTPRequestHandler):
    """Call method of Service() based on Action field in POST"""
    
    def do_POST(self):
        # Parse the form data posted
        form = cgi.FieldStorage(
            fp=self.rfile, 
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })

        logging.debug('response received')
        for key, value in [(key, form[key].value) for key in form]:
            logging.debug('  %s: %s' % (key, value))

        # Depending on Action, call method
        # test for Action? # 'Action' in form?
        action = form['Action'].value
        parms = dict( [(key, form[key].value) for key in form] )

        # test for Action? hasattr?
        action_call = getattr(service, action)

        code, response = action_call(**parms)

        # or throw exception?
        # handle stack trace here...

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
        xml = etree.tostring(response, xml_declaration=True, 
                encoding = "utf-8")

        logging.debug('code: %d' % code)
        logging.debug('response: %s' % xml)

        self.send_response(code)
        self.end_headers()
        self.wfile.write(xml)

"""
    # PYMOTW cglt or something -- just after/after BaseHTTPServer
    # might have this funcationality

    Errors should contain code, description and error stack trace if any (see appendix below)
     Calls are coming sequentially. No task queues needed. 
     The verb is 'POST'
     No auth (v1)
"""

def main():

    from BaseHTTPServer import HTTPServer
    server = HTTPServer(('localhost', 8080), Handler)
    print 'Starting server, use <Ctrl-C> to stop'
    server.serve_forever()

if __name__ == '__main__':
    main()
