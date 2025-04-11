################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: USB_UART_INTEL_HEX.py
# | Date: 2025-04-03
# | Rev: 1.0
# | Change By: Everly Larche
# | ECO Ref: LXP-421
#  ----------------
# | Project Name: LxDSP2
# | Developer: Everly Larche
# | File Description: TO handle the generic uploading and downloading of intel hex firmware files over usb uart connections
#  ----------------
################################################################
################################################################

## IMPORT FILES ##
from os import path, PathLike
from io import BufferedReader
from typing import Dict
import serial, regex

################################################################

## CLASS DEFINITION AND METHODS ##
class INTEL_HEX:
    """
    .. versionadded:: 1.0
    .. versionchanged :: 1.0

    # Intel Hex
    """

    DEFUALT_ENCODING:str = "UTF-8"

    def __init__(self, connectionObject:serial.Serial, hardwareFlowRequired:bool=False, softwareFlowRequired:bool=False) -> None:

        self.connectionSettingCopy:Dict[str, any] = None

        # check the serial object to be valid,
        # re-setup with flow control if required
        if not connectionObject.is_open: raise ConnectionAbortedError(f"")

        if hardwareFlowRequired:
            connectionSettings = connectionObject.get_settings()
            self.connectionSettingCopy = dict(connectionSettings) # Ensure new object in mem
            connectionSettings["rtscts"] = True
            connectionSettings["xonxoff"] = False
            connectionObject.apply_settings(connectionSettings)

        elif softwareFlowRequired:
            connectionSettings = connectionObject.get_settings()
            self.connectionSettingCopy = dict(connectionSettings) # Ensure new object in mem
            connectionSettings["xonxoff"] = True
            connectionSettings["rtscts"] = False
            connectionObject.apply_settings(connectionSettings)

        else:
            pass

        self.targetDevice:serial.Serial = connectionObject

        return None
    

    def _checkValidFile(self, file:BufferedReader) -> bool:
        """
        .. versionadded:: 1.0
        .. versionchanged :: 1.0
        """

        validINTELhex:bool = False
        _stdREGEX: str = ':[0-9A-F]+\\r\\n'
        _regexCOMP:regex.Pattern = regex.compile(_stdREGEX)

        _allLinesValid:bool = True
        for line in file.readlines():
            matched = regex.match(
                pattern = _regexCOMP,
                string = line.decode(self.DEFUALT_ENCODING)
            )
            if matched != None: continue
            else:
                _allLinesValid = False
                break
            
        validINTELhex = _allLinesValid

        return validINTELhex
    

    def _revertSerialSettings(self) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0
        """

        if None != self.connectionSettingCopy:
            self.targetDevice.apply_settings(self.connectionSettingCopy)

        return None


    def upload(self, source:PathLike, disableFC:bool=False) -> str|int|None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0
        """

        returnData:str|int|None = None

        try:
            _file:str = ""
            with open(file = source, mode = 'r') as file:
                for line in file.readlines():
                    _file += line

            #if not self._checkValidFile(_file):
            #    raise BufferError(f"Invalid line in supplied HEX file! Check your file.")
            
            ## NOW READY TO UPLOAD FILE ##
            _returnCode:int|None = self.targetDevice.write(bytes(_file, self.DEFUALT_ENCODING))

        except Exception as e:
            returnData = e.strerror
            self.targetDevice.close()

        finally:
            if disableFC: self._revertSerialSettings()
            return returnData
    

    def download(self, destination:PathLike) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged :: 1.0
        """

        raise NotImplementedError(f"Not implimented for the scope of the required project. Can be added in the future if needed.")

        # get file
        # check valid INTEL HEX

        return None

################################################################

## OTHER CODE ##

################################################################

# EOF