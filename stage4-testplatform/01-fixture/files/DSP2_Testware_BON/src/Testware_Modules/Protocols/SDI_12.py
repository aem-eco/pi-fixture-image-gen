################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: SDI_12.py
# | Date: 2024-12-23
# | Rev: 0
# | Change By: Everly Larche
# | ECO Ref: CTF-79
#  ----------------
# | Project Name: AEM Test & Measurement Platform
# | Developer: Everly Larche
# | File Description:
#  ----------------
################################################################
################################################################

## LIBRARY USE // EXPECTED INPUT/OUTPUT AND LIMITATIONS ##

################################################################

## SUBCOMPONENT IMPORTS ##
from ..Peripherals.SC16IS752_Handle import SC16IS752_Handler

from typing import List
import time, random

################################################################

## CLASS DEFINITION AND METHODS ##
class Datalogger(SC16IS752_Handler):
    '''
    
    '''
    pass


class Sensor(SC16IS752_Handler):
    '''
    
    '''

    SDI_IDENTIFIY_COMMAND: str          = "I!"
    SDI_START_MEASUREMENT_COMMAND: str  = "M!"
    SDI_DATA_COMMAND: str               = "D0!"

    SDI_PROCESS_NAME_CONTAINS_A:str = "-A"
    SDI_PROCESS_NAME_CONTAINS_B:str = "-B"
    SDI_PROCESS_NAME_CONTAINS_C:str = "-C"
    SDI_PROCESS_NAME_CONTAINS_D:str = "-D"

    SDI_AC_UART_PORT: int = 0
    SDI_BD_UART_PORT: int = 1

    SDI_AC_TX_EN_PIN: int = 6
    SDI_BD_TX_EN_PIN: int = 7

    SDI_A_PWR_READ_PIN: int = 2
    SDI_B_PWR_READ_PIN: int = 4
    SDI_C_PWR_READ_PIN: int = 1
    SDI_D_PWR_READ_PIN: int = 3

    SDI_A_PWR_OUTPUT_PIN: int = 1
    SDI_B_PWR_OUTPUT_PIN: int = 3
    SDI_C_PWR_OUTPUT_PIN: int = 0
    SDI_D_PWR_OUTPUT_PIN: int = 2

    SDI_UART_GPIO_OUTPUTS_AB: List[bool] = [
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True
    ]
    SDI_UART_GPIO_SENSOR_STATES_AB: List[bool] = [
        False,
        False,
        False,
        False,
        False,
        False,
        True,
        True
    ]

    SDI_UART_GPIO_OUTPUTS_CD: List[bool] = [
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True
    ]
    SDI_UART_GPIO_SENSOR_STATES_CD: List[bool] = [
        False,
        False,
        False,
        False,
        False,
        False,
        True,
        True
    ]

    SDI_SENSOR_ADDRESS: int = 7
    SDI_SENSOR_VERSION_COMPATIBILITY: str = "14"
    SDI_SENSOR_VENDOR: str = "AEMECO24"
    SDI_SENSOR_MODEL: str = "GOLD"
    SDI_SENSOR_VERSION: str = "2"
    SDI_SENSOR_OPTIONAL_FIELD: str = "GLV2_1"

    SDI12_BAUD: int             = 1200
    SDI12_Byte_Size: int        = 7
    SDI12_PARITY: str           = SC16IS752_Handler.PARITY_EVEN
    SDI12_FLOW_CONTROL: str     = 0
    SDI12_STOP_BITS: int        = 1
    SDI12_EOL_TERMINATOR:str    = "!"

    def __init__(self, address) -> None:

        self.SDI_PORT_NAME = self.twLogger.name # Could also use I2C address but this allows us to use the name assigned to the logger (ex. SDI-Port-A~twLogger)

        super().__init__(
            address,
            self.SDI12_BAUD,
            self.SDI12_Byte_Size,
            self.SDI12_PARITY,
            self.SDI12_STOP_BITS,
            self.SDI12_FLOW_CONTROL,
            self.SDI12_EOL_TERMINATOR
        )
        
        # Set SDI PWR settings accordingly for a sensor connection
        # ONLY WORKS ON GL Revision 2 or A
        # By defualt, all aux GPIO is outputs and LOW
        if (self.SDI_PROCESS_NAME_CONTAINS_A or self.SDI_PROCESS_NAME_CONTAINS_B) in self.SDI_PORT_NAME:
            for i, output in  enumerate(self.SDI_UART_GPIO_OUTPUTS_AB):
                if output: self.setupGPIO(0, i, 1)
                else: self.setupGPIO(0, i, 0)

                if self.SDI_UART_GPIO_SENSOR_STATES_AB[i]: self.writeGPIO(0, i, 1)
                else: self.writeGPIO(0, i, 0)

        elif (self.SDI_PROCESS_NAME_CONTAINS_C or self.SDI_PROCESS_NAME_CONTAINS_D) in self.SDI_PORT_NAME:
            for i, output in  enumerate(self.SDI_UART_GPIO_OUTPUTS_CD):
                if output: self.setupGPIO(0, i, 1)
                else: self.setupGPIO(0, i, 0)

                if self.SDI_UART_GPIO_SENSOR_STATES_CD[i]: self.writeGPIO(0, i, 1)
                else: self.writeGPIO(0, i, 0)

        if (self.SDI_PROCESS_NAME_CONTAINS_A or self.SDI_PROCESS_NAME_CONTAINS_C) in self.SDI_PORT_NAME: self.uartPort:int = 0
        else: self.uartPort:int = 1

        self.enablePWRout(False) # Turn off applied SDI power by default
        self.enableMonitoringOfSDIPWR(True) # By defualt turn on monitoring power

        return None
    

    def enablePWRout(self, enabled:bool=True) -> None:
        """
        .. versionadded:: 0.4
        .. versionchanged:: 0.4

        .. NOTE:: Needs update to support Goldilocks Revision A
        """

        outputLevel:int = 0
        if enabled: outputLevel = 1

        if self.SDI_PROCESS_NAME_CONTAINS_A in self.SDI_PORT_NAME:
            self.writeGPIO(0, self.SDI_A_PWR_OUTPUT_PIN, outputLevel)

        elif self.SDI_PROCESS_NAME_CONTAINS_B in self.SDI_PORT_NAME:
            self.writeGPIO(0, self.SDI_B_PWR_OUTPUT_PIN, outputLevel)

        elif self.SDI_PROCESS_NAME_CONTAINS_C in self.SDI_PORT_NAME:
            self.writeGPIO(0, self.SDI_C_PWR_OUTPUT_PIN, outputLevel)

        elif self.SDI_PROCESS_NAME_CONTAINS_D in self.SDI_PORT_NAME:
            self.writeGPIO(0, self.SDI_D_PWR_OUTPUT_PIN, outputLevel)

        else:
            listofkeywords:List[str] = [self.SDI_PROCESS_NAME_CONTAINS_A, self.SDI_PROCESS_NAME_CONTAINS_B, self.SDI_PROCESS_NAME_CONTAINS_C, self.SDI_PROCESS_NAME_CONTAINS_D]
            raise ValueError(f"The process name {self.SDI_PORT_NAME} does not contain any of the following keywords: {listofkeywords} and is unable to set the SDI PWR output accordingly.")

        return None
    

    def enableMonitoringOfSDIPWR(self, enabled:bool=True) -> None:
        '''
        .. versionadded:: 0.4
        .. versionchanged:: 0.4

        .. NOTE:: Needs update to support Goldilocks Revision A
        '''

        outputLevel:int = 0
        if enabled: outputLevel = 1

        if self.SDI_PROCESS_NAME_CONTAINS_A in self.SDI_PORT_NAME:
            self.writeGPIO(0, self.SDI_A_PWR_READ_PIN, outputLevel)

        elif self.SDI_PROCESS_NAME_CONTAINS_B in self.SDI_PORT_NAME:
            self.writeGPIO(0, self.SDI_B_PWR_READ_PIN, outputLevel)

        elif self.SDI_PROCESS_NAME_CONTAINS_C in self.SDI_PORT_NAME:
            self.writeGPIO(0, self.SDI_C_PWR_READ_PIN, outputLevel)

        elif self.SDI_PROCESS_NAME_CONTAINS_D in self.SDI_PORT_NAME:
            self.writeGPIO(0, self.SDI_D_PWR_READ_PIN, outputLevel)

        else:
            listofkeywords:List[str] = [self.SDI_PROCESS_NAME_CONTAINS_A, self.SDI_PROCESS_NAME_CONTAINS_B, self.SDI_PROCESS_NAME_CONTAINS_C, self.SDI_PROCESS_NAME_CONTAINS_D]
            raise ValueError(f"The process name {self.SDI_PORT_NAME} does not contain any of the following keywords: {listofkeywords} and is unable to set the PWR monitoring accordingly.")

        return None
    

    def setTxLine(self, SetForTx:bool=True) -> None:
        '''
        .. versionadded:: 0.4
        .. versionchanged:: 0.4
        '''

        if self.uartPort == self.SDI_AC_UART_PORT:
            TxENpin:int = self.SDI_AC_TX_EN_PIN
        else:
            TxENpin:int = self.SDI_BD_TX_EN_PIN

        # Transmitting is an active low activity
        if SetForTx: self.writeGPIO(0, TxENpin, 0)
        else: self.writeGPIO(0, TxENpin, 1)

        return None
    

    def respondToLogger(self, SDImessage:str) -> None:
        '''
        .. versionadded:: 0.4
        .. versionchanged:: 0.4
        '''

        self.setTxLine(True)
        self.transmitData(self.uartPort, SDImessage+"\r\n")
        self.setTxLine(False)
        self._resetFIFOs(self.uartPort)

        return None
    

    def _simulatedMeasurementCommand(self) -> None:
        '''
        .. versionadded:: 0.4
        .. versionchanged:: 0.4
        '''

        # Determine the number of measurement values in range 1-9 as per SDI12 1.4
        measurementValueCount:int = random.randint(1, 9)

        # Determine the amount of time to wait for the D command from the datalogger
        measurementWaitSeconds:int = random.randint(2, 10)

        self.respondToLogger(f"{self.SDI_SENSOR_ADDRESS}{measurementWaitSeconds:03}{measurementValueCount}")
        timerStart: float = time.perf_counter()

        # Generate fake generic data while the logger waits
        # Data values as per SDI12 1.4 follow pd.d
        genericFloats:List[float] = []
        for i in range(0, measurementValueCount, 1):
            genericFloats.append(
                random.uniform(0.0, 50.0)
            )

        genericDataString: str = f"{self.SDI_SENSOR_ADDRESS}"+[f"{value:.2}" for value in genericFloats]

        while (time.perf_counter() - timerStart) < measurementWaitSeconds - 0.5:
            pass # Do nothing, wait for time to elapse (minus a little so we are ready for the logger)

        expectedDataCommand: str = self.waitForSDIMessage(False)

        if self.SDI_DATA_COMMAND in expectedDataCommand: pass
        else: raise ValueError(f"Got another SDI command {expectedDataCommand}. Expected aD0!.")

        self.respondToLogger(genericDataString)

        return None
    

    def determineCommand(self, command:str) -> None:
        '''
        .. versionadded:: 0.3
        .. versionchanged:: 0.4
        '''

        if self.SDI_IDENTIFIY_COMMAND in command:
            self.respondToLogger(f"{self.SDI_SENSOR_ADDRESS}{self.SDI_SENSOR_VERSION_COMPATIBILITY}{self.SDI_SENSOR_VENDOR}{self.SDI_SENSOR_MODEL}{self.SDI_SENSOR_VERSION}{self.SDI_SENSOR_OPTIONAL_FIELD}")

        elif self.SDI_START_MEASUREMENT_COMMAND in command:
            self._simulatedMeasurementCommand()

        return None

    
    def waitForSDIMessage(self, decodeCommand:bool=True, receivedFrom:str|None=None) -> None|str:
        '''
        .. versionadded:: 0.3
        .. versionchanged:: 0.4
        '''

        self.setTxLine(False)
        message: str = self.receiveASAP(self.uartPort)
        if decodeCommand:
            self.determineCommand(message)
        else:
            self._resetFIFOs(self.uartPort)
            return message

        return None
    
################################################################

## OTHER CODE ##

################################################################

# EOF