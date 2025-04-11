################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: eeprom.py
# | Date: 2025-02-21
# | Rev: 0.5
# | Change By: R.Crouch
# | ECO Ref: CTF-130
#  ----------------
# | Project Name: AEM Test & Measurement Platform
# | Developer: Robert Crouch
# | File Description: Support class and methods for using I2C EEPROMs, both for GL and for UUTs
#  ----------------
################################################################
################################################################

## COMPONENT USE // EXPECTED INPUT/OUTPUT AND LIMITATIONS // LIBRARY DESIGNED FOR ##
################################################################

## IMPORT FILES ##

from ...Core_Testware.I2C.I2C import I2C
import time

################################################################

## CLASS DEFINITION AND METHODS ##

class eeprom(I2C):
    """
    .. versionadded:: 0.1
    .. versionchanged:: 0.5

    # eeprom

    The eeprom class is used for both internal use on the AEM Test Platform as well as for communicating with EEPROM devices connected to the platform.
    It is intialized with the appropriate I2C address as well as the EEPROM memory size and page size, both in bytes.

    """

    # General Consts.
    CLEAR_BYTE = 0xFF

    def __init__(self, eepromAddress:int, memSizeBytes:int = 0x100, pageSizeBytes:int = 0x01, i2cBusOverride:int = None)->None:
        '''
            .. versionadded:: 0.1
            .. versionchanged:: 0.3

            Initialization of EEPROM instance.
        '''
        if None == i2cBusOverride:
            super().__init__(eepromAddress)
        else:
            super().__init__(eepromAddress, i2cBusOverride)
        self.address = eepromAddress
        self.memSizeBytes = memSizeBytes
        self.pageSizeBytes = pageSizeBytes
        return None

    def __del__(self)->None:
        '''
            .. versionadded:: 0.1
            .. versionchanged:: 0.1

            Clean-up after deleting instatiation.
        '''
        return None

    def _getPageLocation(self,pageNumber:int = 0x00)->int:
        '''
            .. versionadded:: 0.1
            .. versionchanged:: 0.1
            
            Returns the memory location for the requested page, given the EEPROM pagesize.
        '''
        memLocation = 0x00 + (self.pageSizeBytes * pageNumber)
        return memLocation
    
    def _readEEPROMpage(self, pageNumber:int = 0)->list[int]:
        '''
            .. versionadded:: 0.1
            .. versionchanged:: 0.1

            Returns a list of bytes from the requested page number.
        '''
        pageList = self.read(
                self.getMemLocation(pageNumber),
                self.pageSizeBytes
        )   
        return pageList

    def _convertToBytes(self, inputString:str)->list:
        '''
            .. versionadded:: 0.1
            .. versionchanged:: 0.1

            Converts the passed string into a list of bytes.
        '''
        outputBytes = []
        for element in inputString:
            outputBytes.append(ord(element))
        return outputBytes

    def _updateEEPROMpage(self, pageNumber:int = 0, newValue:str = '')->None:
        '''
            .. versionadded:: 0.1
            .. versionchanged:: 0.1

            Write the passed string to a page section. Pads 0x00 to fill in any remaining bytes.
        '''
        if (newValue == '') or (pageNumber > (self.memorySizeBytes / self.pageSizeBytes)):
            return None

        pageValue = newValue
        if len(pageValue) > self.pageSizeBytes:
            pageValue = pageValue[:self.pageSizeBytes]

        charToAdd = self.pageSizeBytes - len(pageValue)
        while(charToAdd):
            pageValue += chr(0x00)
            charToAdd -= 1

        pageList = self._convertToBytes(pageValue)

        self.write(
            self._getPageLocation(pageNumber),
            pageList
        )
        return None

    def _clearPage(self, pageNumber:int = 0)->None:
        '''
            .. versionadded:: 0.1
            .. versionchanged:: 0.1

            Fills the passed page area with the CLEAR_BYTE value.
        '''
        if (pageNumber > (self.memSizeBytes / self.pageSizeBytes)):
            return None
        memLocation = self._getPageLocation(pageNumber)

        clearByteList = []
        for i in range(self.pageSizeBytes):
            clearByteList.append(self.CLEAR_BYTE)

        self.write(
            memLocation,
            clearByteList
        )
        return None
        
    def _clearAll(self)->None:
        '''
            .. versionadded:: 0.1
            .. versionchanged:: 0.1

            Fills the entire EEPROM memory with the CLEAR_BYTE value.
        '''
        memLocation = 0x00
        while memLocation <= self.memSizeBytes:
            self.write(
                memLocation,
                self.CLEAR_BYTE
            )
            memLocation += 0x01
            time.sleep(0.01)
        return None
    
    def _writeAll(self, newValue:bytes)->None:
        '''
            .. versionadded:: 0.2
            .. versionchanged:: 0.3

            Write the passed bytes to the EEPROM, filling any remaining space with CLEAR_BYTEs.
        '''
        memLocation = 0x00
        for i in newValue:
            self.write(
                memLocation,
                i
            )
            memLocation += 0x01
            time.sleep(0.01)

        for i in range(memLocation, self.memSizeBytes):
            self.write(
                i,
                self.CLEAR_BYTE
            )
            time.sleep(0.01)
        return None
    
################################################################

## OTHER CODE ##
################################################################

# EOF