from src.AEMtestware import AEMtestware
from src.Testware_Exceptions.AEMtestwareException import AEMtestwareException
from src.Core_Testware.UnitUnderTest.UUT import UUT
from src.Core_Testware.TestSteps.testStepDecoder import TestStepDecoder as TSdecoder
from src.Core_Testware.TestSteps.testStepDecoder import payload
from src.TestwareConstants import *

import datetime, logging, os, json, time, sys
from multiprocessing import Process, Queue
from typing import List
from subprocess import check_output, STDOUT


def listener(queue:Queue, minLevel:str, logName:str, logPath:str) -> None:
    '''
    This method is the target for a special subthread/process that the main thread will always create.
    It's role is to be the listener for messages on the Queue. The queue it is passed is designed for
    use with logging.handlers.QueueHanlder objects (ex. a logger in any thread/process can use the queue
    object to post messages to as it is an address in mem. that this method will keep tabs on and save to all
    logging file/stream handlers).
    '''
    
    root = logging.getLogger()
    formatter = logging.Formatter(fmt="Logger Name/Process: [%(name)s][%(process)6d] | [%(levelname)-8s] | Path: %(filename)s -> %(funcName)s -> %(lineno)d | Time: %(created).4f || Message: %(message)s")


    handler = logging.FileHandler(os.path.join(logPath, logName), 'w', 'utf-8')
    handler.setFormatter(formatter)
    root.addHandler(handler)
        
    root.setLevel(getattr(logging, minLevel)) # Switch out the str for logging equivilent item (ex. DEBUG for logging.DEBUG)

    root.info("STARTED ROOT LISTENER")
    
    while True:
        if queue.empty(): continue
        try:
            record:logging.LogRecord = queue.get()
            if None == record: break # Sentinal
            logger = logging.getLogger(record.name)
            if getattr(logging, record.levelname) >= root.level:     # Only handle the record if the primary root logger is set for a level less than or equal to the record level
                logger.handle(record)
        except Exception as e:
            root.exception(e)


def resetI2CDriverOnStart() -> None:
    """
    
    """

    activeI2CDrivers:List[bytes] = []

    response:bytes = check_output(
        args = "kmod list | grep i2c",
        stderr = STDOUT,
        shell = True
    )

    lines = response.split(b'\n')
    for line in lines:
        activeI2CDrivers.append(line.split(b' ')[0])

    for driver in activeI2CDrivers:
        code = os.system(f"sudo modprobe --remove {driver.decode(encoding='utf-8')}")
        if 0 != code: 
            raise SystemError(f"When running kernal module modification, got returned code of:{code}, expected 0! FATAL.")
        
        code = os.system(f"sudo modprobe {driver.decode(encoding='utf-8')}")
        if 0 != code: 
            raise SystemError(f"When running kernal module modification, got returned code of:{code}, expected 0! FATAL.")

    return None

def main():
    print("Starting AEM Testware, please wait....")

    logLevel:str = ""
    logPath: str = ""
    fixtureName: str = ""
    masterCfgPath:os.path = os.path.join(os.getcwd(), "configurations", "main_configuration.json")

    with open(masterCfgPath, 'r') as file:
        config = json.load(file)

    logLevel = config["Logging-Level"]     # Gets the desired logging level for all loggers based on configuration file as str
    logPath = config["Logging-Path"]
    fixtureName = config["Fixture-Name"]

    logName = f"{fixtureName}-TMLog-{logLevel}-{datetime.datetime.now().isoformat().replace('/', '-').replace(':', '-')}.txt"

    queue = Queue(-1)                                                   #
    listenerProcess = Process(target=listener,                          #
                              args=(queue,logLevel,logName, logPath))   #
    listenerProcess.start()                                             #
    time.sleep(0.01)                                                    # Allow the sub-thread/process time to spin-up before putting it to use

    # TODO need a logger object in this primary process

    #resetI2CDriverOnStart() # RESET The I2C bus by unloading and loading the Linux Kenral module for I2C

    testware = AEMtestware(masterCfgPath, queue)            # Create an instance of the testware class using the queue for logging and master config

    for threadName in testware.activeThreads.keys():        #
        testware.updateThreadState(threadName, "UNKNOWN")   # Defualt all thread status' to UNKNOWN until reported otherwise

    # Main loop local-use variables
    _breakCondition: bool = False
    _carryMethodInit: bool = False
    _carryRepliesToCaller: bool = False
    _carryCallerName:str = ""
    _carryOccurred:bool = False
    _carryBlocking:bool = False
    _startOfNewTest: bool = False # use this to prevent doing anything until the target thread indicates it is running the task
    responses: list = None
    stepPassedComparison: bool = False
    currentStepIndex: int = 0
    isFirstLoop: bool = True
    totalTestTimeStart: float = time.time()
    currentTestTimeStart: float = 0.0
    newPayload:payload|None = None

    testware.mainLogger.debug("Completed main thread set up.")
    
    #
    #
    #
    # $$$$ Main program loop $$$$
    while not _breakCondition:
        testware.mainLogger.debug(f"Starting a new loop through MAIN. Step Number: {currentStepIndex} Complete: {stepPassedComparison}")

        #
        # $$ First Loop Segement - Only runs once, sentinal skips it if we have already done this $$
        #

        testware.mainLogger.debug(f"Checking if this is the very start: {isFirstLoop}")
        if isFirstLoop:
            testware.mainLogger.info("Step 0 found - starting with pre-test steps!")
            testware.mainLogger.debug("Delay - waiting for threads to settle.")
            time.sleep(0.05)
            for i in range(0, len(testware.UUTsBySlot), 1):
                testware.UUTsBySlot[i].startDatetime = datetime.datetime.now()
            testware.runTestStep(0)
            isFirstLoop = False

        #
        # $$ Look for and receive message from a subthread based on their assigned priority level $$
        #
        
        try:                                                                                                # Follows the flow:
            messageTuple = testware.rxMessageFromThreadBasedOnPriority()                                    # 1. Get a message for the first thread that sent something by DESC priotiy
            if None == messageTuple: pass                                                                 # 2. Either unpack or skip depending if we got any data
            else: responses,rxedFromThread = messageTuple                                                # 3. Move to the next chunk of main loop to determine what to do with the received messages.
            testware.mainLogger.debug(f"Response list for this loop: {responses} from: {rxedFromThread}")   #    If no message was received some of the following main loop chunks will be skipped.

        except Exception as e:
            pass

        if ("DEBUG" == logLevel) and (None != messageTuple):
            print(f"Active Message is: {responses} || from thread: {rxedFromThread}")

        # update if the new task has started (its a new task and the thread reports something other than IDLE)
        #likely in leu of ACK command structure I originally had - this is simplier but should help do the same thing
        if (_startOfNewTest) and (not testware.checkAndReportStateOfSubThreads([testware.testStep.payload.threadName])):
            _startOfNewTest = False

        #
        # $$ Parse collected data from subthread or verify action took by main thread was completed as expected $$
        #

        try:
            for i, response in enumerate(responses):                                                                                # Fllows the flow:
                testware.mainLogger.debug(f"Processing response type: {response[0]} from thread named: {rxedFromThread}")           # 1. Determine the type based on the response (STATS/FLAG/ACKN/METHOD/DATA)
                                                                                                                                    # 2. Take the correct action for the response type
                if THREAD_STATUS in response[0]:                                                                           # 3. Check that if we ran something using the MAIN THREAD
                    testware.updateThreadState(rxedFromThread, response[1])                                                         # 3A. Check the returned data is what we expected from the MAIN THREAD task                                                                     

                elif THREAD_CARRY_METHOD in response[0]:
                    if isinstance(response[1], tuple):
                        if not isinstance(response[1][0], payload): raise TypeError("Incorect type for a CARRY_METHOD")
                        else: newPayload: payload = response[1][0]        # response[1] should be a payload type for sending this request
                    elif isinstance(response[1], payload):
                        newPayload: payload = response[1]
                    else: raise TypeError("UNABLE TO DETERMINE TYPE")

                    if None != testware.originalPayload:
                        pass                                                    # This is a sequential carry
                    else:
                        testware.originalPayload = testware.testStep.payload    # Save the original non carry payload for final checks of test step

                    testware.testStep.payload = newPayload                      # Update the payload to the carry payload for processing the carry method

                    if newPayload.threadName == MAIN_THREAD_NAME:
                        mainThreadMethodToRun = getattr(testware, newPayload.message[0])
                        mainThreadMethodToRun(*newPayload.message[1:])
                        
                    else:
                        testware.txMessageToSubThread(
                            targetThread=testware.activeThreads[newPayload.threadName][0],
                            targetMessage=("Method", newPayload.message[0], (*newPayload.message[1:], rxedFromThread))                  # Give the thread preforming the next action the data + where it came from for the return
                        )
                        _carryMethodInit = True
                        
                        if (DUMMY_PLAYLOAD_DELIVER_TO != newPayload.deliverTo):
                            _carryRepliesToCaller = True
                            if testware.testStep.saveData:
                                _carryCallerName = rxedFromThread
                                _carryBlocking = True

                    testware.testStep.payload.deliverTo = newPayload.deliverTo                          # Update the deliver data to thread
                    #continue

                elif THREAD_FLAG in response[0]: pass #TODO

                elif (THREAD_DATA in response[0]):

                    # If a carry method was executed and data was returned,
                    # check to see if this is the caller giving us data
                    # this is the final check before we can proceed to another step
                    if _carryOccurred and _carryBlocking and (_carryCallerName == rxedFromThread):
                        _carryBlocking = False

                    _updateDataFromUI: bool = (UI_THREAD_NAME == rxedFromThread) and (type(response[1]) is tuple)

                    if _updateDataFromUI and ("UUT" in response[1][1]):
                        testware.mainLogger.debug(f"Found data from UI that needs to be used to update an object in testware: {response[1]}")
                        # Expecting the tuple to contain data that needs to be updated in the testware class
                        # EXAMPLE: response[1] = (<return data ex. str>, "UUT.serialNumber")
                        # [4:] --> removing the 'UUT.' from the attribute name

                        if "user" in response[1][1]:
                            setattr(testware.UUTsBySlot[testware.testStep.slotIndex], response[1][1][4:], response[1][0])

                        elif "subUnits" in response[1][1]:
                            testware.mainLogger.info(f"Adding subUnit(s) to UUT object based on slot.\nUUT Slot: {testware.testStep.slotIndex} with subUnits data: {response[1][0]}")
                            _retNone = testware.addSubUnitToUUT(response[1][0])
                            response = (THREAD_DATA, _retNone) # Clear the data to allow for compare to null - denotes done with subUUTs

                        # UUT base object or information to make the base object
                        elif "UUT_Std" in response[1][1]:
                            splitString:List[str] = response[1][0].split("/")
                            setattr(testware.UUTsBySlot[testware.testStep.slotIndex], "model", splitString[0])
                            setattr(testware.UUTsBySlot[testware.testStep.slotIndex], "rev", splitString[1])
                            setattr(testware.UUTsBySlot[testware.testStep.slotIndex], "batchSerialNumber", splitString[2]+splitString[3])
                            setattr(testware.UUTsBySlot[testware.testStep.slotIndex], "serialNumber", splitString[2]+splitString[3]+splitString[4])
                            response = (THREAD_DATA, response[1][0]) # Replace the tuple with only the actual data that was used for comparisons.

                        # Non standard barcode requires additional information to be avaliable in config
                        elif "UUT_nStd" in response[1][1]:
                            setattr(testware.UUTsBySlot[testware.testStep.slotIndex], "model", testware.nonStdBarcodeData["Model"])
                            setattr(testware.UUTsBySlot[testware.testStep.slotIndex], "rev", testware.nonStdBarcodeData["Rev"])
                            setattr(testware.UUTsBySlot[testware.testStep.slotIndex], "serialNumber", response[1][0])

                    elif _updateDataFromUI and ("ResetFixture" in response[1][1]):
                        testware.mainLogger.info("User has indicated if another unit should be run or to close the application.")
                        if N_RESET_FIXTURE_TRIGGER == response[1][0]: setattr(testware, "ResetFixture", False)
                        response = (THREAD_DATA, response[1][0])

                    elif _updateDataFromUI and ("" == response[1][1]):
                        testware.mainLogger.debug(f"Didnt find anything matching {response[1][1]} for setting attributes in main thread")
                        response = (THREAD_DATA, response[1][0]) # Rebuilt tuple with only the data we want to compare with

                    # THIS IS WHERE WE DETERMINE THE DATA OF THIS STEP IS A PASS OR FAIL
                    try:
                        if isinstance(response[1], tuple):
                            response = response[1][0]
                        else:
                            response = response[1]

                        # Reset the payload if we are done with carry method(s) and we have data from the original method
                        # Complete the step by preforming a passed comparison test on the final data from the caller
                        if (None == newPayload) or (None == testware.originalPayload): pass
                        elif (rxedFromThread == testware.originalPayload.threadName) and (not (_carryRepliesToCaller or _carryMethodInit)):
                            testware.testStep.payload = testware.originalPayload
                            testware.originalPayload = None
                            stepPassedComparison = testware.verifyStepIsComplete(rxedFromThread, response, testware.testStep.expect)

                        # The carry method was completed but the data needs to be returned to the caller process
                        if (not _carryMethodInit) and (testware.testStep.payload.deliverTo != DUMMY_PLAYLOAD_DELIVER_TO) and _carryRepliesToCaller:
                            testware.txMessageToSubThread(
                                targetThread=testware.activeThreads[testware.testStep.payload.deliverTo][0],
                                targetMessage=response
                            )
                            _carryRepliesToCaller = False # Reset this flag since we actioned it BUG - what about sequential calls from a process? they fail here...
                            _carryOccurred = True

                        elif (not _carryMethodInit) and (testware.testStep.payload.deliverTo != DUMMY_PLAYLOAD_DELIVER_TO) and not _carryRepliesToCaller:
                            stepPassedComparison = testware.verifyStepIsComplete(rxedFromThread, response, testware.testStep.expect)

                        elif (not _carryMethodInit) and (testware.testStep.payload.deliverTo == DUMMY_PLAYLOAD_DELIVER_TO) and not _carryRepliesToCaller:
                            continue # Dont need to do anything, the data was sent to the void, just proceed to the next message
                            
                    except Exception as e:
                        pass

                elif (None == testware.testStep.expect.type) and (THREAD_STATUS in response[0]):
                    try:
                        stepPassedComparison = testware.verifyStepIsComplete(rxedFromThread, None, None)
                    except Exception as e:
                        pass

                else: raise AEMtestwareException
                responses.pop(i)

            if (MAIN_THREAD_NAME == testware.testStep.payload.threadName):
                testware.mainLogger.debug("Ran something in the main thread")
                stepPassedComparison = testware.verifyStepIsComplete(MAIN_THREAD_NAME, testware.mainThreadMethodReturnData, testware.testStep.expect)
                if stepPassedComparison:
                    _startOfNewTest = False
     
            # Reset the payload since we are done with the main thread
            if (MAIN_THREAD_NAME == testware.testStep.payload.threadName) and (None != testware.originalPayload):
                testware.testStep.payload = testware.originalPayload
                testware.originalPayload = None
           

        except Exception as e:
            testware.mainLogger.exception(e)
            pass #TODO - handle this exception

        # update if the carry method is being done now (ex. the new thread has reported RUN)
        if _carryMethodInit and not testware.checkAndReportStateOfSubThreads([testware.testStep.payload.threadName]):
            _carryMethodInit = False

        #
        # $$ Preform action based on completetion status and what thread/testStep conditions we have in use $$
        #

        # Create common check variables for better readability in if-else blocks
        _failedComparisonAndBlocking: bool =        (testware.testStep.block) and (not stepPassedComparison)
        _failedComparisonAndNonblocking: bool =     (not stepPassedComparison) and (not testware.testStep.block)
        _threadIsNotDoneAndBlocking: bool =         (not testware.checkAndReportStateOfSubThreads([testware.testStep.payload.threadName])) and (testware.testStep.block)
        _threadIsDoneAndComparisonPassed: bool =    (stepPassedComparison) and (testware.checkAndReportStateOfSubThreads([testware.testStep.payload.threadName]))
        _threadIsDone: bool =                       (testware.checkAndReportStateOfSubThreads([testware.testStep.payload.threadName]))
        _notTheUIThread: bool =                     (UI_THREAD_NAME != testware.testStep.payload.threadName)
        _isTheUIThread: bool =                      (UI_THREAD_NAME == testware.testStep.payload.threadName)
        _isTheMAINThread:bool =                     (MAIN_THREAD_NAME == testware.testStep.payload.threadName)
        _saveToUUT: bool =                          testware.testStep.saveData
        _shouldRetry: bool =                        testware.testStep.retry
        _uiThreadIsDone: bool =                     testware.checkAndReportStateOfSubThreads(["UI"])
        _isNotDeliveredToBlankThread: bool =        (testware.testStep.payload.deliverTo != "_")


        if _carryBlocking: continue
        
        elif _isTheMAINThread and _failedComparisonAndBlocking:                               # Check:
            continue                                                                            # 1. Using the MAIN THREAD.
                                                                                            # 2. This action should be done before we proceed (blocking).
                                                                                            # 3. The action has not been completed yet.

                                                                                            # Do:
                                                                                            # 1. make no changes as the next chunk of main loop will re-run the current test step since we did not change it.


        elif _threadIsNotDoneAndBlocking or _carryMethodInit or _startOfNewTest:                                                   # Check:
            continue                                                                        # 1. The target or in-use thread has not reported back in an IDLE state (ex. its still running).
                                                                                            # 2. This action should be done before we proceed (blocking).

                                                                                            # Do:
                                                                                            # 1. Nothing - skip the rest of the checks as they are not needed or could cause issues. Proceed to next main loop.

        elif _isTheUIThread and _uiThreadIsDone and stepPassedComparison:
            currentStepIndex += 1
            _startOfNewTest = True

        elif _threadIsDoneAndComparisonPassed and _notTheUIThread:                          # Check:
            if _saveToUUT: testware.updateStepResults(                                      # 1. Data passed validation
                stepResult=stepPassedComparison, # PASS                                     # 2. The target or in-use thread has reported back saying its complete its work.
                durationOfTestInSeconds=time.time() - currentTestTimeStart                  # 3. The Thread was not the UI.
            )
            currentStepIndex += 1                                                           # Do:
            _startOfNewTest = True
                                                                                            # 1. Increment the test step to the next test, match case will run the next steps.
                                                                                            # 2. Update the step results so they are stored in the UUT object.
                                                                                                                                                    
        elif _failedComparisonAndNonblocking and _threadIsDone and _notTheUIThread:         # Check:
            if _saveToUUT: testware.updateStepResults(                                      # 1. Data failed validation
                stepResult=stepPassedComparison, # FAIL                                     # 2. This action is non-blocking
                durationOfTestInSeconds=time.time() - currentTestTimeStart                  # 3. The thread who was responsible for the action has reported IDLE
            )                                                                               # 4. The thread who preformed the action is not the UI thread (and therefore should be an actual test)
            currentStepIndex += 1
            _startOfNewTest = True

        elif _failedComparisonAndBlocking and _threadIsDone and _notTheUIThread and _isNotDeliveredToBlankThread and not _carryMethodInit:
            if _saveToUUT: testware.updateStepResults(
                stepResult=stepPassedComparison, # FAIL
                durationOfTestInSeconds=time.time() - currentTestTimeStart
            )
            currentStepIndex += 1
            _startOfNewTest = True

        elif _failedComparisonAndNonblocking and (not testware.testStep.block):             # Check: #TODO - This should fail the current step and move on
            sys.exit() # handle when something comes back with not complete and we are not retyring

        elif None == stepPassedComparison:                                                  # Check # TODO - Checking the current step return value has failed - go to previous test step and try again
            pass # Handle when a step check fails
        
        elif _shouldRetry and _failedComparisonAndBlocking:
            testware.runTestStep(currentStepIndex)  # step failed but should be redone
            continue

        else:                                                                               # Check # TODO - Critical failure
            continue # Something went wrong - lets catch an error here. # TODO

        #
        # $$ Based on the current step index (just incremented or the same) run the corresponding test step, if the test step is out of range, we increment the phase and loop again to run the new step on the next loop $$
        #

        try:
            currentTestTimeStart = time.time()                                  # Start the "timer" for how long a testStep takes to complete.

            testware.threadStates[testware.testStep.payload.threadName] = "WAIT FOR NEXT LOOP"

            #match testware.testPhase:
            if testware.testPhase == PRE_TEST_PHASE:                                   # When inside of the Phase: Pre-Test
                stepPassedComparison = False
                if None == testware.runTestStep(currentStepIndex):          # Open the test_Step.json file and decode the step of index currentStepIndex    
                    testware.testPhase = MAIN_TEST_PHASE                    # If this decode failes (ex. a handled out of index range error is raised)
                                                                            # Set the testware phase to the next in sequence and reset the index
                    currentStepIndex = 0                                    # This causes a small delay on the UI but will then execute the next phase on the next main loop
                                                                            # [ ] - Room for improvement in the future, should not be delayed by a whole loop of main loop, could also read steps into memory
            if testware.testPhase == MAIN_TEST_PHASE:
                stepPassedComparison = False
                if None == testware.runTestStep(currentStepIndex):
                    testware.testPhase = POST_TEST_PHASE
                    currentStepIndex = 0

                    for i in range(0, len(testware.UUTsBySlot), 1):
                        testware.UUTsBySlot[i].endDatetime = datetime.datetime.now()
                        testware.UUTsBySlot[i].durationOfRun = (testware.UUTsBySlot[i].endDatetime - testware.UUTsBySlot[i].startDatetime).total_seconds()
                        testware.determineFinalResult(i)
                    
                    testware.makeUUTReports()
                    testware.uploadLogs(logPath, logName)

            if testware.testPhase == POST_TEST_PHASE:
                stepPassedComparison = False
                if None == testware.runTestStep(currentStepIndex):

                    if testware.ResetFixture:
                        testware.testPhase = PRE_TEST_PHASE
                        testware.UUT = UUT(
                            model = None,
                            serialNumber = None,
                            fixtureName = testware.fixtureName,
                            fixtureSerialNumber = None,
                            user = None,
                            testStepResults = [],
                            overallResult = False,
                            durationOfRun = None,
                            startDatetime = None,
                            endDatetime = None
                        )
                        currentStepIndex = 0

                    else:
                        for thread in testware.activeThreads:
                            testware.activeThreads[thread][0].terminate()

                        _breakCondition = True
                        break

        except Exception as e:
            if isinstance(e, UnboundLocalError): raise e
            pass #TODO - handle this error

        time.sleep(0.01)       # Included for correct logging, if the logging queue is sent too much data too fast it can fail

        #
        # $$ END OF MAIN LOOP $$
        #

    sys.exit(0)


if __name__=="__main__":
    main()