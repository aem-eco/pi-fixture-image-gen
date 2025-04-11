################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: GPIO.py
# | Date: 2025-03-24
# | Rev: 1
# | Change By: Everly Larche
# | ECO Ref:
#  ----------------
# | Project Name: AEM Test & Measurement Platform
# | Developer: Everly Larche
# | File Description: Class for controlling the built-in GPIO of the RPi5
#  ----------------
################################################################
################################################################

## LIBRARY USE // EXPECTED INPUT/OUTPUT AND LIMITATIONS ##

################################################################

## SUBCOMPONENT IMPORTS ##
import gpiod

from typing import Dict, List

################################################################

## CLASS DEFINITION AND METHODS ##
class GPIO:
    '''
    .. versionadded:: 1.0
    .. versionchanged:: 1.0
    '''

    LATEST_GOLDILOCKS_REV:str = "GOLDILOCKS_REV_A"
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    The defualt & latest HW revision to be used by the GPIO controlling class.
    """

    GOLDILOCKS_REV_1_2:Dict[str, List[int]] = {
        "n_Int_UART_EF"              : [4, gpiod.line.Direction.INPUT],     # GPIO04 [INPUT]
        "sbc_n_Int_A"                : [17, gpiod.line.Direction.INPUT],    # GPIO17 [INPUT]
        "n_FAULT_12V_Current_Limit"  : [27, gpiod.line.Direction.INPUT],    # GPIO27 [INPUT]
        "eFuse_5V_OUT_B_FAULT"       : [22, gpiod.line.Direction.INPUT],    # GPIO22 [INPUT]
        "n_EN_5V_OUT_B"              : [5, gpiod.line.Direction.OUTPUT],    # GPIO05 [OUTPUT]
        "eFuse_5V_OUT_A_FAULT"       : [6, gpiod.line.Direction.INPUT],     # GPIO06 [INPUT]
        "n_EN_5V_OUT_A"              : [13, gpiod.line.Direction.OUTPUT],   # GPIO13 [OUTPUT]
        "n_EN_3V3_OUT_B"             : [19, gpiod.line.Direction.OUTPUT],   # GPIO19 [OUTPUT]
        "eFuse_3V3_OUT_B_FAULT"      : [26, gpiod.line.Direction.INPUT],    # GPIO26 [INPUT]
        "n_WRITE_EEPROM"             : [18, gpiod.line.Direction.OUTPUT],   # GPIO18 [OUTPUT]
        "sbc_n_INT_B"                : [23, gpiod.line.Direction.INPUT],    # GPIO23 [INPUT]
        "n_EN_3V3_OUT_A"             : [24, gpiod.line.Direction.OUTPUT],   # GPIO24 [OUTPUT]
        "eFuse_3V3_OUT_A_FAULT"      : [25, gpiod.line.Direction.INPUT],    # GPIO25 [INPUT]
        "n_Int_UART_AB"              : [12, gpiod.line.Direction.INPUT],    # GPIO12 [INPUT]
        "n_Int_UART_GH"              : [16, gpiod.line.Direction.INPUT],    # GPIO16 [INPUT]
        "n_Int_UART_CD"              : [20, gpiod.line.Direction.INPUT],    # GPIO20 [INPUT]
        "n_RESET_DIO"                : [21, gpiod.line.Direction.OUTPUT]    # GPIO21 [OUTPUT]
    }
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    The dictionary containing the net names of Goldilocks rev 1 & 2 net names this class controlls.
    """

    GOLDILOCKS_REV_A:Dict[str, int] = {

    }
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    The dictionary containing the net names of Goldilocks rev A net names this class controlls.
    """


    SYS_GPIO_CONTROLER_DEFAULT: str = '/dev/gpiochip4'
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    The defualt path to the GPIO controller file on the rspberry pi 5.
    """


    def __init__(self, threadName:str, gpioController:str=SYS_GPIO_CONTROLER_DEFAULT, goldilocksRevision:str=LATEST_GOLDILOCKS_REV):
        # Get and consume GPIO lines for use by this process
        self.controllerChip = gpiod.Chip(gpioController)

        try:
            _gpioConfiguration:dict = self.__getattribute__(goldilocksRevision)
        except:
            pass # TODO

        _netNames:List[str] = _gpioConfiguration.keys()

        gpiodConfiguration:dict = {}
        for net in _netNames:
            _current:list = _gpioConfiguration.get(net, [-1, -1])

            if 2 == len(_current):
                gpiodConfiguration[_current[0]] = gpiod.LineSettings(
                    direction = _current[1]
                )
            elif (3 == len(_current)) and (_current[2] != gpiod.line.Value.ACTIVE):
                gpiodConfiguration[_current[0]] = gpiod.LineSettings(
                    direction = _current[1],
                    bias = _current[2]
                )
            elif (3 == len(_current)) and (_current[2] == gpiod.line.Value.ACTIVE):
                gpiodConfiguration[_current[0]] = gpiod.LineSettings(
                    direction = _current[1],
                    output_value = _current[2]
                )
            else:
                raise ValueError(f"The value of gpioConfiguration: {_current} is not valid.")

        self.lines = self.controllerChip.request_lines(
            config = gpiodConfiguration,
            consumer = threadName
        )

        return None
    

    def __del__(self):
        self.controllerChip.close()
    

    def setPinState(self, pin:str, setPinHigh:bool=True) -> None:
        '''
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param pin: The net name of the GPIO pin to action on.
        :param setPinHigh: If the pin should be set high, if false, the pin is set low.

        :raises IOError: When a pin who is configured to be an input in HW, is requested to be set to a value.

        ## Set GPIO Pin
        '''

        pinNum:int = getattr(self, pin)

        pinCfg = self.controllerChip.get_line_info(pinNum)
        if pinCfg.direction == gpiod.line.Direction.INPUT: raise IOError("Tried to set a sys GPIO input pin to a value - INVALID TRANSACTIOn")

        if setPinHigh:
            self.lines.set_value(
                line = pinNum,
                value = gpiod.line.Value.ACTIVE
            )
        else:
            self.lines.set_value(
                line = pinNum,
                value = gpiod.line.Value.INACTIVE
            )

        return None
    

    def readPinState(self, pin:str) -> bool:
        '''
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param pin: The net name of the GPIO pin to action on.

        :returns bool: The value of the pin/net in CMOS LL, False is 0, True is 1.

        ## Read GPIO Pin
        '''

        readState:bool = False
        pinNum:int = getattr(self, pin)

        raw = self.lines.get_value(pinNum)
        if raw.value == 'hi': readState = True

        return readState

################################################################

## OTHER CODE ##

################################################################

# EOF