################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: SC16IS752.py
# | Date: 2024-10-28
# | Rev: 2.1
# | Change By: Everly Larche
# | ECO Ref: CTF-78
#  ----------------
# | Project Name: AEM_Testware
# | Developer: R.Crouch & Everly Larche
# | File Description: 
#  ----------------
################################################################
################################################################

## COMPONENT USE // EXPECTED INPUT/OUTPUT AND LIMITATIONS // LIBRARY DESIGNED FOR ##

# Developed for use in test fixtures utilizing the Goldilocks testbed.
# Provides methods for using both the dual UART and GPIO functionality of the SC16IS752 chipset

################################################################

## IMPORT FILES ##
from ...Core_Testware.Tools.String_Tools import encodeStringToChars

from ctypes import cdll, c_ubyte, create_string_buffer, byref, c_long, c_char_p, c_uint, c_int
import time

################################################################

## CLASS DEFINITION AND METHODS ##
class SC16IS752_Handler:
    """
    .. versionadded:: 1.0
    .. verionchanged:: 2.1

    # SC16IS752 Handler
    """

    # General Consts.
    PARITY_NONE: str        = "N"
    PARITY_ODD: str         = "O"
    PARITY_EVEN: str        = "E"
    PARITY_FORCE_ONE: str   = "1"
    PARITY_FORCE_ZERO: str  = "0"

    C_LIB_FULL_PATH: str = "/home/Test-Measurement-AEM/DSP2_Testware/src/Testware_Modules/Peripherals/SC16IS752.so"
    """
    The full absolute path to the shared object file containing the c-based code to drive the SC16IS752 in user-space.
    """

    MAX_BUFFER_SIZE:int = 1000

    # UART Consts.
    XTAL_FREQ_SDI: int       = 3686400
    """
    The crystal frequency used in the drivers for the SDI section of Goldilocks.
    """

    XTAL_FREQ_UART: int      = 18432000
    """
    The crystal frequency used in the drivers for the general purpose UART section of Goldilocks.
    """

    MCR_MASK: c_ubyte        = c_ubyte(0x80)
    INTERNAL_UART_A: c_ubyte = c_ubyte(0x00)
    INTERNAL_UART_B: c_ubyte = c_ubyte(0x01)

    def __init__(self, address, baudRate:int=9600, byteSize:int=8, parity:str=PARITY_NONE, stopBits:int=1, flowControl:int=0, endOfMessage:str="\r\n", internalUART:int|None=None) -> None:

        #GPIO
        self.bitMask        = None

        # UART
        self.baudRate: int              = baudRate
        self.byteSize: int              = byteSize
        self.parity: str                = parity
        self.stopBits: int              = stopBits
        self.flowControl: int           = flowControl

        self.eolTerminator              = endOfMessage


        # Determine if being used for SDI or UARTS - different XTALs
        # GL Rev A and above (or modified GL Rev 2)
        if (address == 82) or (address == 87):
            self.xtal_selected = self.XTAL_FREQ_UART
        else:
            self.xtal_selected = self.XTAL_FREQ_SDI

        self.readWriteComboDelay: float = (self._singleClockDelayTime())*64.0   # Gives us the time we should wait after pushing data out of the FIFO before executing a read.

        self.characterTimeDelay_ns:c_long   = c_long(int((self._singleClockDelayTime())*pow(10,9)*self.byteSize*64))
        self.address: c_ubyte               = c_ubyte(address)
        self.c_lib                          = cdll.LoadLibrary(self.C_LIB_FULL_PATH)        # Load custom driver
        self.c_lib.read_gpio.restype        = c_ubyte                                       # Define the return type as a uint8_t
        self.c_lib.transmit_data.argtypes   = c_ubyte, c_ubyte, c_char_p, c_int, c_long     # Define the argument types for transmit data, needed for string to char * conversion
        self.c_lib.receive_data.argtypes    = c_ubyte, c_ubyte, c_long, c_char_p
        self.c_lib.setup_uart.argtypes      = c_ubyte, c_ubyte, c_ubyte, c_ubyte, c_ubyte, c_ubyte

        if None == internalUART:
            self.setupUART(self.INTERNAL_UART_A)    # Setup both UARTS when
            self.setupUART(self.INTERNAL_UART_B)    # no spesific UART selected
        else:
            self.setupUART(internalUART)            # Only setup specified UART

        return None
    

    def _singleClockDelayTime(self) -> float:
        """
        .. versionadded:: 2.1
        .. versionchanged:: 2.1

        ## Calculate the Clock Delay
        """

        _delayTime:float = (1/self.xtal_selected)

        return _delayTime


    def setupUART(self, uart:c_ubyte) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 2.1

        :param uart: The interal UART used for this call. 0 or 1 (A or B).

        :raises IndexError: If the parity selection is invalid.

        ## UART Setup
        """

        ## Set the Parity and Word Length
        # For parity only care about the 3-bits in the middle [5] ... [3]
        match self.parity:
            case self.PARITY_NONE:
                parityMask = 0x00

            case self.PARITY_EVEN:
                parityMask = 0x18

            case self.PARITY_ODD:
                parityMask = 0x08

            case self.PARITY_FORCE_ONE:
                parityMask = 0x28

            case self.PARITY_FORCE_ZERO:
                parityMask = 0x38
            
            case _:
                raise IndexError("No valid Parity Selected for SC16IS752!")

        if self.stopBits == 1:
            stopBitMasks = [0xFB,0x00]  # xxxx x0xx
        else:
            stopBitMasks = [0xFF,0x04]  # xxxx x1xx

        wordLengthMask = self.byteSize - 0x05
        wordLengthMasks = [wordLengthMask | 0xFC, wordLengthMask]

        lcrNew = parityMask
        lcrNew = (lcrNew & stopBitMasks[0]) | stopBitMasks[1]
        lcrNew = (lcrNew & wordLengthMasks[0]) | wordLengthMasks[1]
        lcrNew:c_ubyte = c_ubyte(lcrNew) # Re-cast as uint8

        divisorOne = round((self.xtal_selected / 1) / (self.baudRate * 16),0)
        if divisorOne > 0:
            calcBaudOne = ((self.xtal_selected / 1)/ divisorOne) / 16
        else:
            calcBaudOne = -99999999
        divisorFour = round((self.xtal_selected / 4) / (self.baudRate * 16),0)
        if divisorFour > 0:
            calcBaudFour = ((self.xtal_selected /4)/ divisorFour) / 16
        else:
            calcBaudFour = -99999999

        if abs(calcBaudOne / self.baudRate) < abs(calcBaudFour / self.baudRate):
            divisor = divisorOne
            prescaler = 1
        else:
            divisor = divisorFour
            prescaler = 4

        if prescaler == 1:
            newMCRValue:c_ubyte = c_ubyte(0x00)
        else:
            newMCRValue:c_ubyte = c_ubyte(0x80)
        
        divisor = int(round(divisor,0))
        dlh: c_ubyte = divisor & 0xFF00
        dll: c_ubyte = divisor & 0x00FF
        
        self.c_lib.setup_uart(self.address, uart, dll, dlh, newMCRValue, lcrNew)

        return None


    def sendBreak(self, uart:c_ubyte, duration_ns:c_uint = c_uint(15000000)) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 2.1

        :param uart: The interal UART used for this call. 0 or 1 (A or B).

        ## Send Break
        """

        uart = c_ubyte(uart)
        self.c_lib.send_break(self.address, uart, duration_ns)

        return None


    
    def _resetFIFOs(self, uart:c_ubyte) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 2.1

        :param uart: The interal UART used for this call. 0 or 1 (A or B).

        ## Reset FIFO Buffers
        """

        uart = c_ubyte(uart)
        self.c_lib.reset_fifos(self.address, uart, self.xtal_selected)
    
        return None


    def transmitData(self, uart:c_ubyte, data:str) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 2.1

        :param uart: The interal UART used for this call. 0 or 1 (A or B).

        ## Transmit Data
        """

        _encodedStringToSendToCLib = data.encode()
        length:c_int = c_int(len(_encodedStringToSendToCLib))
        uart = c_ubyte(uart)
        self.c_lib.transmit_data(self.address, uart, _encodedStringToSendToCLib, length, self.characterTimeDelay_ns)
        time.sleep(self.readWriteComboDelay)

        return None

    
    def receiveASAP(self, uart:c_ubyte) -> str:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 2.1

        :param uart: The interal UART used for this call. 0 or 1 (A or B).

        ## Receive Data
        """

        uart = c_ubyte(uart)
        data = create_string_buffer(self.MAX_BUFFER_SIZE)
        self.c_lib.receive_data(self.address, uart, self.characterTimeDelay_ns, data)
        try:
            stringData = data.value.decode()
        except Exception as e:
            # TODO log the error
            return "-9999" # Decode failed - return none for main process to decide what to do next

        return stringData
    

    def setupGPIO(self, uart:c_ubyte, pin:c_ubyte, output:c_ubyte) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 2.1

        :param uart: The interal UART used for this call. 0 or 1 (A or B).

        ## Set-up GPIO
        """

        uart = c_ubyte(uart)
        pin = c_ubyte(pin)
        output = c_ubyte(output)
        self.c_lib.setup_gpio(self.address, uart, pin, output)

        return
    

    def writeGPIO(self, uart:c_ubyte, pin:c_ubyte, newState:c_ubyte) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 2.1

        :param uart: The interal UART used for this call. 0 or 1 (A or B).

        ## Write GPIO Pin
        """

        uart = c_ubyte(uart)
        pin = c_ubyte(pin)
        newState = c_ubyte(newState)

        self.c_lib.write_gpio(self.address, uart, pin, newState)

        return
    

    def readGPIO(self, uart:c_ubyte, pin:c_ubyte) -> bool:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 2.1

        :param uart: The interal UART used for this call. 0 or 1 (A or B).

        ## Read GPIO Pin
        """
        uart = c_ubyte(uart)
        pin = c_ubyte(pin)

        _receiveValue: c_ubyte = self.c_lib.read_gpio(self.address, uart, pin)
        if _receiveValue > 0x00:
            return True

        return False    

################################################################

## OTHER CODE ##

################################################################

# EOF