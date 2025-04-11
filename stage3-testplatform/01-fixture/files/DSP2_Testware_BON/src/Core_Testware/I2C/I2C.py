################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: I2C.py
# | Date: 2024-10-28
# | Rev: 1
# | Change By: Everly Larche
# | ECO Ref:
#  ----------------
# | Project Name: AEM Test & Measurement Platform
# | Developer: Everly Larche
# | File Description: Master I2C bus handler
#  ----------------
################################################################
################################################################

## LIBRARY USE // EXPECTED INPUT/OUTPUT AND LIMITATIONS ##

################################################################

## SUBCOMPONENT IMPORTS ##
import os, time
from fcntl import ioctl
from typing import List
from ctypes import c_char

################################################################

## CLASS DEFINITION AND METHODS ##
class I2C:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    # Python I2C Linux Driver
    A basic user-space lniux I2C bus driver using `ioctl` and constants found in the `i2c-dev.h` file in Torvols/linux.

    This class is acceptable to use in situations where timming or response time is not absolutly critical. Pythons overhead will become an issue in
    high-speed, time-critical situations. In cases such as these use the Testware C-based drivers.
    """

    # CONSTS #
    I2C_RDWR: int    = 0x0707
    """
    IOCTL mode as per linux/i2c-dev.h
    """

    I2C_SLAVE: int   = 0x0703
    """
    IOCTL command as per linux/i2c-dev.h
    """


    def __init__(self, address:int, i2c_bus:int) -> None:
        self.devAddress: int = address
        self.bus: int = i2c_bus
        return None


    def _open(self) -> int:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :internal: Yes
        :returns Int: File-descriptor of the I2C bus file object

        Opens and returns the I2C FD for use in other function.
        """

        fd: int = os.open(f"/dev/i2c-{self.bus}", os.O_RDWR)
        if fd < 0: raise IOError(f"Unable to open: /dev/i2c-{self.bus}")

        return fd


    def _close(self, fd:int) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :internal: Yes
        :param fd: Int of file-descriptor to be closed (release resource back to system).
        """

        os.close(fd)
        
        return None
    

    def _setIOCTLslave(self, fd) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :internal: Yes.
        :param fd: The file-descriptor of the I2C file/bus to be actioned upon.

        Prepares IOCTL to communicate with an I2C slave device.
        """


        _ret:int = ioctl(fd, self.I2C_SLAVE, self.devAddress)
        if _ret < 0: raise IOError(f"Unable to select address:{self.devAddress}, using ioctl, got error code:{_ret} expected 0!")

        return None


    def write(self, register:int, byteList:list|None) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :internal: No
        :param register: Int/byte of the slave register to be used
        :param byteList: The byte or sequence of bytes to be written to the slave register.

        :raises IOError: When the returned code from `os.write()` is less than 1 (should be the number of bytes written to the file)

        Writes a byte or sequence of bytes to a I2C bus FD using `os.write()`.
        """

        register = int(register)

        fd: int = self._open()
        self._setIOCTLslave(fd)

        if None != byteList:
            _totalSequence:list = [register] + byteList # Put the register as the first byte to write to the dev
        else:
            _totalSequence:list = [register]            # Only writing the register we want to use, likely if a subsequent read call is pending

        _ret: int = os.write(fd, bytearray(_totalSequence))
        if _ret < 0: raise IOError(f"Unable to write to the address:{self.devAddress} with data:{bytearray(_totalSequence)}, got return code:{_ret}, expected 0!")

        self._close(fd)

        return None


    def read(self, register:int|None, length:int, decode:bool=False, readDelay:float|None=None) -> list|str:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :internal: No
        :param register: Int/byte of the slave register to be used
        :param length: The number of bytes to be read (min is 1)
        :param decode: Boolean to decode into `utf-8` string from data
        :param readDelay: The delay between setting up the slave device by writting the register to the bus and reading data from the device. Set to `None` to skip.

        :raises IOError: When the returned code from `os.write()` is less than 1 (should be the number of bytes read from the file)

        Reads a number of bytes from a I2C slave register after writing the register to the salve device.
        """

        if 0 == length: raise ValueError(f"Not allowed to read a length of zero!")

        if None != register: self.write(register, None)    # Write the register to the device, this will set us up for a read operation
        
        if None != readDelay: time.sleep(readDelay)
        fd: int = self._open()
        self._setIOCTLslave(fd)
        data:bytes = os.read(fd, length)

        intData:list = []
        for byte in data:
            intData.append(int(byte))

        if decode:
            return self.decodeUnicode(data)
        
        self._close(fd)

        return intData
    

    def generateEolchars(self, eolTerminator:str) -> tuple:
        '''
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param eolTerminator:

        Given a string, this method returns a tuple containing:
        - A list of integers representing the end-of-line string for comparison with raw data sent from a periferial
        - A count of how many c_characters are being looked for

        This is used by read() for detecting when it has found the end of the expected data.
        '''

        eolc_chars:list = []
        for c_character in eolTerminator:
            eolc_chars.append(ord(c_character))
        eolLen:int = len(eolc_chars)

        return (eolc_chars, eolLen)


    def decodec_characters(self, rawData:List[c_char]) -> str:
        '''
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param rawData: A list of `c_char` variables to be decoded into `UTF-8` string.

        Taking in a list of integers representing unicode c_characters, return the constructed string representation of the data.
        '''
        
        decodedString: str = ""

        for block in rawData:
            if isinstance(block, int):
                block = [block]
            for c_character in block:
                decodedString += chr(c_character)

        return decodedString