################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: RS232.py
# | Date: 2024-11-02
# | Rev: 0
# | Change By: Everly Larche
# | ECO Ref:
#  ----------------
# | Project Name: AEM Test & Measurement Platform
# | Developer: Everly Larche
# | File Description: Top level component to communicate using RS232 on the Goldilocks test platform.
#  ----------------
################################################################
################################################################

## LIBRARY USE // EXPECTED INPUT/OUTPUT AND LIMITATIONS ##

################################################################

## SUBCOMPONENT IMPORTS ##
from ..Peripherals.SC16IS752_Handle import SC16IS752_Handler

################################################################

## CLASS DEFINITION AND METHODS ##
class RS232(SC16IS752_Handler):
    '''
    
    '''

    # Goldilocks RS232 UART addresses
    GOLD_UART_EF_ADDRESS:int = 82
    GOLD_UART_GH_ADDRESS:int = 87

    # Goldilocks UART EF Consts.
    GOLD_UART_EF_N_EN_RS232_A_GPIO_PIN:int  = 0
    GOLD_UART_EF_N_EN_RS232_B_GPIO_PIN:int  = 1
    GOLD_UART_EF_AUX_GPIO_B_OUT_6_PIN:int   = 2
    GOLD_UART_EF_AUX_GPIO_B_OUT_5_PIN:int   = 3
    GOLD_UART_EF_AUX_GPIO_B_OUT_4_PIN:int   = 4
    GOLD_UART_EF_AUX_GPIO_B_OUT_3_PIN:int   = 5
    GOLD_UART_EF_AUX_GPIO_B_OUT_2_PIN:int   = 6
    GOLD_UART_EF_AUX_GPIO_B_OUT_1_PIN:int   = 7

    # Goldilocks UART GH Consts.
    GOLD_UART_GH_N_EN_RS232_C_GPIO_PIN:int  = 0
    GOLD_UART_GH_N_EN_RS232_D_GPIO_PIN:int  = 1
    GOLD_UART_GH_AUZ_GPIO_C_IN_1_PIN:int    = 2
    GOLD_UART_GH_AUZ_GPIO_C_IN_2_PIN:int    = 3
    GOLD_UART_GH_AUZ_GPIO_C_IN_3_PIN:int    = 4
    GOLD_UART_GH_AUZ_GPIO_C_IN_4_PIN:int    = 5
    GOLD_UART_GH_AUZ_GPIO_C_IN_5_PIN:int    = 6
    GOLD_UART_GH_AUZ_GPIO_C_IN_6_PIN:int    = 7

    def __init__(self, address:int, baudRate:int, byteSize:int, parity:str, stopBits:int, flowControl=0, eolTerminator:str="\r\n", uartARS232Lvl:bool=True, uartBRS232Lvl:bool=True) -> None:
        # Classwide Variables
        self.address = address

        # Confirm pairty string is valid
        if parity not in [
            SC16IS752_Handler.PARITY_EVEN,
            SC16IS752_Handler.PARITY_ODD,
            SC16IS752_Handler.PARITY_NONE,
            SC16IS752_Handler.PARITY_FORCE_ONE,
            SC16IS752_Handler.PARITY_FORCE_ZERO ]: raise ValueError

        # Setup UART A and B
        super().__init__(
            address = address,
            baudRate = baudRate,
            byteSize = byteSize,
            parity = parity,
            stopBits = stopBits,
            flowControl = flowControl,
            endOfMessage = eolTerminator
        )

        # Setup GPIO for respective UART IC's (either UART E/F or G/H)
        # Defualt is all ports are considered to be using RS232 lvls unless constructor is False
        # Activation of MAX lvl converters is active LOW, code logic is active HIGH, so inverting here
        match address:
            case self.GOLD_UART_EF_ADDRESS:
                for i, is_output in enumerate([True]*8):
                    if is_output:
                        self.setupGPIO(0, i, 1)
                    else:
                        self.setupGPIO(0, i, 0)

                if uartARS232Lvl:
                    self.writeGPIO(0, self.GOLD_UART_EF_N_EN_RS232_A_GPIO_PIN, 0)
                if uartBRS232Lvl:
                    self.writeGPIO(0, self.GOLD_UART_EF_N_EN_RS232_B_GPIO_PIN, 0)

            case self.GOLD_UART_GH_ADDRESS:
                for i, is_output in enumerate([True]*2 + [False]*6):
                    if is_output:
                        self.setupGPIO(0, i, 1)
                    else:
                        self.setupGPIO(0, i, 0)

                if uartARS232Lvl:
                    self.writeGPIO(0, self.GOLD_UART_GH_N_EN_RS232_C_GPIO_PIN, 0)
                else:
                    self.writeGPIO(0, self.GOLD_UART_GH_N_EN_RS232_C_GPIO_PIN, 1)

                if uartBRS232Lvl:
                    self.writeGPIO(0, self.GOLD_UART_GH_N_EN_RS232_D_GPIO_PIN, 0)
                else:
                    self.writeGPIO(0, self.GOLD_UART_GH_N_EN_RS232_D_GPIO_PIN, 1)

            case _:
                raise IndexError
        
        return None
    

    def sendCmdAndReceive(self, cmd:str, delayForResponse:float=0.0, activeUART:int=0) -> str:
        '''
        
        '''

        self.transmitData(activeUART, cmd)
        return self.receiveASAP(activeUART)


    def sendCmd(self, cmd:str, activeUART:int=0) -> None:
        '''
        
        '''

        self.transmitData(activeUART, cmd)

        return None
    

    def readLine(self, activeUART:int=0, rxedFromThread:str=None) -> str:
        '''
        
        '''

        if isinstance(activeUART, list):
            activeUART = activeUART[0]      # Unpack if being used in a CARRY_METHOD
        
        data = self.receiveASAP(activeUART)
        #self._resetFIFOs(activeUART)

        return data

################################################################

## OTHER CODE ##

################################################################

# EOF