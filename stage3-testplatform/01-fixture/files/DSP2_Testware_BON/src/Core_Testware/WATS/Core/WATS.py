################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: WATS.py
# | Date: 2025-03-24
# | Rev: 1.0
# | Change By: Everly Larche
# | ECO Ref:
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
from .watsConfig import aemWATSconfiguration
from .WSJFconverter import WSJF, ObjectToJson
from ...UnitUnderTest.UUT import UUT

from typing import List
import os, json, requests

################################################################

## CLASS DEFINITION AND METHODS ##
class WATS:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    # Primary anchor point for linking between AEM Test & Measurement WATS compoents.
    ### WSJFconverter
    - Constant Codes
    - Data structures
    - ObjectToJson framework
    - createObjectified()
    - convertObjectifiedToWSJF()
    ### Fixture-dependent custom implimentation of the required methods from a process file in WATS -> Processes:
    - createElements()
    - generateSingleStep()
    - generateRootSequenceCall()
    ### Current Class Components:
    - Decoding of aem_wats_config.json
    - Translation between aemUUT object(s) and WATS UUT object(s)
    - REST calls and retrevial of environment secret API key
    """

    JSON_TYPE_KEY: str                  = "Type"
    JSON_PART_NUMBER_KEY: str           = "Part-Number"
    JSON_PART_REVISION_KEY: str         = "Part-Revision"
    JSON_PROCESS_CODE_KEY: str          = "Process-Code"
    JSON_PROCESS_NAME_KEY: str          = "Process-Name"
    JSON_LOCATION_KEY: str              = "Location"
    JSON_PURPOSE_KEY: str               = "Purpose"
    JSON_MACHINE_NAME_KEY: str          = "Machine-Name"
    JSON_WATS_PYTHON_PROCESS_KEY: str   = "WATS-Python-Process-Name"

    API_KEY_NAME: str = "WATS_GOLDILOCKS_API_KEY"
    """
    The key of the environment variable containing the WATS token.
    """

    def __init__(self, watsConfigPath:os.path, aemUUTs:List[UUT]) -> None:
        # Get AEM WATS configuration and create object, pass it to ObjectToJson

       # try:
            #if (None == watsProcessName) or (len(watsProcessName) < 1): raise ValueError    # A valid process is required to use this class

            with open(watsConfigPath, 'r') as configFile:
                self.config:dict = json.load(configFile)

            self.watsConfiguration: aemWATSconfiguration = aemWATSconfiguration(
                type                = self.config[self.JSON_TYPE_KEY],
                processCode         = self.config[self.JSON_PROCESS_CODE_KEY],
                processName         = self.config[self.JSON_PROCESS_NAME_KEY],
                location            = self.config[self.JSON_LOCATION_KEY],
                purpose             = self.config[self.JSON_PURPOSE_KEY],
                machineName         = self.config[self.JSON_MACHINE_NAME_KEY],
                WATSpythonProcess   = self.config[self.JSON_WATS_PYTHON_PROCESS_KEY]
            )

            self.converterInstance: ObjectToJson = ObjectToJson(
                processFileToUse = self.watsConfiguration.WATSpythonProcess
            )

            self.uutReports: List[UUT] = aemUUTs

        #except Exception as e:
        #    pass #TODO

        #finally: return None

    
    def runConverterCode(self, uutReport:UUT) -> dict:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param uutReport: The object version of the WSJF UUT report.

        :returns dict: The dict containing the WSJF data to be PUT in WATS via requests.

        Using the instance of the ObjectToJson class from WSJFconverter that was initilized using the fixture-dependent
        process python file to preform the conversions from testware to WSJF using its two primary methods:
        1. createObjectified()
        2. convertObjectifiedToWSJF()
        """
        
        objectVersion:WSJF = self.converterInstance.createObjectified(
            aemUUT = uutReport,
            WATSfixtureConfig = self.watsConfiguration
            )
        
        return self.converterInstance.convertObjectifiedToWSJF(objectVersion)


    def upload(self) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :raises ConnectionError: When the response from aem.wats.com is not 200OK.

        Impliments the call to runConverterCode() and the REST call with a check for "200 OK".
        This is the method that should be called by the MAIN THREAD to initiate the WATS conversion and upload.
        """

        for uutReport in self.uutReports:
            # for each report given, convert and upload
            self.wsjfToUpload = self.runConverterCode(uutReport)
                        
            endpoint: str = "https://aem.wats.com/api/Report/WSJF"
            headers: dict = {
                'Authorization': f'Basic {os.environ.get(self.API_KEY_NAME)}'
            }

            response: requests.Response = requests.request(
                "POST",
                endpoint,
                headers=headers,
                data=json.dumps(self.wsjfToUpload)
            )

            if 200 != response.status_code:
                raise ConnectionError(f"WATS Rest callback: {response.text}")

        return None

################################################################

## OTHER CODE ##

################################################################

# EOF