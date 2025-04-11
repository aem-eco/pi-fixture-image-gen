################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: DAC7573.py
# | Date:2025-03-24
# | Rev: 1.0
# | Change By: Everly Larche
# | ECO Ref: CTF-121
#  ----------------
# | Project Name: AEM Test & Measurement Platform
# | Developer: Everly Larche
# | File Description: Support class and methods to use the inetgrated DACs on the Goldilocks platform/testbed
#  ----------------
################################################################
################################################################

## IMPORT FILES ##
from ...Core_Testware.I2C.I2C import I2C

from typing import List

################################################################

## CLASS DEFINITION AND METHODS ##
class DAC7573(I2C):
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    # DAC7573

    ## Control Register Message Format
    MSB -- A3,A2,L1,L2,Sel1,Sel0,PD0 -- LSB

    | Bit Name | Description |
    | -------- | ----------- |
    | A3 | Extended Address Bit |
    | A2 | Extended Address Bit |
    | L1 & L2 | Load bits (Mode Select) |
    | --> 00 | Store I2C data. The contents of MS-BYTE and LS-BYTE (or power down information) are stored in the temporary register of a selected channel. This mode does not change the DAC output of the selected channel |
    | --> 01 | Update selected DAC with I2C data. Most commonly utilized mode. The contents of MS-BYTE and LS-BYTE (or power down information) are stored in the temporary register and in the DAC register of the selected channel. This mode changes the DAC output of the selected channel with the new data. |
    | --> 10 | 4-Channel synchronous update. The contents of MS-BYTE and LS-BYTE (or power down information) are stored in the temporary register and in the DAC register of the selected channel. Simultaneously, the other three channels get updated with previously stored data from the temporary register. This mode updates all four channels together. |
    | --> 11 | Broadcast update mode. This mode has two functions. In broadcast mode, DAC7573 responds regardless of local address matching, and channel selection becomes irrelevant as all channels update. This mode is intended to enable up to 64 channels simultaneous update, if used with the I2C broadcast address (1001 0000). |
    | Sel1 & Sel0 | Channel select bits.
    | --> 00 | Channel A |
    | --> 01 | Channel B |
    | --> 10 | Channel C |
    | --> 11 | Channel D |
    | PD0 | Power Down Flag |
    | --> 0 | Normal operation. |
    | --> 1 | Power down. |

    ## Control Byte Data
    MSB -- MSB[7..0],LSB[7..0] -- LSB
    | Bit Name | Description |
    | -------- | ----------- |
    | MSB7..0 | Consists of eight most significant bits of 12-bit unsigned binary D/A conversion data. |
    | LSB7..4 | Consists of the 4 least significant bits of the 12-bit unsigned binary D/A conversion data. |
    | LSB3..0 | Don't care bits. |

    .. WARNING:: Only the Update mode (L1,L2 --> 01) is implimented. None of the other update modes are available.
    """

    MAX_ALLOWED_ERROR: float = 0.02
    """
    % Error allowed in measurements.
    """


    NUM_STEPS_TOTAL: int = 4096
    """
    The number of output positions in the DAC.
    """

    REFERENCE_VOLTAGE: float = 4.096
    """
    Attached reference voltage in voltd DC.
    """


    EXTENDED_ADDRESS_BITS: int = 0x00
    MODE_SELECT_UPDATE_BITS: int = 0x10
    CHANNEL_SELECT_BITS_A: int = 0x00
    CHANNEL_SELECT_BITS_B: int = 0x02
    CHANNEL_SELECT_BITS_C: int = 0x04
    CHANNEL_SELECT_BITS_D: int = 0x06
    POWER_DOWN_FLAG_DISABLE: int = 0x00
    POWER_DOWN_FLAG_ENABLE: int = 0x01

    # DAC Control Bytes
    CRTL_BYTE_UPDATE_A: int = EXTENDED_ADDRESS_BITS + MODE_SELECT_UPDATE_BITS + CHANNEL_SELECT_BITS_A + POWER_DOWN_FLAG_DISABLE
    CTRL_BYTE_UPDATE_B: int = EXTENDED_ADDRESS_BITS + MODE_SELECT_UPDATE_BITS + CHANNEL_SELECT_BITS_B + POWER_DOWN_FLAG_DISABLE
    CTRL_BYTE_UPDATE_C: int = EXTENDED_ADDRESS_BITS + MODE_SELECT_UPDATE_BITS + CHANNEL_SELECT_BITS_C + POWER_DOWN_FLAG_DISABLE
    CTRL_BYTE_UPDATE_D: int = EXTENDED_ADDRESS_BITS + MODE_SELECT_UPDATE_BITS + CHANNEL_SELECT_BITS_D + POWER_DOWN_FLAG_DISABLE


    def __init__(self, dacAddress:int, i2cBusOverride:int=None) -> None:
        # init the I2C class and its params that are given from the DAC7573 constructor args
        if None == i2cBusOverride:
            super().__init__(dacAddress, 1)
        else:
            super().__init__(dacAddress, i2cBusOverride)

        return None
    

    def _checkValidDAC(self, dac:int) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param dac: The selected DAC from 0-3 representing DAC A-D.
        :returns None:
        :raises IndexError: When dac is outside the valid range of 0-3.

        Checks DAC selection within valid range.
        """

        if 3 < dac < 0:
            raise IndexError(f"Selected DAC of {dac} is outside the range 0-3 representing DACs A,B,C,D!")

        return None


    def _stepsToVolts(self, currentSteps:int) -> float:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param currentSteps:
        :returns float:
        """

        return float(currentSteps)*(self.REFERENCE_VOLTAGE/float(self.NUM_STEPS_TOTAL))


    def _voltsToSteps(self, voltageSetPoint:float) -> List[int]:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param voltageSetPoint: The desired voltage from 0.0V - 4.096V DC.
        :returns tuple: The number of steps required to reach the setpoint parameter as a 12-bit unsigned binary number split into two bytes.
        :raises ValueError: When the selected output voltage is outside the valid range.
        """

        if  self.REFERENCE_VOLTAGE < voltageSetPoint < 0.0:
            raise ValueError(f"Desired DAC setpointof {voltageSetPoint} is outside the valid range of 0.0-4.096!")

        stepCountCalulated: int = int(round((voltageSetPoint/self.REFERENCE_VOLTAGE) * self.NUM_STEPS_TOTAL, 0))

        # Creates the 4 dont care bits at the end of the 12-bit sequence
        stepCountCalulated = stepCountCalulated << 4

        # Splits into MSB and LSB after data has been shifted by 4 bits
        msb: int = (stepCountCalulated & 0xFF00) >> 8 # Bring back down to valid range
        lsb: int = (stepCountCalulated & 0x00F0)

        return [msb, lsb]
    

    def _calculateError(self, voltageSetPoint:float, setPointSteps:int) -> float:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param voltageSetPoint: The desired voltage from 0.0V - 4.096V DC.
        :param setPointSteps: The calculated number of steps to reach near the desired voltage setpoint.
        :returns float: The calculated error in % 0.0 - 1.0. To be used in comparison expect blocks as the tolerance argument.
        """

        if 0 == voltageSetPoint: return 0.0

        correctedVoltage:float = self._stepsToVolts(setPointSteps)
        error:float = (correctedVoltage/voltageSetPoint)*100

        if error > self.MAX_ALLOWED_ERROR:
            # TODO
            pass
            #raise ArithmeticError(f"The error between the desired voltage and calculated step voltage is greater than the allowed {self.MAX_ALLOWED_ERROR}% ({error}%)")

        return error
    

    def setDAC(self, dac:str, setValue:float, rxedFromThread:str|None=None) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param dac: The selected DAC from A-D.
        :param setValue: The floating point value in VDC that is desired on the selected DAC.
        :returns float: The % err from desired voltage.

        .. NOTE:: The allowed voltage range on any of the four DACs is `0.0-4.096V`.
        """

        selectedDAC: int = 0

        if dac.islower(): dac = dac.capitalize()

        match dac:
            case "A":
                selectedDAC = self.CRTL_BYTE_UPDATE_A

            case "B":
                selectedDAC = self.CTRL_BYTE_UPDATE_B

            case "C":
                selectedDAC = self.CTRL_BYTE_UPDATE_C

            case "D":
                selectedDAC = self.CTRL_BYTE_UPDATE_D

            case _:
                raise IndexError(f"Invalid DAC selection of: {dac}. Valid range is A-D, or a-d only.")

        setValueSteps:List[int] = self._voltsToSteps(setValue)
        self._calculateError(setValue, sum(setValueSteps))

        self.write(
            selectedDAC,
            setValueSteps
        )

        return

################################################################

## OTHER CODE ##

################################################################

# EOF