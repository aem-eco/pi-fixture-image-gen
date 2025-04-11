################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: watsConfig.py
# | Date: 2024-10-24
# | Rev: 1.0
# | Change By: Everly Larche
# | ECO Ref:
#  ----------------
# | Project Name: AEM Test & Measurement Platform
# | Developer: Everly Larche
# | File Description: Dataclass for the WATS Json configuration file
#  ----------------
################################################################
################################################################

## IMPORT FILES ##
from dataclasses import dataclass

################################################################

## CLASS DEFINITION AND METHODS ##
@dataclass
class aemWATSconfiguration:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    Simple dataclass for 1:1 translation of the WATS fixture configuration file.
    """

    type: str
    processCode: int
    processName: str
    location: str
    purpose: str
    machineName: str

    WATSpythonProcess: str

    # These are dynamic and may not be available at init
    pn: str|None = None
    rev: str|None = None

################################################################

## OTHER CODE ##

################################################################

# EOF