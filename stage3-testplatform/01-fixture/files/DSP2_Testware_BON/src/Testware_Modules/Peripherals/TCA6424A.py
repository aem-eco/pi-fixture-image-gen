################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: TCA6424A.py
# | Date: 2025-03-24
# | Rev: 1.0
# | Change By: R.Crouch
# | ECO Ref: CTF-78
#  ----------------
# | Project Name: AEM_Testware
# | Developer:
# | File Description: Class for TCA6424A GPIO Expander
#  ----------------
################################################################
################################################################

## COMPONENT USE // EXPECTED INPUT/OUTPUT AND LIMITATIONS // LIBRARY DESIGNED FOR ##

################################################################
# Developed for use in test fixtures utilizing the Goldilocks testbed.
# Pass the chips I2C address, GPIO channel and signal direction.
# Allows setting the channel/pin by the passed state as a bool and reading of channels/pins as a bool.

## IMPORT FILES ##
from ...Core_Testware.I2C.I2C import I2C

from typing import List
import time

################################################################

## CLASS DEFINITION AND METHODS ##

################################################################
class TCA6424AHandler(I2C):                                                                # Digital I/O
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    :extends: I2C

    # TCA6424 - I2C GPIO Expander
    """

    EXPECTED_RETURN_SIZE_BYTES: int = 1
    EXPECTED_DEVICE_PROCESSING_TIME: float = 0.001

    GOLD_DIO_A_ADDRESS: int = 34
    GOLD_DIO_B_ADDRESS: int = 35

    DIO_A_1: int    = 0
    DIO_A_2: int    = 1
    DIO_A_3: int    = 2
    DIO_A_4: int    = 3
    DIO_A_5: int    = 4
    DIO_A_6: int    = 5
    DIO_A_7: int    = 6
    DIO_A_8: int    = 7
    DIO_A_9: int    = 10
    DIO_A_10: int   = 11
    DIO_A_11: int   = 12
    DIO_A_12: int   = 13
    DIO_A_13: int   = 14
    DIO_A_14: int   = 15
    DIO_A_15: int   = 16
    DIO_A_16: int   = 17
    DIO_A_17: int   = 20
    DIO_A_18: int   = 21
    DIO_A_19: int   = 22
    DIO_A_20: int   = 23
    DIO_A_21: int   = 24
    DIO_A_22: int   = 25

    DIO_B_1: int    = 0
    DIO_B_2: int    = 1
    DIO_B_3: int    = 2
    DIO_B_4: int    = 3
    DIO_B_5: int    = 4
    DIO_B_6: int    = 5
    DIO_B_7: int    = 6
    DIO_B_8: int    = 7
    DIO_B_9: int    = 10
    DIO_B_10: int   = 11
    DIO_B_11: int   = 12
    DIO_B_12: int   = 13
    DIO_B_13: int   = 14
    DIO_B_14: int   = 15
    DIO_B_15: int   = 16
    DIO_B_16: int   = 17
    DIO_B_17: int   = 20
    DIO_B_18: int   = 21
    DIO_B_19: int   = 22
    DIO_B_20: int   = 23
    DIO_B_21: int   = 24
    DIO_B_22: int   = 25

    # Goldilocks Rev 1 & 2
    n_Reset_UART_AB: int = 27       # RESERVED INTERNAL DIOA
    n_Reset_UART_CD: int = 26       # RESERVED INTERNAL DIOA

    n_Reset_UART_GH: int = 27       # RESERVED INTERNAL DIOB
    n_Reset_UART_EF: int = 26       # RESERVED INTERNAL DIOB

    # Goldilocks Rev A
    
    
    def __init__(self, address, pinOutputList:List[str]|None=None) -> None:
        self.hexAddress = address

        super().__init__(address, 1)

        # Set internal lines to OUTPUT and set HIGH
        if address == self.GOLD_DIO_A_ADDRESS:
            self.uartLines:List[str] = ["n_Reset_UART_AB", "n_Reset_UART_CD"]
        elif address == self.GOLD_DIO_B_ADDRESS:
            self.uartLines:List[str] = ["n_Reset_UART_EF", "n_Reset_UART_GH"]

        for uart in self.uartLines:
            self.setPinDirection(uart, True)
            self.writePin(uart, True)

        # User configurable output list, defualt reset state is input
        # so only if output, set them as such
        for pin, state in pinOutputList:
            self.setPinDirection(pin, True)
            self.writePin(pin, state)

        self.resetUARTics()

        # TODO - determine HW revision GL

        return None
    

    def resetUARTics(self) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        ## Reset Goldilocks UARTs
        Uses the lines reserved for internal use to pull-down the RESET lines for the UARTS.
        Waits 2 seconds between changing state on each.
        """

        for uart in self.uartLines:
            self.writePin(uart, False)
            time.sleep(2)
            self.writePin(uart, True)

        return None
    

    def _getPinInt(self, pinName:str) -> int:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        ## [Internal] Get the Pin Number from String
        """
        
        pin: int = -1

        pin = getattr(self, pinName)

        return pin
    

    def setPinDirection(self, pin:str, output:bool=True, rxedFromThread:str|None=None) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param pin: The net name of the control line (ex. DIO_A_1) as a string.
        :param output: Weather to set the pin as an output or input (true or false).
        :param rxedFromThread: A throwaway variable to drop extra arguments when being called from another process.

        # Set Pins Input/Output
        """

        pinInt: int = self._getPinInt(pin)

        self.getPortLocations(pinInt)
        current = self.read(
            0x0C + self.registerOffset,
            1
        )[0]

        if output:
            newPinDirectionConfig = current & ~(self.pinMask)
        else:
            newPinDirectionConfig = current | self.pinMask

        self.write(
            0x0C + self.registerOffset,
            [newPinDirectionConfig]
        )

        return None


    def getPortLocations(self, signalChannel:int) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param signalChannel: The numerical refernce to the pin being used.

        For a given pin (signalChannel), update the masks for getting and
        setting registeres related to the desired pin.

        This method shall be called by any who requires a R/W operation within this class.
        """
        
        if signalChannel < 8:
            registerOffset = 0x00
            bitPosition = signalChannel
        if 7 < signalChannel < 18:
            registerOffset = 0x01
            bitPosition = signalChannel - 0x0A
        if 18 < signalChannel:
            registerOffset = 0x02
            bitPosition = signalChannel - 0x14

        self.registerOffset = registerOffset
        self.pinMask = 0x01 << bitPosition
        

    def configPinInvert(self, pin:str, polarityInvert:bool) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param pin: The net name of the control line (ex. DIO_A_1) as a string.
        :param polarityInvert: Flag to indicate if the measured state should be inverted (True) or not inverted (False).

        # Configure Inverted Measurement
        """

        pinInt: int = self._getPinInt(pin)

        self.getPortLocations(pinInt)

        currentValue = self.read(
            0x08 + self.registerOffset,
            1
        )[0]

        if polarityInvert:
            newPolarityRegister = currentValue ^ self.pinMask
        else: 
            newPolarityRegister = currentValue & ~(self.pinMask)

        self.write(
            0x08 + self.registerOffset,
            [newPolarityRegister]
        )

        return None


    def writePin(self, pin:str, pinSetHigh:bool, rxedFromThread:str|None=None) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param pin: The net name of the control line (ex. DIO_A_1) as a string.
        :param pinSetHigh: The logic state of the passed pin, LL HIGH (true) or LL LOW (false).
        :param rxedFromThread: A throwaway variable to drop extra arguments when being called from another process.

        # Set Pin State
        """

        pinInt: int = self._getPinInt(pin)

        self.getPortLocations(pinInt)
        currentState = self.read(
            0x00 + self.registerOffset,
            1
        )[0]

        if pinSetHigh:
            newOutputRegister = currentState | self.pinMask
        else:
            newOutputRegister = currentState & ~(self.pinMask)

        self.write(
            0x04 + self.registerOffset,
            [newOutputRegister]
        )

        return None


    def readPin(self, pin:str, rxedFromThread:str|None=None) -> bool:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param pin: The net name of the control line (ex. DIO_A_1) as a string.
        :param rxedFromThread: A throwaway variable to drop extra arguments when being called from another process.

        # Read Pin State
        """

        pinInt: int = self._getPinInt(pin)
        
        self.getPortLocations(pinInt)

        portState = self.read(
            0x00 + self.registerOffset,
            1
        )[0]

        if (0 < pinInt < 10): pinState = portState & pow(2,(pinInt))
        elif (9 < pinInt < 18): pinState = portState & pow(2,(pinInt-10))
        elif (19 < pinInt < 28): pinState = portState & pow(2,(pinInt-20))

        if pinState != 0:
            return True
        else:
            return False

## OTHER CODE ##

################################################################

# EOF