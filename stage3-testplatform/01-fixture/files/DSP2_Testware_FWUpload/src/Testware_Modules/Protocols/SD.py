################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: SD.py
# | Date: 2025-03-18
# | Rev: 1
# | Change By: Everly Larche
# | ECO Ref: LXP-366
#  ----------------
# | Project Name: LxDSP 2.0 Bed of Nails
# | Developer: Everly Larche
# | File Description: A basic implimentation of SD over SPI to return a card identifier string
#  ----------------
################################################################
################################################################

## COMPONENT USE // EXPECTED INPUT/OUTPUT AND LIMITATIONS // LIBRARY DESIGNED FOR ##

################################################################

## IMPORT FILES ##
from src.Core_Testware.SPI.SPI_Handler import SPI_Handler

from typing import List
import time

################################################################

## CLASS DEFINITION AND METHODS ##
class SD(SPI_Handler):
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    # Secure Digitial - SD
    
    Only functional method is to set a standard SD card in SPI mode.
    Designed to test electrical connections in hardware fixtures.
    """

    def __init__(self, slaveSelectNetName:str) -> None:

        super().__init__(
            slaveSelect = slaveSelectNetName
        )

        return None
    

    def sendAndGetCMD0(self) -> int:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :returns int: Responds with the `in idle state` bit. 0x01 is IDLE.

        ## CMD0 Card Test
        Using CMD0 (`GO_IDLE_STATE` or RESET) and manually setting the CS/SS
        pins, we can initialize an SD card into SPI mode and check for `IDLE`
        (0x01) on its return to confirm electrical connections to all required pins.

        This is not tested or garunteed to work with SDHC or SDUC cards.
        Verified to work on a Class 4 SD, 256MB card by Lerdisk.
        """

        self._setSS(True)
        wakeupSeq = [0xFF]
        length = 1

        for i in range(0,10,1):
            self.readWrite(length, wakeupSeq)

        self._setSS(False)

        testSequence = [0x40] + [0x00]*4 + [0x95]
        length = len(testSequence)
        self.readWrite(length, testSequence)
        time.sleep(0.25)

        for i in range(0,8,1):
            response = self.readWrite(1, wakeupSeq)
            responseInt:int = int.from_bytes(response)
            if responseInt == 0x01: break

        return responseInt

################################################################

## OTHER CODE ##

################################################################

# EOF