################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: SPI.py
# | Date: 2025-03-06
# | Rev: 1
# | Change By: Everly Larche
# | ECO Ref: LXP-365
#  ----------------
# | Project Name: AEM Test & Measurement Platform
# | Developer: Everly Larche
# | File Description: The base SPI class interfacing inside of user-space.
#  ----------------
################################################################
################################################################

## LIBRARY USE // EXPECTED INPUT/OUTPUT AND LIMITATIONS ##

################################################################

## SUBCOMPONENT IMPORTS ##
from src.TestwareConstants import THREAD_CARRY_METHOD, THREAD_METHOD, MAIN_THREAD_NAME, DUMMY_PLAYLOAD_DELIVER_TO
from src.Core_Testware.TestSteps.testStepDecoder import payload

import os, time
from ctypes import CDLL, c_int, c_uint8, c_char_p, c_uint32, create_string_buffer
from typing import List

################################################################

## CLASS DEFINITION AND METHODS ##
class SPI_Handler:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    :param slaveSelect: The Goldilocks DIO net name controlling the `SS` pin of the target device.
    :param spi_bus:
    :param sub_select:
    :param devClockspeed:
    :param devSPImode:

    # SPI - C Driver Handler
    Implimented as a wrapper of a compiled C file similar to the SC16IS752_Handler.
    Designed to be inherited by another class to add functions for spesific devices, ex an SD card.
    The C driver only has 3 functions, 2 of which are not accessed via the python wrapper.
    The python wrapper is responsible for all of the following functions:
    1. Setting the chip/slave-select lines corresponding to the device inheriting this class
    2. Creating and managing the character buffers used for the tx and rx buffers used in the `spi_ioc_transfer` struct as per spidev.h
    3. Any pre/post-processing on the data buffers

    The goal with a manual/custom implimentation such as this, is to:
    - Maintain control over the source code.
    - Simplification in testing environments.

    This class assumes use on the Goldilocks platform with the chip-select being one of the DIO lines avaliable
    on the base-board (`DIO_A_x` or `DIO_B_x`). This value will be passed along as a CARRY_METHOD to the respective
    DIO process just as in calling a function from the test step file, so ensure the net name is correct and matches
    the CONST in the DIO lib.
    

    ## References
    https://www.kernel.org/doc/html/v5.7/spi/spidev.html
    https://linux-kernel-labs.github.io/refs/heads/master/labs/device_drivers.html#laboratory-objectives
    https://github.com/torvalds/linux/blob/master/include/uapi/linux/spi/spidev.h
    https://github.com/sckulkarni246/ke-rpi-samples/blob/main/spi-c-ioctl/spi_sysfs_loopback.c

    """

    C_LIB_FULL_PATH:str = "/home/Test-Measurement-AEM/DSP2_Testware/src/Core_Testware/SPI/SPI.so"
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    The local absolute path of the shared object file containing the c-based code for driving SPI.
    """

    def __init__(self, slaveSelect:str, spi_bus:int=0, sub_select:int=0, devClockspeed:int=100000, devSPImode:int=0):
        # Changing scope of init arguments to classwide
        self.ss:str = slaveSelect
        self.bus:int = spi_bus
        self.bus_sub:int = sub_select
        self.speed:int = devClockspeed
        self.mode:int = devSPImode

        # Verify the select controller and net is valid
        if "DIO_A_" in slaveSelect: self.ioController:str = "A"
        elif "DIO_B_" in slaveSelect: self.ioController:str = "B"
        else: raise ValueError(f"The value for slaveSelect of:{slaveSelect} is invalid.")

        # Set up for the use of the C library
        self.c_lib                          = CDLL(self.C_LIB_FULL_PATH)
        self.c_lib.readWriteSPI.restype     = c_int
        self.c_lib.readWriteSPI.argtypes    = c_uint8, c_uint8, c_char_p, c_char_p, c_uint32, c_uint32, c_uint32

        return None
    

    def _setSS(self, outputLevel:bool=False) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param outputLevel: Boolean representing a 1 or 0 (high or low) logic voltage output.

        :raises RuntimeError: If the environment at runtime does not contain the expected function `txMessage` which is inherited from `Threading`.

        ## [Internal] - Set Slave-Select
        The function used in this mehtod is only accessable during runtime when
        the class inherits the multiprocessing functions.

        Send the message via main process for the respective DIO controller to
        set the corresponding pin high/low for chip/slave select for SPI comms.

        Assumes the following:
        1. The IO process is alive
        2. IO pin was configured during startup
        3. After the built-in delay to this method, the pin has been set
        """

        if not callable(self.txMessage):
            raise RuntimeError()
        else:
            self.txMessage((
                THREAD_CARRY_METHOD,
                payload(
                    f"DIO_{self.ioController}",
                    THREAD_METHOD,
                    ["writePin", self.ss, outputLevel],
                    DUMMY_PLAYLOAD_DELIVER_TO
                )
            ))

        time.sleep(0.25)

        return None
    

    def readWrite(self, length:int, data:str|List[int]|bytes, decode:bool=False, ssOverride:bool|None=None) -> str|List[int]:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param length: The length as an int of the data object
        :param data: Either a string or list of ints that is to be written to the SPI device
        :param decode: A boolean to denote if the function should return the raw ints (bytes) or a unicode string.

        :returns: A string or list of ints (if no decoding is desired) comprised of the reply from the SPI device

        :raises OverflowError: If the length of the data does not match the passed length argument.

        ## Combo - R/W SPI data
        """

        if len(data) > length: raise OverflowError(f"Data array is larger than length!")

        byteData:bytes

        # TODO - move this encoding to String_Tools
        if isinstance(data, str):
            byteData = bytes(data, 'UTF-8')
        elif isinstance(data, list):
            byteData = bytes(data)

        #if None == ssOverride: self._setSS(True)
        #else: self._setSS(ssOverride)

        tx_Buffer = create_string_buffer(byteData, length)
        rx_Buffer = create_string_buffer(length)

        self.c_lib.readWriteSPI(self.bus, self.bus_sub, rx_Buffer, tx_Buffer, length, self.speed, self.mode)

        # TODO - use a common decode function in the future
        if decode:
            pass # do the thing here, get from tools
        else:
            #if None == ssOverride: self._setSS(False) # Return the SS or CS to a low
            #else: self._setSS(ssOverride)
            
            return rx_Buffer.value
    
################################################################

## OTHER CODE ##

################################################################

# EOF