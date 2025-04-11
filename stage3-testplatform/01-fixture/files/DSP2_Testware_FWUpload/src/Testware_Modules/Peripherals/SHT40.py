################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: SHT40.py
# | Date: 2025-03-05
# | Rev: 1.0
# | Change By: Everly Larche
# | ECO Ref: LXP-364
#  ----------------
# | Project Name: LxDSP2.0 Bed-of-Nails
# | Developer: Everly Larche
# | File Description: Device driver for I2C device on UUT
#  ----------------
################################################################
################################################################

## IMPORT FILES ##
from src.Core_Testware.I2C.I2C import I2C
#from src.Core_Testware.Tools.CRC import CRC # Left out for basic implimentation

from typing import List

################################################################

## CLASS DEFINITION AND METHODS ##
class SHT40(I2C):
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    :peripheral_Type: EXTERNAL
    :param deviceAddress: The I2C bus 7-bit address in python int format (ex. 0x44)

    # SHT40
    Introduced as part of the DSP2.0 BoN Test Fixture, this class is designed to interface
    with the SHT40-AD1B-R3 and support reading in all the prescision modes + mfg information.

    CRC is supported and enforced.

    Currently this class does not support the use of the heater.
    """

    POLYNOMIAL = 0x31
    """
    The CRC poly as defined in the SHT40 datasheet.
    """

    def __init__(self, deviceAddress:int):
        #self.crcCheck = CRC()
        
        super().__init__(
            address = deviceAddress,
            i2c_bus = 1
        )

        return None


    def __del__(self):
        super().__del__() # Ensures FD is closed in I2C.

        return None


    def getMfgInformation(self) -> str:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :returns: A string containing the 16-bit mfg data (SN)

        ## Get MFG. Information from Device
        # Process flow:
        1. Read 3-bytes from device
            x2 data bytes + 1 CRC byte
        2. Verify CRC, if bad, return '-9999'
        3. Decode the string and return
        """

        command = 0x89
        serialInfo:str = ""

        rawData = self.read(register=command, length=3)
        if not self.crcCheck.decode8(rawData, self.POLYNOMIAL):
            serialInfo = "-9999"
        else:
            serialInfo = self.decode_characters(rawData)

        return serialInfo


    def getTempHum(self, mode:int) -> List[float]:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param mode:

        :returns List:

        :param mode: The required prescision as per datasheet (0 highest - 2 lowest)
        :returns: A list of floats in the order of temperature in deg. C and RH%

        ## Read Current Temp/Hum
        # Process flow:
        1. Determine prescision mode
        2. Read all 6-bytes from the device
           Temp: x2 8-bit + 8-bit CRC
           Hum: x2 8-bit + 8-bit CRC
        3. Shift and add data for the tick count of each measurement
        4. Verify CRC, if invalid, return -9999
        5. Calculate Temp/RH as per datasheet and return
        """
        tempHum:List[float] = []

        match mode:
            case 0:
                command = 0xFD # High-prescision
            case 1:
                command = 0xF6 # Med-prescision
            case 2:
                command = 0xE0 # Low-prescision

        # read 3-bytes per temp/hum
        # temp, temp, crc, hum, hum ,crc
        try:
            rawData = self.read(register=command, length=6, readDelay=0.1)
        except Exception as e:
            return [-9999, -9999]

        tempTicks:int    = (rawData[0] *256) + rawData[1]
        humTicks:int     = (rawData[3] *256) + rawData[4]

        tempHum = [
            -45.0 + 175.0 * tempTicks / 65535.0,
            -6.0 + 125.0 * humTicks /65535.0
        ]

        return tempHum

################################################################

## OTHER CODE ##

################################################################

# EOF