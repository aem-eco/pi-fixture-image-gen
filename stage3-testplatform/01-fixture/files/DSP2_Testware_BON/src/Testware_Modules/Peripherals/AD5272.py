################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: AD5272.py
# | Date: 2024-12-27
# | Rev: 1.0
# | Change By: Everly Larche
# | ECO Ref: CTF-121
#  ----------------
# | Project Name: AEM_Testware
# | Developer: R.Crouch
# | File Description: Class for Analog Devices AD5272 Digipot
#  ----------------
################################################################
################################################################

## LIBRARY USE // EXPECTED INPUT/OUTPUT AND LIMITATIONS ##

################################################################

# Library Use:  Creating an object to interact with a AD5272 Digipot via I2C
# Inputs:       I2C Bus handle, I2C Address, Digipot Maximum Value
# Outputs:      AD5272 object with support methods
# Limitations:  AD5272 only (does not support AD5274)
#               Wiper memory is not implemented

## SUBCOMPONENT IMPORTS ##
from ...Core_Testware.I2C.I2C import I2C

from typing import List, Tuple, Dict

################################################################

## CLASS DEFINITION AND METHODS ##

################################################################
class CombinedDigipots:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    .. WARNING:: This class is only designed for use on the 7315.500 test platform Revsision 2 and above.

    # Goldilocks AD5272 Set
    Implimentation of multiple AD5272 objects to combine as needed, for the required resistances.
    """

    GOLD_DIGIPOT_A_NAME: str = "A"
    GOLD_DIGIPOT_B_NAME: str = "B"
    GOLD_DIGIPOT_C_NAME: str = "C"

    MAX_RESISTOR_NETWORK_VALUE: int = 250000
    MIN_RESISTOR_NETWORK_VALUE: int = 0

    def __init__(self, addresses:List[int], maxTotalResistance:int=250000) -> None:
        self.checkMaxDesiredOhms(maxTotalResistance)

        if 3 != len(addresses):
            raise ValueError(f"The number of addresses in {addresses} is too short or too long. Expected 3 got {len(addresses)}")

        self.GOLD_DIGIPOT_A_ADDRESS: int = addresses[0]
        self.GOLD_DIGIPOT_B_ADDRESS: int = addresses[1]
        self.GOLD_DIGIPOT_C_ADDRESS: int = addresses[2]

        # Control of all pots required to read correct resistance
        pots:tuple = (
            (self.GOLD_DIGIPOT_A_ADDRESS, 50000, self.GOLD_DIGIPOT_A_NAME),
            (self.GOLD_DIGIPOT_B_ADDRESS, 100000, self.GOLD_DIGIPOT_B_NAME),
            (self.GOLD_DIGIPOT_C_ADDRESS, 100000, self.GOLD_DIGIPOT_C_NAME)
        )

        self.maxNetworkOhms:float = maxTotalResistance
        self.activeDigipots:Dict[AD5272] = {}

        for address, maxOhms, name in pots:
            self.activeDigipots[name] = (
                AD5272(address, maxOhms)
            )

        self.updateResistanceNetwork(0.0)

        return
    

    def checkMaxDesiredOhms(self, maxOhms:int) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param maxOhms: The max possible resistance required.

        :returns None:

        :raises ValueError: When the max resistance is outside the valid range (0-250kOhms)
        """

        if self.MAX_RESISTOR_NETWORK_VALUE < maxOhms < self.MIN_RESISTOR_NETWORK_VALUE:
            raise ValueError(f"The requested max resistance range of {maxOhms} is invalid. The accepted range is between {self.MIN_RESISTOR_NETWORK_VALUE}-{self.MAX_RESISTOR_NETWORK_VALUE}kOhms.")

        return None
    

    def enableOutput(self) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        Enganges all wipers of Digipots A, B, and C.
        """

        for digipotHandler in self.activeDigipots:
            pass #TODO

        return None
    

    def disableOutput(self) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        Disengages all wipers of Digipots A, B, and C.
        """

        for digipotHandler in self.activeDigipots:
            digipotHandler.setResistance(0.0)
            # TODO

        return None
    

    def updateResistanceNetwork(self, newResistance:float, rxedFromThread:str|None=None) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        .. WARNING:: Do not use a new value that is higher than your defined highest resistance. Doing so will raise an error. If a higher resistance is needed, it should be defined at setup.

        :param newResistance: The new value that will be written directly to the output of the digipot network if valid.

        :returns None:

        :raises ValueError: When a value which is higher than the defined maxNetworkResistance is passed as the param.

        Using the classwide maxNetworkResistance to remeber what the valid range is that we are working with, update the applicable digipots to obtain the desired output value.

        ## Split Resistance Breakdown
        | Output Range | Digipots Set Above 0Ohms | % Allocation |
        | ------------ | ------------------------ | ------------ |
        | `0 - 50kOhms` | Digipot A | `100%` |
        | `50k - 100kOhms` | Digipot B | `100%` |
        | `100k - 150kOhms` | Digipot A, Digipot B | Digipot A `0-33.33%`, Digipot B `66.66%` (FIXED) |
        | `150k - 200kOhms` | Digipot A, Digipot, B, Digipot C | Digipot A `0-25%`, Digipot B `50%` (FIXED), Digipot C `25%` (FIXED) |
        | `200k - 250kOhms` | Digipot A, Digipot B, Digipot C | Digipot A `0-20%`, Digipot B `40%` (FIXED), Digipot C `40%` (FIXED) |
        """

        if self.maxNetworkOhms < newResistance: raise ValueError(f"The desired setpoint {newResistance}Ohms is greater than the configured max of {self.maxNetworkOhms}Ohms!")

        if newResistance <= 50000.0:
            digipotAhandle:AD5272 = self.activeDigipots.get(self.GOLD_DIGIPOT_A_NAME)
            digipotAhandle.setResistance(newResistance)

            digipotAhandle:AD5272 = self.activeDigipots.get(self.GOLD_DIGIPOT_B_NAME)
            digipotAhandle.setResistance(0.0)

            digipotAhandle:AD5272 = self.activeDigipots.get(self.GOLD_DIGIPOT_C_NAME)
            digipotAhandle.setResistance(0.0)

        elif 50000.0 < newResistance <= 100000.0:
            digipotAhandle:AD5272 = self.activeDigipots.get(self.GOLD_DIGIPOT_B_NAME)
            digipotAhandle.setResistance(newResistance-50000.0)

            digipotAhandle:AD5272 = self.activeDigipots.get(self.GOLD_DIGIPOT_A_NAME)
            digipotAhandle.setResistance(50000.0)

            digipotAhandle:AD5272 = self.activeDigipots.get(self.GOLD_DIGIPOT_C_NAME)
            digipotAhandle.setResistance(0.0)

        elif 100000.0 < newResistance <= 150000.0:
            digipotAhandle:AD5272 = self.activeDigipots.get(self.GOLD_DIGIPOT_A_NAME)
            digipotAhandle.setResistance(newResistance - 100000.0)

            digipotAhandle:AD5272 = self.activeDigipots.get(self.GOLD_DIGIPOT_B_NAME)
            digipotAhandle.setResistance(100000.0)

            digipotAhandle:AD5272 = self.activeDigipots.get(self.GOLD_DIGIPOT_C_NAME)
            digipotAhandle.setResistance(0.0)

        elif 150000.0 < newResistance <= 200000:
            digipotAhandle:AD5272 = self.activeDigipots.get(self.GOLD_DIGIPOT_A_NAME)
            digipotAhandle.setResistance(newResistance - 150000)

            digipotAhandle:AD5272 = self.activeDigipots.get(self.GOLD_DIGIPOT_B_NAME)
            digipotAhandle.setResistance(100000)

            digipotAhandle:AD5272 = self.activeDigipots.get(self.GOLD_DIGIPOT_C_NAME)
            digipotAhandle.setResistance(50000)

        elif 200000 < newResistance <= 250000:
            digipotAhandle:AD5272 = self.activeDigipots.get(self.GOLD_DIGIPOT_A_NAME)
            digipotAhandle.setResistance(newResistance - 200000)

            digipotAhandle:AD5272 = self.activeDigipots.get(self.GOLD_DIGIPOT_B_NAME)
            digipotAhandle.setResistance(100000.0)

            digipotAhandle:AD5272 = self.activeDigipots.get(self.GOLD_DIGIPOT_C_NAME)
            digipotAhandle.setResistance(100000.0)

        else:
            raise ValueError(f"The desired max resistance value of {self.maxNetworkOhms} does not fit into one of the valid ranges!")

        return None
    

class AD5272(I2C):
    """
    .. vserionadded:: 1.0
    .. versionchanged:: 1.0

    # AD5272
    The primary class of the inddividual digipots to be combined into another class.
    """

    START_RESISTANCE:float = 0.0
    START_SHUTDOWN_MODE: bool = True

    # Command Bytes
    COMMAND_WRITE_DIRECT_RDAC: int         = 0x01
    COMMAND_READ_RDAC: int                 = 0x02
    COMMAND_WRITE_CONTROL: int             = 0x07

    # Control Register Bytes
    CONTROL_REGISTER_DISABLE_WRITE_PROTEC: int = 0x03


    def __init__(self, i2cAddress:int, maxResistance:int) -> None:

        self.maxResistance = maxResistance

        super().__init__(i2cAddress, 1)

        self._disableWriteProtection()

        return None
    

    def _generateCombinedBytes(self, commandByte:int, dataBytes:List[int]) -> Tuple[int]:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param commandByte: The command or register to send to the device.
        :param dataBytes: The value of the resistance to set.

        :returns Tuple: Immutable list of ints to be sent to the device.

        0 0 C3 C2 C1 C0 D9 D8 || D7 .. D0
        -- "register" byte -- || "data" byte
        """

        # Sift the C data up by two bits and add the two msbits of the data
        registerByte:int = (commandByte << 2) + (dataBytes[0] & 0x03)
        setValueByte:int = dataBytes[1]

        return (registerByte, setValueByte)


    def _disableWriteProtection(self) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0
        """

        hexValues:Tuple[int] = self._generateCombinedBytes(
            commandByte = self.COMMAND_WRITE_CONTROL,
            dataBytes = [0x00, self.CONTROL_REGISTER_DISABLE_WRITE_PROTEC]
        )

        self.write(
            hexValues[0],
            [hexValues[1]]
        )

        return None
    

    def _writeRDAC(self, dataBytes:List[int]) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param dataBytes: The list of bytes to be sent to the device's RDAC register.
        """

        hexValues:Tuple[int] = self._generateCombinedBytes(
            commandByte = self.COMMAND_WRITE_DIRECT_RDAC,
            dataBytes = dataBytes
        )

        self.write(
            hexValues[0],
            [hexValues[1]]
        )

        return None


    def setResistance(self,resistanceValue:float) -> float:
        '''
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param resistanceValue: The desired setpoint resistance in Ohms.
        :returns float: The calculated likely resistance.
        '''

        if 0 == resistanceValue:
            rdacValue = 0
            calcResistance = 0

        else:
            rdacValue = int((resistanceValue / self.maxResistance) * 1023)
            calcResistance = (rdacValue / 1023) * self.maxResistance

            if (calcResistance/resistanceValue) > 0.02:
                pass
                #print(f"Difference for POTS is: {calcResistance/resistanceValue}%")
                #raise ArithmeticError(f"The requested resistance of {resistanceValue} is more than 2% out from the nearest step level of {calcResistance}!")

        rdacMSB = (rdacValue & 0xFF00) >> 8
        rdacLSB = (rdacValue & 0x00FF)

        self._writeRDAC([rdacMSB, rdacLSB])

        return calcResistance
    

    def getResistance(self) -> float:
        '''
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :returns float: The current calculated resistance from the digipot.
        '''

        currentRDAC = self.readRDAC() # TODO
        rValue = (currentRDAC/1024) * self.maxResistance
        
        return rValue

## OTHER CODE ##

################################################################

# EOF