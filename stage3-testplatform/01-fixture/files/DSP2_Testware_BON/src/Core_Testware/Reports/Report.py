################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: Report.py
# | Date: 2025-03-24
# | Rev: 1
# | Change By: Everly Larche
# | ECO Ref: CTF-75
#  ----------------
# | Project Name: AEM Test & Measurement Platform
# | Developer: Everly Larche
# | File Description: Top-Level module for creating file outputs / reports on the Test & Measurement platform
#  ----------------
################################################################
################################################################

## LIBRARY USE // EXPECTED INPUT/OUTPUT AND LIMITATIONS ##

################################################################

## SUBCOMPONENT IMPORTS ##
from .exportAsCSV import CreateCSV
from .exportAsMarkdownText import Markdown
from .makePDF import CreatePDF
from ..UnitUnderTest.UUT import UUT as aemUUT

import os, json, shutil, requests, ast, time
from typing import Dict, BinaryIO
from dataclasses import dataclass

################################################################

## CLASS DEFINITION AND METHODS ##
@dataclass
class SingleReportConfig:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    :internal: Yes

    A small dataclass for translating between the reports json config
    and python code. Not meant for use outside of NewReport.
    """

    localDirectory: os.path
    cloudDirectory: str


class NewReport:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    Combines the following components in order to create output files
    given any aemUUT object and according to the reporting json configuration file.
    - SingleReportConfig dataclass
    - aem_reports_config.json file
    - exportAsCSV
    - exportAsMarkdown
    - makePDF

    Given the json configuration file, it is possible to output all 3 file types
    for each UUT. It is not possible to only do certain filetypes per UUT in a single run.
    """

    JSON_KEY_LOCAL_DIRECTORY: str = "Local-Directory"
    JSON_KEY_CLOUD_ENDPOINT: str = "Cloud-Endpoint"

    ENVIRONMENT_KEY_AZURE_CLIENT_ID: str = "Azure_Client_ID"
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0
    Key from storing the client id as an environment variable in UNIX-based systems via the ***export key:value*** cli command. Each test fixture system will need to store these secrets and are not accessable unless signed into that user.
    """

    ENVIRONMENT_KEY_AZURE_CLIENT_SECRET: str = "Azure_Client_Secret"
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0
    Key from storing the client secret (application secret key) as an environment variable in UNIX-based systems via the ***export key:value*** cli command. Each test fixture system will need to store these secrets and are not accessable unless signed into that user.
    """

    ENVIRONMENT_KEY_AZURE_TENNENT_ID: str = "Azure_Tennent_ID"
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0
    Key from storing the AEM azure tennent id as an environment variable in UNIX-based systems via the ***export key:value*** cli command. Each test fixture system will need to store these secrets and are not accessable unless signed into that user.
    """


    AZURE_SCOPE: str = "https://graph.microsoft.com/.default"
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0
    Default scope for Microsoft Graph API Calls - must be configured by IT when creating the application permission scheme.
    """

    AZURE_GRANT_TYPE: str = "client_credentials"
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0
    Lets the token granter know we wish to authenticate with Microsoft Graph using our client secret (credentials)
    """

    AZURE_SITE_NAME: str = "AEMOperations"
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0
    User-facing name of the Sharepoint Online site we wish to use as the root drive for subsequent api calls.
    """


    def __init__(self, configurationPath:os.PathLike|None) -> None:

        if None == configurationPath: return None

        self.reportsConfigurations: Dict[str, SingleReportConfig] = {}
        
        with open(configurationPath, 'r') as configFile:
            configJson:dict = json.load(configFile)
            for key in configJson.keys():

                if key == "Logs":
                    self.reportsConfigurations[key] = configJson[key]
                else:
                    self.reportsConfigurations[key] = SingleReportConfig(
                            localDirectory = os.path.abspath(configJson[key][self.JSON_KEY_LOCAL_DIRECTORY]),
                            cloudDirectory = configJson[key][self.JSON_KEY_CLOUD_ENDPOINT]
                        )
                
        return None


    def generateAndSaveReport(self, unitData:aemUUT) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param unitData: An aemUUT object containing all the test data to be placed in the report.

        :raises KeyError: If an unknown report type is encountered.

        Will generate reports and call exportReports() for all
        configured outputs (ex. CSV + Markdown file to be exported to a particular DIR + Cloud)\n

        **See below for the format required of the JSON configuration file this class expects:**

        Supported Keys:
        - CSV
        - Markdown
        - PDF
        - Logs

        Supported Value Pairs:
        - Local-Directory (string, absolute)
        - Cloud-Endpoint (URLencoded string, relative from sharepoint online drive)
            - Use this format for the value pair of the "Logs" key

        .. NOTE:: You must provide all the value pairs to each key used. Ex. you must have a Local-Directory and Cloud-Endpoint even if you only want a CSV locally, just leave the unused value pair as an empty string
        """

        for reportType in self.reportsConfigurations.keys():
            if None == self.reportsConfigurations[reportType]: continue                         # Skip empty report types

            match reportType:
                case "CSV":
                    csvCreator:CreateCSV = CreateCSV(unitData)
                    self.exportReport(
                        originDIR = csvCreator.genCSV(),
                        localDIR = self.reportsConfigurations[reportType].localDirectory,
                        cloudParentFolderName = self.reportsConfigurations[reportType].cloudDirectory
                    )

                case "Markdown":
                    self.exportReport(
                        originDIR = Markdown(),
                        localDIR = self.reportsConfigurations[reportType].localDirectory,
                        cloudParentFolderName = self.reportsConfigurations[reportType].cloudDirectory
                    )

                case "PDF":
                    self.exportReport(
                        originDIR = CreatePDF(),
                        localDIR = self.reportsConfigurations[reportType].localDirectory,
                        cloudParentFolderName = self.reportsConfigurations[reportType].cloudDirectory
                    )

                case "Logs":
                    pass

                case _:
                    raise KeyError("Unknown report type")

        return None
    

    def _pushSharePointViaREST(self, filePath:os.PathLike, cloudFolder:str) -> int:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param filePath: The local file path where the report exists. To be read in as bytes and pushed to cloud.
        :param couldFolder: The drive path in Azure where the file is to be PUT.

        :returns int: -9999 if a request error is encountered, -2 if an error with the local file is encountered, and 200 when OK.

        Given an endpoint and body data, use the python
        requests library to push an output report to the AEM Sharepoint following the below flow:
        1. Get Access Token
            - Endpoint: https://login.microsoft.com/{tennentID}/oauth2/v2.0/token
            - Save token for later calls
        2. Get Site ID By Site Search using the AZURE_SITE_NAME
            - Endpoint: https://graph.microsoft.com/v1.0/sites?search={self.AZURE_SITE_NAME}
            - From knowing the name now we can have the UUID of the sharepoint online site within the tennent, this is required for the next calls
        3. Get Site Drive ID
            - Endpoint: https://graph.microsoft.com/v1.0/sites/{siteID}/drive
            - From the site id, we can get the UUID of the drive we want to store data inside of
        4. Get Parent Asset ID (parent folder ID)
            - Endpoint: https://graph.microsoft.com/v1.0/sites/{siteID}/drive/root:/{cloudFolder}
            - Using the JSON config file for this operation, we can search for the folder we want to place our data into from the drive ID
        5. Post The report into the folder we just made
            - Endpoint: https://graph.microsoft.com/v1.0/sites/{siteID}/drive/items/{parentAssetID}:/{os.path.basename(filePath)}:/content
            - This endpoint lets us push byte data into the folder given a filename+extension. Data is placed in the body of the PUT call

        This method is mostly to be used in the NewReport class, but may be used by the
        MAIN THREAD to upload fixture logs as well.

        .. NOTE:: For more information regarding the Microsoft Graph v1 API, see: https://learn.microsoft.com/en-us/graph/api/overview?view=graph-rest-1.0
        """

        if None == (filePath or cloudFolder): return -9999

        fileData: BinaryIO = None

        try:
            with open(filePath, 'rb') as fileToRead:
                fileData = fileToRead.read()
        except FileNotFoundError as e:
            return -2

        callbackCode: int = -1
        instanceToken: str = ""
        siteID: str = ""
        parentAssetID: str = ""
        clientId = os.getenv(self.ENVIRONMENT_KEY_AZURE_CLIENT_ID)
        clientSecret = os.getenv(self.ENVIRONMENT_KEY_AZURE_CLIENT_SECRET)
        tennentID = os.getenv(self.ENVIRONMENT_KEY_AZURE_TENNENT_ID)

        response = requests.request(
            method = "GET",
            url = f"https://login.microsoft.com/{tennentID}/oauth2/v2.0/token",
            headers = {
                "Conent-Type":"application/x-www-form-urlencoded"
            },
            data = f"client_id={clientId}&scope={self.AZURE_SCOPE}&client_secret={clientSecret}&grant_type={self.AZURE_GRANT_TYPE}"
        )

        if 200 != response.status_code: return -9999
        instanceToken = ast.literal_eval(response.text)["access_token"]

        response = requests.request(
            method = "GET",
            url = f"https://graph.microsoft.com/v1.0/sites?search={self.AZURE_SITE_NAME}",
            headers = {
                "Authorization":instanceToken
            },
            data = ""
        )

        if 200 != response.status_code: return -9999
        for value in json.loads(response.text)["value"]:
            if value["name"] == self.AZURE_SITE_NAME:
                siteID = value["id"]
                break

        response = requests.request(
            method = "GET",
            url = f"https://graph.microsoft.com/v1.0/sites/{siteID}/drive",
            headers = {
                "Authorization":instanceToken
            },
            data = ""
        )

        if 200 != response.status_code: return -9999
        driveID = json.loads(response.text)["id"]

        response = requests.request(
            method = "GET",
            url = f"https://graph.microsoft.com/v1.0/sites/{siteID}/drive/root:/{cloudFolder}",
            headers = {
                "Authorization":instanceToken
            },
            data = ""
        )

        if 200 != response.status_code: return -9999
        parentAssetID = json.loads(response.text)["id"]

        response = requests.request(
            method = "PUT",
            url = f"https://graph.microsoft.com/v1.0/sites/{siteID}/drive/items/{parentAssetID}:/{os.path.basename(filePath)}:/content",
            headers = {
                "Authorization":instanceToken
            },
            data = fileData
        )

        if 201 != response.status_code: return -9999

        return callbackCode


    def exportReport(self, originDIR:os.PathLike, localDIR:os.PathLike|None = None, cloudParentFolderName:str|None = None) -> int:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param originDIR: The temp file directory to be put into the final location localaly and or in the cloud.
        :param localDIR: The directory for the new local copy to be placed into.
        :param cloudParentFolderName: The parent folder of the azure SP online folder.

        :returns int: -9999 if a request error is enountered, 200 if OK.

        Implimented by generateAndSaveReport().

        Takes in the temp file location and output path(s) - then either copies the file
        or creates a byte array of it for cloud upload, or both.

        After this occures the temp file is deleted from the system.

        .. NOTE:: If no local directory is provided, files will continnue to remain and be generated into the .temp/ directory and must be purged manually.
        """

        time.sleep(5)

        if None != cloudParentFolderName:
            try:
                self._pushSharePointViaREST(originDIR, cloudParentFolderName)
            except Exception as e:
                return -9999

        if not os.path.exists(localDIR): os.mkdir(localDIR)

        if (None != localDIR) or ("" != localDIR or originDIR):
            try:
                shutil.copy2(
                    src = originDIR,
                    dst = localDIR
                )

                os.remove(originDIR)
            except Exception as e:
                return -9999

        return 0

################################################################

## OTHER CODE ##

################################################################

# EOF