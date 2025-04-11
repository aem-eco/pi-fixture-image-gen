################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: DModule2C6657i.py
# | Date: 2025-04-03
# | Rev: 1.0
# | Change By: Everly Larche
# | ECO Ref: LXP-421
#  ----------------
# | Project Name: LxDSP2
# | Developer: Everly Larche
# | File Description: To handle the pre/post-processing of serial information from the connected DSP module during FW upload
#  ----------------
################################################################
################################################################

## IMPORT FILES ##
from src.Testware_Modules.Utilities.USB_UART_INTEL_HEX import INTEL_HEX
from src.Core_Testware.UnitUnderTest.UUT import UUT, subUUT, miscInfo
from src.Core_Testware.TestSteps.testStepDecoder import payload
from src.TestwareConstants import THREAD_CARRY_METHOD, MAIN_THREAD_NAME, THREAD_METHOD, DUMMY_PLAYLOAD_DELIVER_TO

from serial.tools import list_ports, list_ports_common
from serial import Serial, PARITY_EVEN, PARITY_MARK, PARITY_NONE, PARITY_ODD, PARITY_SPACE
from typing import Tuple, List
import time, regex

################################################################

## CLASS DEFINITION AND METHODS ##
class DModule2C6657i_FW_Upload:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    # DSP Module Firmware Uploading
    """

    DEFUALT_ENCODING:str = "UTF-8"

    SETUP_UTIL_PROMPT:str           = '> '
    PROGRAMMING_SUCCESS_MESSAGE:str = "done, no errors"
    UPLOAD_INTEL_HEX_PROMPT:str     = "enter <i> for Intel-hex program upload"
    UPLOAD_READY_MESSAGE:str        = "ready to receive Intel-hex file"

    LX_BOOT_VALID_IMAGE:regex.Pattern       = regex.compile(".*Valid\simage\sfound\sat\sflash\s.+location.*")
    LX_BOOT_VALID_IMAGE_SEQ:regex.Pattern   = regex.compile(".*Using\sflash\s.+location")
    LX_BOOT_APP_START:regex.Pattern         = regex.compile(".*BOOTING\sIN\sPROGRESS.*")
    LX_BOOT_AD_CONFIG_START:regex.Pattern   = regex.compile(".*AD25M16\sconfiguration\sbegin.*")
    LX_BOOT_AD_CONFIG_END:regex.Pattern     = regex.compile(".*AD25M16\sconfiguration\send.*")
    LX_BOOT_AD_SP_START:regex.Pattern       = regex.compile(".*Signal-Processing\sstarted.*")

    LX_CLEAR_SCREEN:regex.Pattern = regex.compile(".*\[2J.*")    # based on ANSI clear conosle command

    LX_CMD_GET_MAC:str  = "n\n"
    LX_CMD_SET_SN:str   = "S"
    LX_CMD_GET_SN:str   = "s"

    USB_PID:int = 0x6015
    USB_VID:int = 0x403

    DSP_SERIAL_BAUD:int     = 115200
    DSP_SERIAL_PARITY:str   = PARITY_NONE
    DSP_SERIAL_BYTESIZE:int = 8
    DSP_SERIAL_STOPBITS:int = 1


    def __init__(self, bootloaderPath:str, applicationPath:str):
        self.blPATH:str = bootloaderPath
        self.appPATH:str = applicationPath
        return None
    

    def _connectToUnit(self) -> None:
        """
        ..versionadded:: 1.0
        ..versionchanged:: 1.0
        """

        _targetPort = None

        avaliablePorts:List[list_ports_common.ListPortInfo] = list_ports.comports()
        for port in avaliablePorts:
            if self.USB_PID == port.pid and self.USB_VID == port.vid:
                _targetPort = port.device

        if None == _targetPort: raise ConnectionAbortedError(f"No valid port found from obejcts matching:\nPID/VID --> {self.USB_PID}/{self.USB_VID}.\nIs the device connected or powered on?")

        self.deviceConnection:Serial = Serial(
            port        = _targetPort,
            baudrate    = self.DSP_SERIAL_BAUD,
            bytesize    = self.DSP_SERIAL_BYTESIZE,
            parity      = self.DSP_SERIAL_PARITY,
            stopbits    = self.DSP_SERIAL_STOPBITS,
            timeout     = 1.0,
            rtscts      =False
        )

        return None
    

    def checkSetupUtilEntered(self, timeoutSeconds:float=60.0) -> bool:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param timeoutSeconds: A float for how long in seconds we should wait for the setup util to show. Defualt is 1 min.

        :returns bool:

        ## Setup Util Check
        Checks to see if we have now entered the D.Module2 setup function for FW upload.
        This is achieved by looking at the end of the latest serial data to find a `> ` prompt.
        """

        self._connectToUnit()

        _hasEnteredIntoSetupUtil:bool = False
        _startTime:float = time.time()

        _breakCondition:bool = False
        while not _breakCondition:
            if timeoutSeconds < (time.time()-_startTime): _breakCondition = True
            response = self.deviceConnection.readall().decode(self.DEFUALT_ENCODING, "ignore") # Take the last two decoded characters and see if they match the CMD prompt
            if self.SETUP_UTIL_PROMPT in response[-2:]:
                _hasEnteredIntoSetupUtil = True
                _breakCondition = True

        self.deviceConnection.flush()
        return _hasEnteredIntoSetupUtil
    

    def getBoardInformation(self) -> Tuple[str, payload]:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :returns Tuple[str, payload]:

        """

        _serialNumber:str = ""
        _hardwareRev:str = ""
        _BIOSVersion:str = ""

        _writeBuffer:bytes = bytes("i\r\n", self.DEFUALT_ENCODING)
        _retCode:int|None = self.deviceConnection.write(_writeBuffer)
        if (None == _retCode) or (_retCode < 0): raise BufferError(f"When attempting to write the buffer:{_writeBuffer}, the return code was NULL. Invalid return code!")
        time.sleep(0.1) # Wait

        _data:bytes = self.deviceConnection.read_all()
        if None == _data: raise BufferError(f"Buffer with content:{_data} is not valid!")

        _dataString:str = _data.decode(self.DEFUALT_ENCODING)
        _dataString = _dataString.splitlines()
        for line in _dataString:
            _splitline = line.split(' ')
            _field = _splitline[len(_splitline)-1]

            if "serial number" in line: _serialNumber = _field
            elif "hardware rev" in line: _hardwareRev = _field
            #elif "BIOS firmware rev" in line: _BIOSVersion = _field
            else: pass

        unitToAdd:subUUT = subUUT(
            pn          = "7315.425",
            rev         = _hardwareRev,
            sn          = _serialNumber,
            partType    = "PCBA"
        )

        return (
            THREAD_CARRY_METHOD,
            payload(
                threadName = MAIN_THREAD_NAME,
                action = THREAD_METHOD,
                message = ["addSubUnitToUUT", unitToAdd],
                deliverTo = MAIN_THREAD_NAME
            )
        )
    

    def setupForProgramming(self) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0
        """

        self.hexHandler = INTEL_HEX(
            connectionObject        = self.deviceConnection,
            hardwareFlowRequired    = True
        )

        self.deviceConnection.flush()
        time.sleep(1)

        return None
    

    def _setupTraqairForFileRx(self) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0
        """

        self.deviceConnection.write(b'u')
        time.sleep(1)
        _response:str = self.deviceConnection.readall().decode(self.DEFUALT_ENCODING, "ignore")
        #if self.UPLOAD_INTEL_HEX_PROMPT not in _response: raise RuntimeError(f"Unable to set unit into program mode, please try again")

        self.deviceConnection.write(b'i')
        time.sleep(1)
        _response:str = self.deviceConnection.readall().decode(self.DEFUALT_ENCODING, "ignore")
        #if self.UPLOAD_READY_MESSAGE not in _response: raise RuntimeError(f"Unable to set unit into program mode, please try again")

        return None
    

    def uploadBootloader(self) -> bool:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :returns bool:

        """

        self._setupTraqairForFileRx()
        _retCode:int|str|None = self.hexHandler.upload(self.blPATH)

        _response:bytes = self.deviceConnection.readall()
        _response = _response.decode(self.DEFUALT_ENCODING, "ignore")

        if self.PROGRAMMING_SUCCESS_MESSAGE in _response: return True
        else: return False
    

    def uploadApplication(self) -> bool:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :returns bool:

        """

        self._setupTraqairForFileRx()
        _retCode:int|str|None = self.hexHandler.upload(self.appPATH, disableFC=True)

        _response:bytes = self.deviceConnection.readall()
        _response = _response.decode(self.DEFUALT_ENCODING, "ignore")

        if self.PROGRAMMING_SUCCESS_MESSAGE in _response: return True
        else: return False


    def monitorBootProcess(self, timeout:float=60.0) -> bool:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        ## Monitor DSP Bootloader Initialization
        The following checks are done here to validate FW upload completed and
        the hardware is functioning.
        1. FW image flag set
        2. FW image is valid and found at location `x`
        3. CRC image check passes
        """

        _startTime:float = time.time()

        # Comments indicate required final condition to pass
        _booted:bool = False                # True
        _validImageFound:bool = False       # True
        _ImageStarting:bool = False         # True
        _clearScreenCount:int = 0           # <= 2
        _wasWatchdogTripped:bool = False    # False - Indicates uninstalled/bad AD
        _AD25M16configStart:bool = False    # True
        _AD25M16configEnd:bool = False      # True
        _signalProcessStarted:bool = False  # True

        _breakCondition:bool = False
        while not _breakCondition:

            if (time.time()-_startTime) >= timeout:
                _breakCondition = True
                break
            else:
                pass

            if _validImageFound and _ImageStarting and not _wasWatchdogTripped and _AD25M16configStart and _AD25M16configEnd and _signalProcessStarted:
                _breakCondition = True
                _booted = True
                break
            else:
                pass

            _currLine:str = self.deviceConnection.readline().decode(self.DEFUALT_ENCODING, "ignore")

            if not _wasWatchdogTripped and (None != regex.match(self.LX_CLEAR_SCREEN, _currLine)):
                _clearScreenCount += 1
                continue # ignore the first clear console
            elif not _wasWatchdogTripped and (None != regex.match(self.LX_CLEAR_SCREEN, _currLine)) and _clearScreenCount > 2:
                _wasWatchdogTripped = True # Got the clear cmd a second time before getting the FW lines
            elif _wasWatchdogTripped:
                _breakCondition = True
            else:
                pass

            if None != regex.match(self.LX_BOOT_VALID_IMAGE, _currLine):
                _validImageFound = True
            elif None != regex.match(self.LX_BOOT_VALID_IMAGE_SEQ, _currLine):
                _validImageFound = True
            elif None != regex.match(self.LX_BOOT_APP_START, _currLine):
                _ImageStarting = True
            elif None != regex.match(self.LX_BOOT_AD_CONFIG_START, _currLine):
                _AD25M16configStart = True
            elif None != regex.match(self.LX_BOOT_AD_CONFIG_END, _currLine):
                _AD25M16configEnd = True
            elif None != regex.match(self.LX_BOOT_AD_SP_START, _currLine):
                _signalProcessStarted = True
            else:
                continue

        return _booted
    

    def getMACaddress(self) -> str:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0
        """

        _macString:str = ""
        self.deviceConnection.readall() # dump current

        self.deviceConnection.write(bytes(self.LX_CMD_GET_MAC, self.DEFUALT_ENCODING))
        time.sleep(0.5)
        _reponse:str = self.deviceConnection.readall().decode(self.DEFUALT_ENCODING, "ignore")

        for line in _reponse.splitlines():
            if "MAC address" in line:
                _macString = line.split(":", 1)[1][1:]   # Split the field name and field data, then on the data, remove leading space

        _info:miscInfo = miscInfo(
            description = "MAC Address",
            text = _macString,
            typedef = None,
            numeric = None
        )

        # ONLY AVALIABLE DURING RUNTIME
        if callable(self.txMessage):
            self.txMessage((
                THREAD_CARRY_METHOD,
                payload(
                    threadName = MAIN_THREAD_NAME,
                    action = THREAD_METHOD,
                    message = ["addMiscInfoToUUT", _info],
                    deliverTo = MAIN_THREAD_NAME
                )
            ))
            time.sleep(2.5)

        return _macString
    

    def setAEMsn(self, UUTInfo:UUT|None=None, rxedFromThread:str|None=None) -> bool:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0
        """

        self.aemSN = UUTInfo.serialNumber
        _sn = self.aemSN.replace('-', '')

        # set with this sn

        self.deviceConnection.readall() # dump current
        self.deviceConnection.write(bytes(self.LX_CMD_SET_SN, self.DEFUALT_ENCODING))
        time.sleep(0.5)
        self.deviceConnection.write(bytes(_sn, self.DEFUALT_ENCODING))

        return None
    

    def verifyAEMsn(self) -> bool:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0
        """

        _snMatched:bool = False

        self.deviceConnection.readall() # dump current
        self.deviceConnection.write(bytes(self.LX_CMD_GET_SN, self.DEFUALT_ENCODING))
        time.sleep(0.5)
        _reponse:str = self.deviceConnection.readall().decode(self.DEFUALT_ENCODING, "ignore")

        _sn:str = _reponse.split(' ')[4][:-1] # Remove <LF>
        _sn = _sn.replace(':', '-') # Convert back to dash as in barcode

        if _sn == self.aemSN: _snMatched = True

        return _snMatched

################################################################

## OTHER CODE ##

################################################################

# EOF