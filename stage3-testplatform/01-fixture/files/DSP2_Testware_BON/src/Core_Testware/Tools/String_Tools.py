################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: String_Tools.py
# | Date: 2025-03-24
# | Rev: 1.0
# | Change By: Everly Larche
# | ECO Ref:
#  ----------------
# | Project Name: AEM Test & Measurement Platform
# | Developer: Everly Larche
# | File Description: A file containing essential string manilulation functions.
#  ----------------
################################################################
################################################################

## IMPORT FILES ##
from typing import List

################################################################

## CLASS DEFINITION AND METHODS ##

def encodeStringToChars(string:str) -> List[int]:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    :param string: A string to be converted into a list of ints (byte list)
    :returns List[int]: A list of int objects respresenting each unicode character encoded with `UTF-8`.
    """

    _listOfInts:List[int] = []

    for i in range(0, len(string), 1):
        _listOfInts.append(ord(string[i]))

    return _listOfInts

################################################################

## OTHER CODE ##

################################################################

# EOF