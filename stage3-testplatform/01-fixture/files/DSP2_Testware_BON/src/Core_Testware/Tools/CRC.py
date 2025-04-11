################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: CRC.py
# | Date: 2025-03-05
# | Rev: 1
# | Change By: Everly Larche
# | ECO Ref: LXP-364
#  ----------------
# | Project Name: LxDSP2.0 BoN
# | Developer: Everly Larche
# | File Description: CRC required for SHT40 tests
#  ----------------
################################################################
################################################################

## IMPORT FILES ##
from typing import List

################################################################

## CLASS DEFINITION AND METHODS ##
class CRC:
    """
    .. versionadded: 1.0
    .. versionchanged: 1.0

    # CRC
    Built from: https://en.wikipedia.org/wiki/Cyclic_redundancy_check
    """

    def __init__(self):
        return
    

    def _stringToBitList(self, inputString:str) -> List[int]:
        """
        .. versionadded: 1.0
        .. versionchanged: 1.0

        :param inputString: The string to convert to a list of ints
        :returns: A list of ints to represent the byte of a unicode character

        ## Transform a string into a list of bits
        """

        return [ord(x) for x in inputString]
    

    def decode8(self, rawInput:str|List[int], poly:int, checkValue:int) -> bool:
        """
        .. versionadded: 1.0
        .. versionchanged: 1.0

        :param rawInput: Either a string or list of ints representing the byte of a unicode character.
        :param poly: The value of the polynomial used in the CRC check

        :returns: A boolean - true for passed CRC, false for failed.

        ## Decode a message with a 8-bit long CRC
        """

        raise NotImplementedError(f"Function is incomplete and will not be used.")

        valid: bool = False
        topBitMask:int = 0x80

        # Get a list of binary
        if isinstance(rawInput, str):
            sequence:List[int] = self._stringToBitList(rawInput)
        elif isinstance(rawInput, list):
            sequence = rawInput
        else:
            raise TypeError(f"Type of: {type(rawInput)}, is not supported here!")

        totalNumber: int = sum(sequence)

        crcBinSequence:str = bin(checkValue)
        crcLength = len(crcBinSequence[2:])

        # Right pad the sequence
        totalNumber = totalNumber << crcLength
        totalNumber += checkValue

        # Get the binary representation to know length of each
        # bin() returns with no leading zeros
        binSequence:str = bin(totalNumber)
        sequenceLength = len(binSequence[2:])

        # bin()[2:] gives us the binary sequence of the whole message (with CRC check val)
        # and removes the '0b' from the python string represenation of the binary seqeunce
        for crcPosition in range(sequenceLength-1, -1, -1):
            if not (pow(2, crcPosition) & totalNumber): continue
            try:
                shiftedDivider = poly << crcPosition
            except:
                break
            remainder = totalNumber ^ shiftedDivider

        if 0 == remainder:
            valid = True

        return valid

################################################################

## OTHER CODE ##
crc = CRC()
crc.decode8("HELLO", 0x31, 0x2D) # '-' is the expected 8 bit CRC character value

################################################################

# EOF