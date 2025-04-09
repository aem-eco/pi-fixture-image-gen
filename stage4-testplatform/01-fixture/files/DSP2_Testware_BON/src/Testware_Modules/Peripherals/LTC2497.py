################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: LTC2497.py
# | Date: 2024-10-16
# | Rev: 1
# | Change By: R.Crouch
# | ECO Ref: CTF-78
#  ----------------
# | Project Name: AEM_Testware
# | Developer: Everly Larche
# | File Description: Class for LTC2497 ADC
#  ----------------
################################################################
################################################################

## COMPONENT USE // EXPECTED INPUT/OUTPUT AND LIMITATIONS // LIBRARY DESIGNED FOR ##
# Developed for use in test fixtures utilizing the Goldilocks testbed.
# Used for measuring the analog signal on a particular ADC channel.
# Requires a handle to the I2C bus, a I2C hex address, ADC channel, Signal Type and Polarity.
# Returns the measurement as an int (counts).
# Needs to add conversion to an analog unit. 

################################################################

## IMPORT FILES ##
from src.Core_Testware.I2C.I2C import I2C

import time
from typing import List

################################################################

## CLASS DEFINITION AND METHODS ##

################################################################
class LTC2497(I2C):
    """
    
    """

    GOLD_ADC_A_SE_1:int     = 0
    GOLD_ADC_A_SE_2:int     = 1
    GOLD_ADC_A_SE_3:int     = 2
    GOLD_ADC_A_SE_4:int     = 3
    GOLD_ADC_A_SE_5:int     = 4
    GOLD_ADC_A_SE_6:int     = 5
    GOLD_ADC_A_SE_7:int     = 6
    GOLD_ADC_A_SE_8:int     = 7
    GOLD_ADC_A_SE_9:int     = 8
    GOLD_ADC_A_SE_10:int    = 9
    GOLD_ADC_A_SE_11:int    = 10
    GOLD_ADC_A_SE_12:int    = 11
    GOLD_ADC_A_SE_13:int    = 12
    GOLD_ADC_A_SE_14:int    = 13
    GOLD_ADC_A_SE_15:int    = 14
    GOLD_ADC_A_SE_16:int    = 15

    GOLD_ADC_B_DIFF_14:int  = 13    # SE
    """
    Used as single-ended in HW
    """

    GOLD_ADC_B_DIFF_15:int  = 14    # SE
    """
    Used as single-ended in HW
    """

    GOLD_ADC_B_DIFF_16:int  = 15    # SE
    """
    Used as single-ended in HW
    """


    HW_SELECTION_SE:str = "Single-Ended"
    HW_SELECTION_SE_ADDRESS:int = 20

    HW_SELECTION_DIFF:str = "Differential"
    HW_SELECTION_DIFF_ADDRESS:int = 22


    VOLTAGE_STEP_SIZE:float = 4.096/65535.0


    def __init__(self,address:int) -> None:
        super().__init__(address, 1)

        if address == LTC2497.HW_SELECTION_SE_ADDRESS:
            self.hardwareSelection:str = LTC2497.HW_SELECTION_SE
        elif address == LTC2497.HW_SELECTION_DIFF_ADDRESS:
            self.hardwareSelection:str = LTC2497.HW_SELECTION_DIFF
        else:
            raise ValueError("Incorrect I2C address, unknown device config")

        self.polarity:bool = False

        return None
    

    def setPolarityFlag(self, inverted:bool) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param inverted: Flag to switch the polarity of the measurement.
        """

        if inverted:
            self.polarity = True
        else:
            self.polarity = False

        return None


    def getADCAddress(self, pin:str, signalType:str) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param pin: The net name of the ADC channel to be used.
        :param signalType: Denotes single ended or differential measurement type.
        """

        pinInt:int = getattr(self, pin)

        if pinInt in [self.GOLD_ADC_A_SE_13, self.GOLD_ADC_A_SE_14, self.GOLD_ADC_A_SE_15, self.GOLD_ADC_A_SE_16]:
            signalType = self.HW_SELECTION_SE

        diffMaskTablePos = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        seMaskTable = [0x10, 0x18, 0x11, 0x19, 0x12, 0x1A, 0x13, 0x1B, 0x14, 0x1C, 0x15, 0x1D, 0x16, 0x1E, 0x17, 0x1F]

        if (self.HW_SELECTION_DIFF == signalType) and self.HW_SELECTION_DIFF_ADDRESS:
            self.muxAddr = diffMaskTablePos[pinInt]
            if self.polarity:
                self.muxAddr += 0x08
        else:
            self.muxAddr = seMaskTable[pinInt]

        self.muxAddr += 0xA0

        return None


    def parseResult(self,response:List[int], overrideScale:float|None=None)->float:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param response: The byte array or list of ints containing the I2C data.
        :param overrideScale: If applicable, the override scale caluclated and placed in the test step.

        :returns float: The ADC value scaled.

        :raises OverflowError: When the measured voltage is outside the valid range of the ADC.
        """

        if response[0] == 0xC0:
            raise OverflowError("ADC returned error: Vin >= Vref/2!")

        if (response[0] & 0x80) == 0x80:                                        # Check if response indicates a negative number
            isNegative = False
        else:
            isNegative = True

        calcVal = 0
        calcVal = calcVal + ((response[0] & 0x3F) << 16)
        calcVal = calcVal + (response[1] << 8)
        calcVal = calcVal + (response[2] & 0xB0)
        calcVal = calcVal >> 6

        result = calcVal
        if isNegative:                                                          # If the flag was negative, multiply by -1
            result = result * -1

        if None == overrideScale:
            result = result * self.VOLTAGE_STEP_SIZE
        else:
            result = result * self.VOLTAGE_STEP_SIZE * overrideScale

        if None == result: result = 0.0 # should only keep to get F7 line running and stable - normally this would be an error but tests should still fail

        return result


    def measureSignal(self, pin:str, measureInverted:bool=False, overrideScale:float|None=None, rxedFromThread:str|None=None) -> float:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param pin: The net name of the ADC channel used for the measurement.
        :param measureInverted: Flag to denote if the reference should be changed in the measurement (differential) or if the sign should be inverted.
        :param overrideScale: The scalar applied to the normal output of the `parseResult()` function. Calucated ahead of time and placed in the test step.
        :param rxedFromThread: A throw away argument. When receiving a command from another process that is not the main process, the arguments contain which processes sent the request in case the data should be returned to it from here or the receiver needs to know where it came from.

        :returns float: The measured voltage from the ADC scaled if appliable.
        """

        time.sleep(0.15) # This is required and I dont remeber why, so dont take it out, it will break :)

        self.setPolarityFlag(measureInverted)
        self.getADCAddress(pin, self.hardwareSelection)

        self.write(
            self.muxAddr,
            None
        )

        time.sleep(0.16) # Datasheet conversion time is 149.9 mS max; using 160mS

        finalRawData = self.read(
                None, # are we putting the mux address from here?
                3
            )[:3]

        if None != overrideScale:
            value = self.parseResult(finalRawData, overrideScale)
        else:
            value = self.parseResult(finalRawData)

        return value

## OTHER CODE ##

################################################################

# EOF