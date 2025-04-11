################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: AEMtestware.py
# | Date: 2025-04-03
# | Rev: 0.5
# | Change By: Everly Larche
# | ECO Ref:
#  ----------------
# | Project Name: AEM Test & Measurement Platform
# | Developer: Everly Larche
# | File Description: AEM Testware main file
#  ----------------
################################################################
################################################################

## IMPORT FILES ##
import src.Core_Testware.Threading.threader as AEMthread
import src.Core_Testware.TestSteps.testStepDecoder as TSdecoder
from src.Core_Testware.UI.CLIui import TestwareCLIui as UI
from src.Core_Testware.UnitUnderTest.UUT import UUT, SingleTestReport, MultiTestReport, multiMeasurementData, subUUT, miscInfo
from src.Core_Testware.Reports.Report import NewReport
from src.Core_Testware.WATS.Core.WATS import WATS
from src.Core_Testware.SYS.GPIO import GPIO
from .TestwareConstants import *

from src.Testware_Modules.Peripherals.TCA6424A import TCA6424AHandler
from src.Testware_Modules.Peripherals.LTC2497 import LTC2497
from src.Testware_Modules.Peripherals.AD5272 import CombinedDigipots
from src.Testware_Modules.Peripherals.DAC7573 import DAC7573
from src.Testware_Modules.Protocols.SDI_12 import Sensor
from src.Testware_Modules.Protocols.RS232 import RS232
from src.Testware_Modules.Protocols.SD import SD

# Fixture Spesific
from src.Testware_Modules.Product_Interfaces.DSP2 import DSP2_Tests
from src.Testware_Modules.Peripherals.L26T import Quectel_Serial
from src.Testware_Modules.Peripherals.SHT40 import SHT40
from src.Testware_Modules.Product_Interfaces.DModule2C6657i import DModule2C6657i_FW_Upload

## BASE PYTHON 3.xx IMPORTS ##
import logging.handlers
import os, sys, re, time
import json, logging
from typing import List
from multiprocessing import Queue


################################################################

## CLASS DEFINITION AND METHODS ##
class AEMtestware():
    '''
    # AEM Test & Measurement Platform
    ### Version: 0.5
    ### Last Updated: 2025-01-24
    #### The primary class used in the AEM Test & Measurement Platform
    ________
    .. versionadded:: 0.0
    .. versionchanged:: 0.5
    '''


    def __init__(self, masterConfiguration:os.path, sharedQueue:Queue) -> None:
        # Create Class Variables
        self.sharedQueue:Queue = sharedQueue
        self.testPhase: str = "Pre-Test"
        self.threadStates: dict = {}
        self.mainThreadMethodReturnData: any
        self.ResetFixture: bool = True
        self.originalPayload = None

        # Start Root logger of this thread/process as they are not shared
        rootHandler:logging.Handler = logging.handlers.QueueHandler(sharedQueue)
        root:logging.Logger = logging.getLogger()
        root.addHandler(rootHandler)
        root.setLevel(logging.DEBUG)                                                # Leave set to DEBUG as root logger in logging thread will determine what gets logged
        
        # Create MAIN LOGGER
        self.mainLogger:logging.Logger = logging.getLogger("MAIN LOGGER")
        self.mainLogger.info("Started Logging")

        # Load Master Configuration
        self.mainLogger.info(f"Loading Master Configuration at {masterConfiguration}")

        with open(masterConfiguration, 'r') as configurationFile:
            self.masterConfig:dict = json.load(configurationFile)

        # Breakout compoents of master configuration for use in class
        self.fixtureName: str = self.masterConfig["Fixture-Name"]
        self.fixtureVersion: str = self.masterConfig["Fixture-Version"]
        self.mainLogger.info(f"Loaded as: {self.fixtureName} version{self.fixtureVersion}")

        try:
            self.SystemHardwareConfig:dict = self.masterConfig["System_Hardware"]
            self.mainLogger.debug(f"Loaded Hardware Configuration as: {self.SystemHardwareConfig}")
        except KeyError as e:
            self.mainLogger.exception(f"Skipping: {e}")

        try:
            self.PeriferalAddressesConfig:dict = self.masterConfig["Periferial_Addresses"]
            self.mainLogger.debug(f"Loaded I2C Addresses Configuration as: {self.PeriferalAddressesConfig}")
        except KeyError as e:
            self.mainLogger.exception(f"Skipping: {e}")

        try:
            self.UARTConnectionConfiguration:dict = self.masterConfig["Interface-Connection-Configuration"]
            self.mainLogger.debug(f"Loaded Product Interface Connection Configuration as {self.UARTConnectionConfiguration}")
        except KeyError as e:
            self.mainLogger.exception(f"Skipping: {e}")

        try:
            self.MinimumRequirementsConfig:dict = self.masterConfig["Minimum_Requirements"]
            self.mainLogger.debug(f"Loaded Minimum Requirements as: {self.MinimumRequirementsConfig}")
        except KeyError as e:
            self.mainLogger.exception(f"Skipping: {e}")

        try:
            self.PeriferalArgumentsConfig:dict = self.masterConfig["Periferal_Arguments"]
            self.mainLogger.debug(f"Loaded Peripheral Arguments as: {self.PeriferalArgumentsConfig}")
        except KeyError as e:
            self.mainLogger.exception(f"Skipping: {e}")

        try:
            self.nonStdBarcodeData:dict = self.masterConfig["Non-Std-Barcode-Additional-Data"]
            self.mainLogger.debug(f"Loaded Non-Std-Barcode-Additional-Data as: {self.nonStdBarcodeData}")
        except KeyError as e:
            self.mainLogger.exception(f"Skipping: {e}")

        try:
            self.SubConfigurations:dict = self.masterConfig["Sub-Configurations"]
            self.mainLogger.debug(f"Other Configurations to load are: {self.SubConfigurations}")
        except KeyError as e:
            self.mainLogger.exception(f"Skipping: {e}")

        self.numOfSlots: int = self.masterConfig["Test-Slots"]

        # Run additional setup methods
        self.mainLogger.info("Checking Minimum Requirements")
        self.checkMinimumRequirements(self.MinimumRequirementsConfig)

        self.mainLogger.info("Creating SubThreads")
        _tConfigPath:os.path = os.path.join(os.getcwd(), "configurations", self.SubConfigurations["Threading_Configuration"])
        self._readAndSetupSubThreads(threadConfigPath=_tConfigPath)

        # Creating decoders
        self.mainLogger.debug("Creating decoders")

        self.tsDecodePreTest:TSdecoder.TestStepDecoder = TSdecoder.TestStepDecoder(
                    testStepFile=os.path.join(os.getcwd(), "configurations", self.SubConfigurations["Test_Steps"]),
                    phase=PRE_TEST_PHASE
        )
        self.tsDecodeMainTest:TSdecoder.TestStepDecoder = TSdecoder.TestStepDecoder(
                    testStepFile=os.path.join(os.getcwd(), "configurations", self.SubConfigurations["Test_Steps"]),
                    phase=MAIN_TEST_PHASE
        )
        self.tsDecodePostTest:TSdecoder.TestStepDecoder = TSdecoder.TestStepDecoder(
                    testStepFile=os.path.join(os.getcwd(), "configurations", self.SubConfigurations["Test_Steps"]),
                    phase=POST_TEST_PHASE
        )

        # Create UUT object to store information about tests and misc info
        self.UUTsBySlot: List[UUT] = []

        self.mainLogger.debug("Generating list of UUT objects")

        for slot in range(0, self.numOfSlots, 1):
            self.UUTsBySlot.append(UUT(
            model=None,
            testSlot=slot,
            serialNumber=None,
            rev=None,
            batchSerialNumber=None,
            fixtureName=self.fixtureName,
            fixtureSerialNumber=self.masterConfig["Fixture-SN"],
            user=None,
            testStepResults=[],
            miscInfo=[],
            subUUTs=[],
            overallResult=False,
            durationOfRun=None,
            startDatetime=None,
            endDatetime=None
        ))

        self.mainLogger.debug("__init__ is done")
        
        return None


    def checkMinimumRequirements(self, minRequirements:dict) -> None:
        '''
        .. versionadded:: 0.0
        .. versionchanged:: 0.0
        .. WARNING:: Not implimented

        Designed to check that the min requirements as defined in
        the minRequirements configuration have been met before running
        any code or tests.

        Currently this is not implimented and requires additional classes to be created,
        expecially for reading the EEPROM where HW information will be stored.
        '''
        self.mainLogger.warning("REQUIREMENTS NOT IMPLIMENTED")
        return None

        _requirementStatus:dict = {}

        for hardwareRequirements in minRequirements["Hardware"]:
            match hardwareRequirements:
                case "Goldilocks_Revision":
                    # TODO - READ EEPROM
                    pass

                case "Raspberry_Pi_Model":
                    pass

                case "Active_Network_Connection":
                    pass

                case _:
                    self.mainLogger.warning("Defualt case reached - will continue, but may encounter errors")
                    pass

        self.mainLogger.info("Hardware Requirements checked and met")

        for softwareRequirements in minRequirements["Software"]:
            match softwareRequirements:
                case "AEM_Testware_Version":
                    pass

                case "WATS_Sequence_Version":
                    pass

                case "Python":
                    for subComponent in softwareRequirements:
                        match subComponent:
                            case "Version":
                                pass

                            case "Modules":
                                pass

                case _:
                    self.mainLogger.warning("Defualt case reached - will continue, but may encounter errors")
                    pass

        self.mainLogger.info("Software Requirements checked and met")

        return None


    def _readAndSetupSubThreads(self, threadConfigPath:os.path) -> None:
        '''
        .. versionadded:: 0.0
        .. versionchanged:: 0.5
        .. NOTE:: When working with a thread configuration file, the names of the threads must match the variable self.threadClassRelation

        Looks at the confirguration file for Threads and starts to
        create the new threads/processes while appending to a dict storing the Threader
        object + its priority as a tuple.\n

        Additionally, any arguments needing to be passed to a thread/process at initilization will be done here.
        '''

        self.mainLogger.debug("Reading configuration for sub-threads")
        with open(threadConfigPath, 'r') as threadsConfigFile:
            _loadedThreadJSON:dict = json.load(threadsConfigFile)

        self.mainLogger.debug(f"Loaded the Thread configuration as: {_loadedThreadJSON}")

        _numOfUsedThreads: int = len(_loadedThreadJSON["Threads"])
        self.mainLogger.debug(f"Found {_numOfUsedThreads} thread(s) to spawn.")
        
        # Local Method Vars
        self.activeThreads:dict = {}
        self.threadClassRelation:dict = {
            "cliUI":UI,
            "sysGPIO":GPIO,
            "ADC":LTC2497,
            "DSP2_Tests":DSP2_Tests,
            "Quectel_Serial":Quectel_Serial,
            "SHT40":SHT40,
            "RS232":RS232,
            "DIO":TCA6424AHandler,
            "SD":SD,
            "DModule":DModule2C6657i_FW_Upload
        }

        for threadParams in _loadedThreadJSON["Threads"]:
            self.mainLogger.info(f"Setting up a thread named: {threadParams['Name']}, reporting to: {threadParams['Reports-To']}")

            # Special varibles for classes shall be loaded by the classes themselves (ex. I2C device address from masterconfig.json)
            if threadParams["Name"] == "UI": arguments = sys.stdin.fileno()
            elif threadParams["Name"] in ["DIO_A"]: arguments = [self.PeriferalAddressesConfig[threadParams["Name"]], self.PeriferalArgumentsConfig["DIO_A_Outputs"]]
            elif threadParams["Class"] in ["ADC"]: arguments = self.PeriferalAddressesConfig[threadParams["Name"]]
            elif threadParams["Name"] in ["UART-EF", "UART-GH"]: arguments = self.UARTConnectionConfiguration[threadParams["Name"]]
            elif threadParams["Name"] in ["SHT40"]: arguments = self.PeriferalArgumentsConfig["SHT40_I2C_Address"]
            elif threadParams["Class"] in ["Quectel_Serial"]: arguments = self.PeriferalAddressesConfig["UART_CD"]
            elif threadParams["Name"] in ["SD"]: arguments = self.PeriferalArgumentsConfig["SD_SS"]
            elif threadParams["Name"] in ["DModule"]: arguments = self.masterConfig["Firmware_Location"]
            else: arguments = None

            try:
                self.activeThreads[threadParams["Name"]] = (
                    AEMthread.Threader(
                    targetClass=self.threadClassRelation[threadParams["Class"]],
                    reportsTo=threadParams["Reports-To"],
                    loggingQueue=self.sharedQueue,
                    threadName=threadParams["Name"],
                    testwareName=self.fixtureName,
                    biDirectional=threadParams["Duplex"],
                    logLevel=threadParams["Logging-Level"],
                    loggerObject=self.mainLogger,
                    args=arguments
                    ),
                    threadParams["Priority"]
                )
                time.sleep(2)

            except Exception as e:
                self.mainLogger.exception(e)

        # Sort the threads by priority
        _listOfThreadPriorityTuple: list = []
        for thread in self.activeThreads.keys():
            _listOfThreadPriorityTuple.append(
                (thread, self.activeThreads[thread][1])
            )

        # ("I2C Bus Master", 5)
        self.sortedThreadsByPriority: list = sorted(_listOfThreadPriorityTuple, key=lambda threadTuple: threadTuple[1], reverse=True)
        self.mainLogger.debug(f"Sorted all threads by their operational priority: {self.sortedThreadsByPriority}")

        return None
    

    def updateThreadState(self, targetThreadName:str, newstate:str) -> None:
        '''
        .. versionadded:: 0.0
        .. versionchanged:: 0.0

        Sets the attribute self.threadStates to the corresponding newstate that is passed.
        Additionally this logs the new state and returns nothing.
        '''

        self.mainLogger.info(f"Updating status of: {targetThreadName} to {newstate}")
        self.threadStates[targetThreadName] = newstate

        return None
    

    def checkAndReportStateOfSubThreads(self, targetThreadNames:list=None) -> bool|None:
        '''
        .. versionadded:: 0.0
        .. versionchanged:: 0.0

        Can be used to get the status of a particular thread/process (by name)
        and return True if it is IDLE or False if other.

        If a list is sent all threads/processes by name will be checked, if any of them are not IDLE, return False.
        If None is set to the list, check ALL threads/process. False on first non IDLE.
        '''
        
        # if list is none, check all thread states.
        if None == targetThreadNames:
            self.mainLogger.debug("Checking the status of ALL subthreads")
            targetThreadNames = self.activeThreads.keys()

            _allStatus:list = []
            for name in targetThreadNames:
                if "IDLE" != self.threadStates[name]:
                    self.mainLogger.debug(f"List of thread states: {self.threadStates}")
                    return False
            self.mainLogger.debug(f"List of thread states: {self.threadStates}")
            return True

        elif 1 == len(targetThreadNames):
            self.mainLogger.debug(f"Checking the status of thread {targetThreadNames[0]}")
            if MAIN_THREAD_NAME == targetThreadNames[0]: return True
            elif "IDLE" != self.threadStates[targetThreadNames[0]]: return False
            else: return True

        else:   
            return None
    

    def waitForACKNfromSubThread(self, targetThread:AEMthread.Threader, timeout:float=10, retry:int=0) -> bool:
        '''
        .. versionadded:: 0.0
        .. versionchanged:: 0.0
        .. versiondepricated:: 0.3

        Blocking method that will either reutrn True when an acnkwoledgement is rxed from the subthread/process
        or False if we timeout. Defualt timeout is 10sec with 0 retries.
        '''

        raise NotImplementedError("No longer implimented since version 0.3")

        _watchdogStart = time.time()

        _hasACKN: bool = False
        while not _hasACKN:
            # ACKN should be the first thing in the buffer assuming that it has been cleared prior to sending the thread something
            # this should be safe because we RX (ALL) -> TX -> get ACKN -> proceed
            self.mainLogger.debug("Waiting for Sub-Thread to ACKN")

            _response = targetThread.receiveFromSubThread()
            if True == _response:
                self.mainLogger.debug("Sub-Thread ACKN received - continuing")
                _hasACKN = True

            if (time.time() - _watchdogStart) > timeout: raise TimeoutError
        return _hasACKN
    

    def rxMessageFromThreadBasedOnPriority(self) -> tuple|None:
        '''
        .. versionadded:: 0.0
        .. versionchanged:: 0.0

        Initiate a loop through all threads sorted by priority.

        When a thread is found, in order, that has a message pending to be received by the main thread, receive it.
        Then checks for additional messages from that thread.
        '''

        _returnMessages:list = []
        _currentThreadName: str = ""

        for threadTuple in self.sortedThreadsByPriority:
            _currentThreadName = threadTuple[0]

            # Sorted format: AEMthread.Threader.rxMessage()
            _returnMessages.append(self.activeThreads[_currentThreadName][0].receiveFromSubThread())

            if None == _returnMessages[0]:
                self.mainLogger.debug(f"Nothing to RX from thread: {_currentThreadName}")
                _returnMessages = []
                continue
            elif 0 < len(_returnMessages) < 2:
                self.mainLogger.debug(f"{_currentThreadName} has data but only one message.")
                break

        if 0 == len(_returnMessages):
            return None
        return (_returnMessages, _currentThreadName)
    

    def txMessageToSubThread(self, targetThread:AEMthread.Threader, targetMessage:any, waitForACKN:bool=True) -> int|None:
        '''
        .. versionadded:: 0.0
        .. versionchanged:: 0.0

        Acts as a way to access the method inside a Threader object that sends the actual message to a subthread/process.
        Adds an aditional flag to wait for the subthread/process to send an ACKN back to MAIN THREAD before we proceed.
        This can add to the time it takes for a task to be processed, however it does ensure the subthread/process
        understands and accepts what we sent it.
        '''

        # get what to send and where to send it from the arguments
        # send it to the subthread
        # wait for the subthread to ACKN what was sent
        # return None if all good

        _returnCode: int|None = None

        self.mainLogger.debug(f"Sending a message to the subthread: {targetThread.newThreadName} with content: {targetMessage}")
        targetThread.sendToSubThread(targetMessage)

        # Ensure that there are no other messages 

        #try:
            #if waitForACKN: self.waitForACKNfromSubThread(targetThread) # If we are not already ACKN something, we should wait until we get ACKN (ex. sending a command and not replying to an ACKN already)

        #except AEMtestwareException as e:
            #self.mainLogger.exception(e)
            #self.mainLogger.warning("Continuing with a retry to TX message to the target thread")

            #self.txMessageToSubThread(targetThread, targetMessage)

        return _returnCode
    

    def acknSubThread(self, targetThreadName:str) -> None:
        '''
        .. versionadded:: 0.0
        .. versionchanged:: 0.0
        .. versiondepricated:: 0.3

        Send ("ACKN", None, None) to a subthread such that it knows data was rx'ed correctly
        and can carry on with its loops.
        '''

        raise NotImplementedError("Deprecated since version 0.3")
        
        self.txMessageToSubThread(
            targetThread=self.activeThreads[targetThreadName][0],
            targetMessage=("ACKN", None, None),
            waitForACKN=False
        )
        
        return None
    

    def _updateUI(self) -> None:
        '''
        .. versionadded:: 0.0
        .. versionchanged:: 0.0

        A method used to construct the kwargs for the UI THREAD tasks.

        After constructing the UI kwargs it is sent to the UI THREAD as a message.
        It is done this way as to directly retrive data from self and for clarity.

        Some other methods in self may be used to preform UI tasks in addition to this one.
        '''

        # find what method we are using to update the UI
        # get information we need based on testStep
        # send the message to the UI thread
        # return

        _kwargs:dict = {} # make the KW args from a list

        if isinstance(self.testStep.payload.message, list):
            methodName = self.testStep.payload.message[0]
        else:
            methodName = self.testStep.payload.message

        # TODO - dont I have a list of method names already in the threading objects? I should use those as this relys on updating consts if method names change
        match methodName:
            case UI.CLI_UI_PRINT_TITLE:
                _kwargs["program_Name"] = self.fixtureName
                _kwargs["program_Version"] = VERSION
                _kwargs["test_Version"] = self.fixtureVersion

            case UI.CLI_UI_PRINT_Subtitle:
                _kwargs["m_String"] = self.testStep.payload.message[1]

            case UI.CLI_UI_GET_USER_INPUT:
                _kwargs["dataFor"] = self.testStep.payload.message[1]
                _kwargs["query"] = self.testStep.payload.message[2]

            case UI.CLI_UI_PRINT_INFORMATION_NO_SPACER:
                _kwargs["param"] = self.testStep.payload.message[1]
                _kwargs["data"] = self.testStep.payload.message[2]

            case UI.CLI_UI_PRINT_INFORMATION_WITH_SPACER:
                _kwargs["param"] = self.testStep.payload.message[1]
                _kwargs["data"] = self.testStep.payload.message[2]

            case UI.CLI_UI_PRINT_SPACER:
                _kwargs = None
            
            case UI.CLI_UI_GET_SUB_UUTs:
                try:
                    _kwargs["scan"] = self.testStep.payload.message[1]
                except IndexError:
                    _kwargs = None


        # ui prints second time before here
        self.txMessageToSubThread(
            targetThread=self.activeThreads[self.testStep.payload.threadName][0],
            targetMessage=(self.testStep.payload.action, methodName, _kwargs)
        )

        return None


    def runTestStep(self, stepToExec:int) -> int|None:
        '''
        .. versionadded:: 0.0
        .. versionchanged:: 0.0

        From the index given as an argument + self.testPhase state,
        decode the corresponding testStep from the json configuration.

        Depending on the testStep.payload.threadName the task will be handlded differently.
        MAIN THREAD tasks are run by this method,
        UI THREAD tasks are sent to _updateUI() to be handled,
        and all others are sent as messages to the respected thread/process and data is returned via PIPEs.
        '''

        self.stepToExec:int = stepToExec

        # decode test step
        # send data to thread
        # do next step or return (nonblocking or blocking) - this is handled in the main loop code
        # return to main thread to get data from subthreads

        try:
            if PRE_TEST_PHASE == self.testPhase:
                self.testStep:TSdecoder.testStep = self.tsDecodePreTest.decode(stepToExec) # [ ] - in the future these could be one object that gets re-assigned vs 3 objects doing similar things
                
            elif MAIN_TEST_PHASE == self.testPhase:
                self.testStep:TSdecoder.testStep = self.tsDecodeMainTest.decode(stepToExec)

            elif POST_TEST_PHASE == self.testPhase:
                self.testStep:TSdecoder.testStep = self.tsDecodePostTest.decode(stepToExec)

        except IndexError as e:
            self.mainLogger.debug("Index error reported - using this exception to progress the test phase")
            return None

        if "UI" == self.testStep.payload.threadName:
            self._updateUI()
            return stepToExec
        
        if (self.testStep.payload.threadName == MAIN_THREAD_NAME) and (self.testStep.payload.action == THREAD_METHOD):
            if isinstance(self.testStep.payload.message, list):
                _method:object = getattr(self, self.testStep.payload.message[0])

                args = self.testStep.payload.message[1:]
                returnedData = self.mainThreadMethodReturnData = _method(*args)

            else:
                _method:object = getattr(self, self.testStep.payload.message)
                returnedData = self.mainThreadMethodReturnData = _method()

            if (type(returnedData) != tuple) or None == returnedData: pass
            elif THREAD_METHOD == returnedData[1][0]:
                # Test if the reply from MAIN THREAD method is like the format ("UI", ("Method", <methodName:str>, {kwargs}))
                self.txMessageToSubThread(
                    targetThread=self.activeThreads[returnedData[0]][0],
                    targetMessage=returnedData[1]
                )

                # Set the steps payload data so that the program will wait accordingly
                self.testStep.payload.action = THREAD_METHOD
                self.testStep.payload.threadName = returnedData[0]
                self.testStep.payload.deliverTo = MAIN_THREAD_NAME
                self.testStep.payload.message = returnedData[1]

                self.mainThreadMethodReturnData = None
            return stepToExec
        
        if isinstance(self.testStep.payload.message, list):
            self.txMessageToSubThread(
                targetThread=self.activeThreads[self.testStep.payload.threadName][0],
                targetMessage=(self.testStep.payload.action, self.testStep.payload.message[0], self.testStep.payload.message[1:])
            )
            self.mainLogger.debug(f"Running with args: {self.testStep.payload.message[1:]}")
        else:
            self.txMessageToSubThread(
                    targetThread=self.activeThreads[self.testStep.payload.threadName][0],
                    targetMessage=(self.testStep.payload.action, self.testStep.payload.message)
            )

        return stepToExec
    

    def matchExpectTypeAndPreformOp(self, fromThreadName:str, usingTolerance:bool, data:any, expected:TSdecoder.expect|None) -> bool:
        """
        .. versionadded:: 0.4
        .. versionchanged:: 0.4
        """

        _completed:bool = False

        match expected.type:

            # Do a comaprison with None (null) - nothing should be returned as soon as empty data is returned it is considered done
            case TSdecoder.TestStepDecoder.COMP_TYPE_NONE:
                self.mainLogger.debug(f"Matching data of comp type {TSdecoder.TestStepDecoder.COMP_TYPE_NONE}")

                if TSdecoder.TestStepDecoder.COMP_TYPE_NONE == data:
                    self.mainLogger.debug("Matched data, proceed to next step")
                    _completed = True
                else:
                    self.mainLogger.debug(f"Data not matched: {TSdecoder.TestStepDecoder.COMP_TYPE_NONE} vs {data}")

            # DO a comparison with a "Equals" operator
            case TSdecoder.TestStepDecoder.COMP_TYPE_EQ:
                self.mainLogger.debug(f"Matching data of comp type {TSdecoder.TestStepDecoder.COMP_TYPE_EQ}")

                if None == data:
                    _completed = False
                    pass
                elif expected.compareVal == data: _completed = True

                elif usingTolerance:
                    self.mainLogger.debug(f"Using tolerance of: {expected.compareTol}")
                    if 0 == expected.compareVal:
                        _actualDelta: float = abs(data)
                    else:
                        _actualDelta: float = abs(1 - (data/expected.compareVal))

                    self.mainLogger.debug(f"Found delta: {_actualDelta*100}%")
                    if _actualDelta <= expected.compareTol: _completed = True
                    else: pass

                else: pass

            # Do a comparison with a "Greater than" operator
            case TSdecoder.TestStepDecoder.COMP_TYPE_GT:
                self.mainLogger.debug(f"Matching data of comp type {TSdecoder.TestStepDecoder.COMP_TYPE_GT}")

                if None == data:
                    _completed = False
                    pass
                elif expected.compareVal_L < data: _completed = True
                elif usingTolerance:
                    self.mainLogger.debug(f"Using tolerance of {expected.compareTol}")

                    _newAllowedLowLimit: float = expected.compareVal_L - expected.compareVal_L*expected.compareTol
                    self.mainLogger.debug(f"New lower limit calculated to be: {_newAllowedLowLimit}")

                    if _newAllowedLowLimit < data: _completed = True
                    else: pass

                else: pass

            # Do a comparison with a "Less than" operator
            case TSdecoder.TestStepDecoder.COMP_TYPE_LT:
                self.mainLogger.debug(f"Matching data of comp type {TSdecoder.TestStepDecoder.COMP_TYPE_LT}")

                if None == data:
                    _completed = False
                    pass
                elif expected.compareVal_H > data: _completed = True
                elif usingTolerance:
                    self.mainLogger.debug(f"Using tolerance of {expected.compareTol}")

                    _newAllowedLowLimit: float = expected.compareVal_H + expected.compareVal_H*expected.compareTol
                    self.mainLogger.debug(f"New lower limit calculated to be: {_newAllowedLowLimit}")

                    if _newAllowedLowLimit > data: _completed = True
                    else: pass

                else: pass

            # Do a comparison with a "Greater than and less than" operator
            case TSdecoder.TestStepDecoder.COMP_TYPE_GTLT:
                self.mainLogger.debug(f"Matching data of comp type {TSdecoder.TestStepDecoder.COMP_TYPE_GTLT}")
                # Using recusion, create a new expect object and re-use previous cases to determine GT or LT
                # If either are true return True.

                if None == data:
                    _completed = False
                    pass
                elif self.matchExpectTypeAndPreformOp(
                    fromThreadName=fromThreadName,
                    usingTolerance=usingTolerance,
                    data=data,
                    expected=TSdecoder.expect(
                        TSdecoder.TestStepDecoder.COMP_TYPE_GT,
                        expected.units,
                        compareVal=None,
                        compareVal_L=expected.compareVal_L,
                        compareVal_H=None,
                        compareTol=expected.compareTol
                    )

                ) and self.matchExpectTypeAndPreformOp(
                    fromThreadName=fromThreadName,
                    usingTolerance=usingTolerance,
                    data=data,
                    expected=TSdecoder.expect(
                        TSdecoder.TestStepDecoder.COMP_TYPE_LT,
                        expected.units,
                        compareVal=None,
                        compareVal_H=expected.compareVal_H,
                        compareVal_L=None,
                        compareTol=expected.compareTol
                    )

                ): _completed = True

                else: pass

            # Do a comparison with a "Greater than or equal to" operator
            case TSdecoder.TestStepDecoder.COMP_TYPE_GE:
                self.mainLogger.debug(f"Matching data of comp type {TSdecoder.TestStepDecoder.COMP_TYPE_GE}")

                if None == data:
                    _completed = False
                    pass
                elif expected.compareVal_L <= data: _completed = True

                elif usingTolerance:
                    self.mainLogger.debug(f"Using tolerance of {expected.compareTol}")

                    _newAllowedLowLimit: float = expected.compareVal_L - expected.compareVal_L*expected.compareTol
                    self.mainLogger.debug(f"New lower limit calculated to be: {_newAllowedLowLimit}")

                    if _newAllowedLowLimit <= data: _completed = True
                    else: pass

                else: pass

            # Do a comparison with a "Less than or equal to" operator
            case TSdecoder.TestStepDecoder.COMP_TYPE_LE:
                self.mainLogger.debug(f"Matching data of comp type {TSdecoder.TestStepDecoder.COMP_TYPE_LE}")

                if None == data:
                    _completed = False
                    pass
                elif expected.compareVal_H >= data: _completed = True
                elif usingTolerance:
                    self.mainLogger.debug(f"Using tolerance of {expected.compareTol}")

                    _newAllowedLowLimit: float = expected.compareVal_H + expected.compareVal_H*expected.compareTol
                    self.mainLogger.debug(f"New lower limit calculated to be: {_newAllowedLowLimit}")

                    if _newAllowedLowLimit >= data: _completed = True
                    else: pass

                else: pass

            # Do a comparison with a "Greater than or equal to or less than or equal to" operator
            case TSdecoder.TestStepDecoder.COMP_TYPE_GELE:
                self.mainLogger.debug(f"Matching data of comp type {TSdecoder.TestStepDecoder.COMP_TYPE_GELE}")
                # Using recusion, create a new expect object and re-use previous cases to determine GT or LT
                # If either are true return True.
                if None == data:
                    _completed = False
                    pass

                elif self.matchExpectTypeAndPreformOp(
                    fromThreadName=fromThreadName,
                    usingTolerance=usingTolerance,
                    data=data,
                    expected=TSdecoder.expect(
                        TSdecoder.TestStepDecoder.COMP_TYPE_GE,
                        compareVal=None,
                        compareVal_L=expected.compareVal_L,
                        compareVal_H=None,
                        compareTol=expected.compareTol
                    )

                ) and self.matchExpectTypeAndPreformOp(
                    fromThreadName=fromThreadName,
                    usingTolerance=usingTolerance,
                    data=data,
                    expected=TSdecoder.expect(
                        TSdecoder.TestStepDecoder.COMP_TYPE_LE,
                        compareVal=None,
                        compareVal_H=expected.compareVal_H,
                        compareVal_L=None,
                        compareTol=expected.compareTol
                    )

                ): _completed = True

                else: pass

            # Do a comparison with a regex match operator
            case TSdecoder.TestStepDecoder.COMP_TYPE_REGEX:
                # Remove control characters from a string
                if '\n' or '\r' or '\t' in data:
                    data: str = str(data) # Recast as string
                    data = data.translate(data.maketrans("\n\r\t", "   "))

                if None == data:
                    _completed = False
                    pass
                else:
                    comparitor:re.Pattern = re.compile(expected.compareVal)
                    matched = comparitor.match(data)
                    self.mainLogger.debug(f"Preformed a REGEX comparision of: {comparitor} with data: {data} -> {matched}")
                    if None != matched: _completed = True

            # Do a comparison with a list of "equal to" operators where we anticipate a list of data to be compared in order with a list of expected values
            case TSdecoder.TestStepDecoder.COMP_TYPE_EQ_LIST:
                _comparisonList: list = expected.compareVal
                _tolerance: float = expected.compareTol
                _resultList: list[bool] = []

                if None == data:
                    _completed = False

                elif not isinstance(data, list|tuple):
                    pass # TODO

                elif isinstance(data, list|tuple) and (len(data) == len(_comparisonList)):
                    self.mainLogger.debug(f"Comparing list: {_comparisonList} to data: {data}")
                    
                    for i, compvalue in enumerate(_comparisonList):
                        if None != _tolerance:
                            _resultList.append(
                                (compvalue - compvalue*(_tolerance)) <= data[i] <= (compvalue + compvalue*(_tolerance))
                            )

                        else:
                            _resultList.append(
                                compvalue == data[i]
                            )

                else:
                    pass # TODO
    
            # Do a comparison with a boolean match oeprator
            case TSdecoder.TestStepDecoder.COMP_TYPE_EQ_BOOL:
                if None == data:
                    _completed = False
                    pass
                else:
                    self.mainLogger.debug(f"Comparing type BOOL with Expected value of: {expected.compareVal} and data value: {data}")
                    if not isinstance(data, bool): _completed = False
                    elif (expected.compareVal == data): _completed = True
                    elif (expected.compareVal != data): _completed = False

            # Attempt to find a siubstring in the data returned
            case TSdecoder.TestStepDecoder.COMP_TYPE_CONTAINS:
                if -1 != data.find(expected.compareVal):
                    _completed = True

            case _:
                # TODO - handle defualt case error state
                pass

        return _completed
    

    def verifyStepIsComplete(self, fromThreadName:str, data:any, expected:TSdecoder.expect|List[TSdecoder.expect]|None) -> bool|List[bool]|None:
        '''
        .. versionadded:: 0.0
        .. versionchanged:: 0.4

        Preforms a comparison of the data returned from a thread or method against the expected value
        based on its comparison type.\n

        *Saves a copy of the data in the class for use in other methods.*

        - Returns a bool as True if the step was validated to be complete + PASS
        - Returns a bool as False if the step was validated to be complete + FAIL (In this case, on return of this method and we do not retry mark test step in UUT as failed)
        - Returns None if an error occured or the step is incomplete
        '''

        self.mainLogger.debug(f"Checking that step is completed. From: {fromThreadName}, Data: {data}, Expected value: {expected}")

        # If the step under observation has an expected block containing a list of expect objects
        # we need to validate each measurement to know if the step is a pass or fail.
        # Each expect block in a list form should contain a `name` field that will be applied to a final `multiMeasurementData` object.
        if self.testStep.multipleMeasurements and (len(expected) == len(data)):
            _completed: List[bool] = []
            _usingTolerance: bool = False

            for i, singleComparitor in enumerate(expected):
                # If using a tolerance, deviations from a value will be calculated (ex. TYPE_EQ+/-5%)
                if None != singleComparitor.compareTol: _usingTolerance = True
                try:
                    _completed.append(self.matchExpectTypeAndPreformOp(fromThreadName, _usingTolerance, data[i], singleComparitor))
                except Exception as e:
                    pass # TODO
        elif self.testStep.multipleMeasurements:
            raise ValueError(f"Data and Expected lists disagree on length and therfore can not be evaluated. Data({len(data)}) != Expected({len(expected)}).")

        else:
            _completed: bool = False
            _usingTolerance: bool = False

            # If using a tolerance, deviations from a value will be calculated (ex. TYPE_EQ+/-5%)
            if None != expected.compareTol: _usingTolerance = True
            _completed = self.matchExpectTypeAndPreformOp(fromThreadName, _usingTolerance, data, expected)

        self.lastRecordedValue:any = data
        return _completed
    

    def updateStepResults(self, stepResult:bool|List[bool], durationOfTestInSeconds:float) -> None:
        '''
        .. versionadded:: 0.0
        .. versionchanged:: 0.4

        Create a new SingleTestReport object and append it to the testStepResults list
        inside the current UUT object inside of self.\n

        **Data will only be saved to a uut if in the test step json file the key: "Save-Result" is True**
        '''

        # This is the data that will be used later in the process to make reports and the WSJF file

        if self.testStep.multipleMeasurements:
            self.mainLogger.info(f"Generating MultiTestReport for current testStep: {self.testStep.name} with PASS result:{stepResult}")

            _listOfMeasurementData: List[multiMeasurementData] = []
            _totalStepPassed:bool = True

            # All variables should already be the same len. assuming OK here, otherwise raise err
            if None == self.lastRecordedValue and self.testStep.retry:
                self.runTestStep(self.stepToExec)
            elif None == self.lastRecordedValue:
                raise ValueError(f"No data to parse, last recorded data is: {self.lastRecordedValue}! Did the step verification fail?")
            if not (len(self.lastRecordedValue) == len(stepResult) == len(self.testStep.expect)):
                raise IndexError("Length disagreement between values, results, and expected!")

            for i,datapoint in enumerate(self.lastRecordedValue):
                _listOfMeasurementData.append(multiMeasurementData(
                    name            = self.testStep.expect[i].name,
                    result          = stepResult[i],
                    units           = self.testStep.expect[i].units,
                    recordedValue   = datapoint,
                    comparison      = self.testStep.expect[i]
                ))
                if not stepResult[i]: _totalStepPassed = False

            _report:MultiTestReport = MultiTestReport(
                stepName = self.testStep.name,
                stepIndex = self.testStep.step,
                result = _totalStepPassed,
                causedTotalFailure = False, # TODO - add ability for single step or submeasurement to cause cascade failure 1/2
                durationOfStepSeconds = durationOfTestInSeconds,
                measurements = _listOfMeasurementData
            )

            self.mainLogger.info(f"Generated MultiTestReport for testStep: {self.testStep.name}\n{_report}")

        elif not self.testStep.multipleMeasurements:
            self.mainLogger.info(f"Generating SingleTestReport for current testStep: {self.testStep.name} with PASS result:{stepResult}")

            _report:SingleTestReport = SingleTestReport(
                stepName=self.testStep.name,
                stepIndex=self.testStep.step,
                result=stepResult,
                causedTotalFailure=False, # TODO - add ability for single step or submeasurement to cause cascade failure 2/2
                comparison=self.testStep.expect,
                recordedValue=self.lastRecordedValue,
                units=self.testStep.expect.units,
                durationOfStepSeconds=durationOfTestInSeconds
            )

            self.mainLogger.info(f"Generated SingleTestReport for testStep: {self.testStep.name}\n{_report}")

        else:
            raise ValueError(f"Value of self.testStep.multipleMeasurements is invalid! Value: {self.testStep.multipleMeasurements}, type: {self.testStep.multipleMeasurements.__class__}")

        # Finally, add the generated report object to the UUT object by slot
        self.UUTsBySlot[self.testStep.slotIndex].testStepResults.append(_report)
        self.mainLogger.info("Added report to UUT object.")

        return None
    

    def determineFinalResult(self, uutSlot:int) -> None:
        """
        .. versionadded:: 0.0.3
        .. versionchanged:: 0.0.3

        Determine and update the final result for a single UUT
        """

        for test in self.UUTsBySlot[uutSlot].testStepResults:
            if test.causedTotalFailure and not test.result:
                self.UUTsBySlot[uutSlot].overallResult = False
                return None
        
        self.UUTsBySlot[uutSlot].overallResult = True

        return None


    def getUUTdetails(self) -> tuple:
        '''
        .. versionadded:: 0.0
        .. versionchanged:: 0.0

        Gets all information from the testware.UUT object (minus testStep details) and
        returns it inside a tuple for the UI thread to receive.

        All UUT information is transformed into kwargs inside a dict.

        Needs to return data in the format: ("UI", ("Method", <methodName:str>, {kwargs}))
        '''

        return (
            UI_THREAD_NAME,
            (
                THREAD_METHOD,
                UI.CLI_UI_PRINT_UUT_DETAILS,
                {
                    "slot":self.UUTsBySlot[self.testStep.slotIndex].testSlot,
                    "model":self.UUTsBySlot[self.testStep.slotIndex].model,
                    "sn":self.UUTsBySlot[self.testStep.slotIndex].serialNumber,
                    "rev":self.UUTsBySlot[self.testStep.slotIndex].rev,
                    "fixtureName":self.UUTsBySlot[self.testStep.slotIndex].fixtureName,
                    "fixtureSN":self.UUTsBySlot[self.testStep.slotIndex].fixtureSerialNumber,
                    "batchSN":self.UUTsBySlot[self.testStep.slotIndex].batchSerialNumber,
                    "user":self.UUTsBySlot[self.testStep.slotIndex].user,
                    "miscInfo":self.UUTsBySlot[self.testStep.slotIndex].miscInfo,
                    "subUnits":self.UUTsBySlot[self.testStep.slotIndex].subUUTs
                }
            )
        )
    

    def reportLastStep(self) -> tuple:
        '''
        .. versionadded:: 0.0
        .. versionchanged:: 0.0

        Gets the details of the very last step (saved to the uut object) and displays it on the CLI UI in the following format:\n
        `{Test Step Name}....//....{PASSED/FAILED}`\n

        *Note this will not show the value of recorded data to the user on the CLI UI*
        '''

        # Get details of the last step - only steps that were saved will be accessable
        lastSavedStep: SingleTestReport|MultiTestReport = self.UUTsBySlot[self.testStep.slotIndex].testStepResults[len(self.UUTsBySlot[self.testStep.slotIndex].testStepResults) - 1]

        if isinstance(lastSavedStep, MultiTestReport):
            self.mainLogger.debug(f"Showing the user the result of the last preformed multimeasurement step: {lastSavedStep}")

            measurements = lastSavedStep.measurements
            namesToShow:List[str] = []
            resultsToShow:List[bool] = []
            valuesToShow:List[any] = []

            for measurement in measurements:
                measurement: multiMeasurementData = measurement
                namesToShow.append(measurement.name)
                if measurement.result:
                    resultsToShow.append("PASSED")
                else:
                    resultsToShow.append("FAILED")
                valuesToShow.append(measurement.recordedValue)

            # TODO - use payload object for consistancy
            return (
                UI_THREAD_NAME,
                (
                    THREAD_METHOD,
                    UI.CLI_UI_PRINT_INFORMATION_NO_SPACER,
                    {"param":str(namesToShow)[1:-1], "data":str(resultsToShow)[1:-1], "value":str(valuesToShow)}
                )
            )
        
        else:
            if lastSavedStep.result:
                result = "PASSED"
            else:
                result = "FAILED"

            self.mainLogger.debug(f"Showing the user the result of the last preformed singlemeasurement step: {lastSavedStep}")
            # TODO - use payload object for consistancy
            return (
                UI_THREAD_NAME,
                (
                    THREAD_METHOD,
                    UI.CLI_UI_PRINT_INFORMATION_NO_SPACER,
                    {"param":lastSavedStep.stepName, "data":result, "value":lastSavedStep.recordedValue}
                )
            )
    

    def reportToUserPassFail(self) -> tuple:
        '''
        .. versionadded:: 0.0
        .. versionchanged:: 0.0

        Gets the overall status of a UUT from the testware.UUT object.
        This is returned as a tuple to be passed to the UI thread with the
        corresponding UUT information.\n

        This is typically called at the end of the test step file in post-test-steps.
        '''

        self.mainLogger.debug("Showing the user the final result of the UUT")
        
        # TODO - use payload object for consistancy
        return (
            UI_THREAD_NAME,
            (
                THREAD_METHOD,
                UI.CLI_UI_PRINT_PASS_FAIL,
                {"overallPF":self.UUTsBySlot[self.testStep.slotIndex].overallResult}
            )
        )
    

    def makeUUTReports(self) -> None:
        '''
        .. versionadded:: 0.3
        .. versionchanged:: 0.3

        Impliments NewReport class to be called by a MAIN THREAD method step
        **If a connection to the internet can not be found, this will fail and no report will be saved!**
        '''
        self.mainLogger.info("Generating UUT reports")

        reporter: NewReport = NewReport(os.path.join(os.getcwd(), "configurations", self.SubConfigurations["Reporting-Configuration"]))
        try:
            watsUploader = WATS(os.path.join(os.getcwd(), "configurations", self.SubConfigurations["WATS-Reporting-Configuration"]), self.UUTsBySlot)
            watsUploader.upload()
            self.mainLogger.info(f"WSFJ Uploaded:\n{watsUploader.wsjfToUpload}")
            self.mainLogger.info("WATS upload done.")
        except Exception as e:
            self.mainLogger.exception(f"ERROR UPLOADING TO WATS: {e}")

        for unitUnderTest in self.UUTsBySlot:
            try:
                reporter.generateAndSaveReport(unitUnderTest)
            
            except Exception as e:
                self.mainLogger.exception(f"When making UUT report for {unitUnderTest.serialNumber}, an exception occured: {e}")
                raise NotImplementedError # TODO

        return None


    def uploadLogs(self, logPath:str, logName:str) -> None:
        '''
        .. versionadded:: 0.3
        .. versionchanged:: 0.3

        Implimentation of the NewReport._pushSharePointViaREST
        method to upload a copy of the textfixture logs to a DIR on Sharepoint online specisifed via a config.\n
        **If a connection to the internet can not be found, this will fail and no report will be saved!**
        '''

        reporter: NewReport = NewReport(None)

        with open(os.path.join(os.getcwd(), 'configurations', self.SubConfigurations["Reporting-Configuration"]), 'r') as file:
            cloudPath: str = json.load(file)["Logs"]

        try:
            reporter._pushSharePointViaREST(os.path.join(logPath, logName), cloudPath)

        except Exception as e:
            self.mainLogger.exception(f"When pushing logs to SP Online, the following exception occured: {e}")
            raise NotImplementedError # TODO

        return None
    

    def sendUUTObjectToProcess(self, returnToProcessName:str|None=None, returnToMethod:str|None=None) -> tuple:
        '''
        
        '''

        return (
            returnToProcessName,
            (
                THREAD_METHOD,
                returnToMethod,
                [self.UUTsBySlot[self.testStep.slotIndex]]
            )
        )
    

    def addMiscInfoToUUT(self, infoToAdd:miscInfo|List[miscInfo]) -> None:
        """
        .. versionadded:: 0.4
        .. versionchanged:: 0.4

        :param infoToAdd:
        :returns: None
        :rasies IndexError: When the index of the UUT object is invalid. (ex only one slot is configured but #2 was selected)
        :rasies ValueError: When the argument for infoToAdd is not a miscInfo object or list of.
        """

        if isinstance(infoToAdd, miscInfo) or isinstance(infoToAdd, list):
            pass
        else:
            raise ValueError("Passed object is not a valid miscInfo object or list!")
            
        try:
            if isinstance(infoToAdd, list):
                for infoElement in infoToAdd:
                    self.UUTsBySlot[self.testStep.slotIndex].miscInfo.append(infoElement)

            else:
                self.UUTsBySlot[self.testStep.slotIndex].miscInfo.append(infoToAdd)

        except IndexError as e:
            self.mainLogger.exception(e)
            raise e

        return None

      
    def addSubUnitToUUT(self, subUnitToAdd:subUUT|List[subUUT]) -> None:
        '''
        .. versionadded:: 0.4
        .. versionchanged:: 0.4

        :param subUnitToAdd: a subUUT object or list of, to be updated into the currently selected (by test step file) UUT object according to SLOT #.
        :returns: None - nothing to return
        :raises IndexError: When the index of the UUT object is invalid (ex. only one slot is configured but #2 was selected)
        :raises ValueError: When the argument for the subUUT is not a subUUT object.
        '''

        if isinstance(subUnitToAdd, subUUT) or isinstance(subUnitToAdd, list):
            pass
        else:
            raise ValueError("Passed object is not a valid subUUT object or list!")

        try:
            if isinstance(subUnitToAdd, list):
                for subUnit in subUnitToAdd:
                    self.UUTsBySlot[self.testStep.slotIndex].subUUTs.append(subUnit)
                    
            else:
                self.UUTsBySlot[self.testStep.slotIndex].subUUTs.append(subUnitToAdd)

        except IndexError as e:
            self.mainLogger.exception(e)
            raise e

        return None
    

    def sleepStep(self, sleepTime:float) -> None:
        """
        .. versionadded:: 0.2
        .. versionchanged:: 0.2

        ..HINT:: This method is to be used by a test step.
        """

        time.sleep(sleepTime)

        return None


################################################################

## OTHER CODE ##

################################################################
 
# EOF