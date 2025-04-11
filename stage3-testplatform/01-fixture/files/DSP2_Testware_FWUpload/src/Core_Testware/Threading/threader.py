################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: threader.py
# | Date: 2024-08-07
# | Rev: 1
# | Change By: Everly Larche
# | ECO Ref:
#  ----------------
# | Project Name: AEM Test & Measurement Platform
# | Developer: Everly Larche
# | File Description: To handle communications between application threads/components
#  ----------------
################################################################
################################################################

## LIBRARY USE // EXPECTED INPUT/OUTPUT AND LIMITATIONS ##

# Threader.py is to serve as the base of each child or sub-thread of the main
# testware thread spawned by running main.py.
#
# Two classes are built in this file and serve the following purposes:
# 1. Threader
# - Starts as an object inside the Main-Thread and creates the framework for implimenting the Python multiprocessing module
# - Inherits targetWrapper and its functions
# - When the Threader object is first created, it is passed an instance of a class and creates a list of methods from the class it was passed
# -- These listed methods will be executable when the instance of Threader is moved into a sub-thread
# - Sub-threads will communicate with the main-thread via a "pipe" connection where duplex is supported. Objects can be moved between threads.
#
# 2. targetWraper
# - Is designed to be the "main" loop of the sub-thread. The loop should follow the following pattern:
# - A) Enter _run()
# - B) If no method is desegnated to be execuated, exit run and wait for a message from the main-thread. Else:
# - C) Execute the designated method inside of _run() and use kwargs if applicable. Return data from the method if applicable to the main-thread.
# - D) If execution failed, inform the main thread and handle the error.
# - E) Continue waiting for the next message from the main thread and repeat.
#
#
# Note: The main thread can kill the sub-thread through joining it back into the main thread.


################################################################

## SUBCOMPONENT IMPORTS ##
import logging.handlers
import multiprocessing
import multiprocessing.connection
import logging, time, sys, os, datetime
from collections.abc import Iterable

from .AEM_threadingException import AEM_ThreadException as AEM_threadingException
from .AEM_threadingException import customRaiser

################################################################

## CLASS DEFINITION AND METHODS ##
def generateTargetWrapper(superClass, loggingQeue:multiprocessing.Queue, loggingLevel, pipe:multiprocessing.connection.Connection, name:str, testwareName:str, methods:dict, args=None):

    class targetWrapper(superClass):
        '''
        targetWrapper is a class that is designed to act the the "main loop" of the sub-thread/process.

        After initialization, which happens during the start of the sub-thread/process, _run() is called and will initate the main loop.
        Typically the two most used methods will be:
            - _run() which will execute any passed objects if runnable
            - waitForNextTask() which will wait until data is present in the pipe from the main thread. If a method, will call _run()
        '''

        def __init__(self, loggingQueue:multiprocessing.Queue, loggingLevel, pipe:multiprocessing.connection.Connection, name:str, testwareName:str, methods:dict) -> None:
            '''
            Sets up the sub-thread/process as initiated from the Threader class.
            '''

            self.name = name # Save the name of the process to the process for reference
            
            # Set up logger for the sub-thread
            handler:logging.Handler = logging.handlers.QueueHandler(loggingQueue)
            root:logging.Logger = logging.getLogger()
            root.addHandler(handler)
            root.setLevel(getattr(logging, loggingLevel))

            root.debug("Collected root logger in sub-thread")
            
            # Get nammed logger for the sub-thread as a child of root
            self.twLogger = logging.getLogger(f"{name}~twLogger")
            self.twLogger.debug("Collected named logger in sub-thread.")

            # Set classwide variables
            self.subThreadConnection: multiprocessing.connection.Connection = pipe
            self.testwareName:str = testwareName
            self.methods: dict = methods

            # Complete the setup and move on to the _run() loop of the sub-thread
            if (None != args) and (not isinstance(args, Iterable)): super().__init__(args)
            elif (None != args) and (isinstance(args, dict)): super().__init__(**args)
            elif (None != args) and (isinstance(args, Iterable)): super().__init__(*args)
            else: super().__init__()

            self.twLogger.debug("targetWrapper __init__() done")
            self._run(None)

            return None # Included for completeness, _run() should not "return" back.
        

        def _reportHandledError(self, origninalErrCode:int, originalErrMessage:str, possibleReasonMessgae:str, PID:int, intention:str, retries:int=0) -> None:
            '''
            After sucessfuly handling an error condition and being able to carry out the desired task,
            this method will be called to report:
                1. statistics on the retry events
                2. What the issue is likely to have caused the error state
                3. What state the thread/process is now in
                4. What the thread/process intends to do moving forward
            '''
            self.twLogger.debug("Sending status and flag to main thread/process")
            self.txMessage(("STATUS", "SET"))
            self.txMessage(("FLAG", -2))

            self.twLogger.info("Sending dump report of handled error")

            _path:os.path = os.path.join('~', 'AEM', self.testwareName, 'Logs', 'reports')
            self.twLogger.debug(f"Path being used for report: {_path}")

            if not os.path.exists(_path): os.mkdir(_path)

            _isoDate = datetime.datetime.now().date().isoformat()
            _filePath:os.path = os.path.join(_path, f"{_isoDate}-HandledErrorReport-{PID}-{origninalErrCode}.txt")
            self.twLogger.debug(f"Filepath being used for report: {_filePath}")

            with open(_filePath, '+w', encoding="utf-8") as reportFile:
                reportFile.write("-"*20)
                reportFile.write("Handled Error Report".center(width=20, fillchar="-"))
                reportFile.write("\n\n")
                reportFile.write(f"Error Code:Message -> {origninalErrCode}:{originalErrMessage}\n")
                reportFile.write(f"Possible Reason For Failure: {possibleReasonMessgae}\n")
                reportFile.write(f"PID:{PID} || Retries:{retries} || Intention: {intention}\n\n\n")
                reportFile.write(f"Datetime: {datetime.datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}")

            self.twLogger.info(f"Dumped handled error report to file: {_filePath}")

            return None


        def _checkPipeConnectionError(self) -> bool:
            '''
            Checks the connection to the main thread using methods found inside
            the multiprocessing module of python 3.11.x

            Returns TRUE if there IS an issue with the pipe connection.
            '''

            # Check health of pipe with pipe var and multirpocessing class
            _isError:bool = True

            _canRead:bool = self.subThreadConnection.readable           # Should be TRUE
            _canWrite:bool = self.subThreadConnection.writable          # Should be TRUE
            _isClosed:bool = self.subThreadConnection.closed            # Should be FALSE

            if _canRead and _canWrite and not _isClosed: _isError = False

            self.twLogger.debug(f"When checking the pipe connection for errors, the following was found:\nReadable:{_canRead}\nWriteable:{_canWrite}\nConnection is Closed: {_isClosed}\n\nTherefore Error: {_isError}")

            return _isError
        

        def _waitAndReSend(self, message:tuple, retries:int = 5) -> bool:
            '''
            Will be called when the thread/process has enetered into an error state when
            it attempted to send data over the pipe to the main thread.

            If the pipe is intact (found via _checkPipeConnectionError()) we will wait and re-try
            to send the data on the pipe. If this fails, the application should fail out gracefully.
            We can not continue to run tests if a thread/process is misbehaving.

            Returns true if was able to send out the message.
            '''

            self.twLogger.info("Going to wait and try to re-send data to the main thread/process")

            _sent:bool = False
            _retryCount:int = 0

            try:
                while _retryCount <= retries:
                    self.twLogger.debug(f"Retry count for re-sending data to main thread/process: {_retryCount}")

                    self.txMessage(message)
                    #if self.waitForACKN():
                    #    _sent = True
                    #    break
                    #time.sleep(0.5)
                    #_retryCount += 1
                
            except Exception as e:
                self.twLogger.exception(customRaiser.raiseAEMexception(
                    errCode=-9999,
                    errMessage="UNABLE TO COMMUNICATE WITH MAIN THREAD/PROCESS AFTER CHECKING PIPE"
                ))
                self.twLogger.critical("UNABLE TO RECOVER KILLING THREAD/PROCESS")
                sys.exit()
            
            return _sent


        def waitForACKN(self, retires:int=10, waitTime:float=5.00) -> bool:
            '''
            After sending data to the main thread, this method will wait until it
            receives the all-good/Acknoledgement message from the main thread.

            A timeout is implimneted inside of this method as defined by arguments.
            '''

            return True

            _receivedACKN:bool = False

            for retry in range(0, retires, 1):
                self.twLogger.debug(f"Waiting for rxMessage to return 0 (ACKN), on retry: {retry}")

                if 0 == self.rxMessage():
                    _receivedACKN = True
                    self.twLogger.debug("ACKN received from main thread.")
                    break
                time.sleep(waitTime)

            return _receivedACKN


        def _run(self, action:str, methodName:str=None, arguments:dict=None) -> None:
            '''
            _run() will execute a method object that is passed to it during runtime.
            If no method is provided (as per the default case), the thread should wait for another message.
            '''

            # When initialy running this method for the first time, we break out and wait for the next message.
            # This also handles any cases where we enter _run() but have nothing to execute.
            self.twLogger.debug("Starting the _run() method.")

            # SENTINAL
            if "Method" != action:
                self.twLogger.debug("No method found in data passed to _run()")

                try:
                    _message:tuple = ("STATUS", "IDLE")
                    self.txMessage(_message)
                    #self.waitForACKN()
                    #self.waitNextTask()

                except Exception as e:
                    # Since this is an error with sending a message to the main thread,
                    # lets check that the pipe objects are valid and working. Then retry.
                    self.twLogger.exception(customRaiser.raiseAEMexception(
                        errCode=-10,
                        errMessage=e,
                    ))
                    
                    self.twLogger.warning("Checking the pipe for leaks...")

                    if not self._checkPipeConnectionError():                                                        # If there is no error with the pipe, lets try again just in case.
                        self.twLogger.info("No issue found with plumbing.")
                        self._waitAndReSend(_message, 5)

                    else:                                                                                           # If this is true, we cant correct this. We should re-start the application.
                        self.twLogger.critical("Found some leaks in the pipe terminating sub-thread/process...")
                        raise AEM_threadingException(
                            code=-9999,
                            message="CRITIAL ERROR PIPE MISSING"
                        )

                    self.twLogger.debug("Error seams to have been handled now.")
                    self._reportHandledError(
                        origninalErrCode=-10, 
                        originalErrMessage=e,
                        possibleReasonMessgae="MEM/POINTER issue? Python runtime interpreter issue? Main thread/process ignored message?",
                        PID=os.getpid(),
                        intention="CONTINUE EXECUTION",
                        retries=5
                    )

                finally:
                    self.waitNextTask()

            try:
                self.twLogger.debug("Sentinel passed. Running method.")
                self.twLogger.debug(f"Finding a method to match STR {methodName}")
                method = self.methods[methodName]

                if None == arguments:
                    self.twLogger.debug("No arguments found. Running only with self.")
                    _retFromCall = method(self)                                         # Run the desegnated method with only the self argument of the current instance
                elif not isinstance(arguments, dict):
                    self.twLogger.debug("Arguments passed are not dictLike, unpacking as itterable arguments")
                    _retFromCall = method(self, *arguments)
                else:
                    self.twLogger.debug("Arguments passed are key-word, unpacking as dict like arguments")
                    _retFromCall = method(self, **arguments)                               # Run the desegnated method with unpacked key-word arguments in addition to the self argument
                
                try:
                    try:
                        if (isinstance(_retFromCall, tuple)) and (len(_retFromCall) > 1) and _retFromCall[0] == "CARRY_METHOD":
                            self.twLogger.debug("Data was returned from the method object and includes another method to execute in another thread.")
                            self.txMessage(("CARRY_METHOD", _retFromCall[1:]))
                    
                        elif None != _retFromCall:
                            self.twLogger.debug("Data was returned from the method object - sending to main thread.")
                            self.txMessage(("DATA", _retFromCall))                          # If there is data to send back to the main thread label it DATA and send the message. Need to wait for ACKN from main thread before continuing.

                        elif None == _retFromCall:
                            self.twLogger.debug("None returned from method object - sending None to main thread for comparision.")
                            self.txMessage(("DATA", None))
                    
                        self.twLogger.debug("Done with _run() - cleaning up by sending IDLE notif. and then returning to wait for the next task.")

                        #self.waitForACKN()                                              # Wait for this to reutrn False. If we don't see anything in the pipe for us and its not an ACKN, we wait.

                    except TypeError or KeyError:
                        pass # _retFromCall has no len()

                    
                except Exception as e:
                    self.twLogger.exception(customRaiser.raiseAEMexception(
                        errCode=-10,
                        errMessage=e
                    ))

                    self.twLogger.warning("Trying to determine the status of the PIPE")

                    if not self._checkPipeConnectionError():
                        self.twLogger.info("No pipe leaks found, attempting to store and re-send the message to the main thread.")
                        try:
                            self._waitAndReSend()
                            self._reportHandledError()
                            self.txMessage(("FLAG", -2))
                        
                        except Exception as e:
                            self.twLogger.exception(customRaiser.raiseAEMexception(
                                errCode=-11,
                                errMessage=e
                            ))

                            sys.exit(-9999) # Close the process with an error code - this should cause the main thread to panic. Since we cant communicate, this is desired.

            except Exception as e:
                self.twLogger.exception(customRaiser.raiseAEMexception(
                    errCode=-20,
                    errMessage=e
                ))
                
                if None == _retFromCall: self.twLogger.warning("_retFromCall is NONE - was data expected?")
                self.txMessage(("FLAG", -1))
                self._reportHandledError(
                    origninalErrCode=-20,
                    originalErrMessage=e,
                    possibleReasonMessgae="There was an error running the target method, its likely it failed and returned None type to inidcate such.",
                    PID=os.getpid(),
                    intention="A FLAG for this thread/process was sent to the main thread, from this point we should set IDLE status and await further messages.",
                    retries=0
                )
                
            finally:
                try:
                    self.txMessage(("STATUS", "IDLE"))      # Inform the main thread that we are now done handling all execution and data and can receive another task.
                
                except Exception as e:
                    self.twLogger.exception(customRaiser.raiseAEMexception(
                        errCode=-10,
                        errMessage=e
                    ))

                    # DO NOT try to re-send as we likely already did that inside the txMessage method.
                    # Just report and close thread/process as a PIPE error is likely.
                    self._reportHandledError(
                        origninalErrCode=-10,
                        originalErrMessage=e,
                        possibleReasonMessgae="Tried to TX data to the main thread, likely already re-tried and failed or found an issue with the data pipe.",
                        PID=os.getpid(),
                        intention="Report error and kill thread/process.",
                        retries=0
                    )

            return None 
        

        def rxMessage(self) -> int|None:
            '''
            When a message is rx'ed - if calling a method, action it via _run().
            '''
            # Datatype must be pickleable, chose Tuple.
            try:
                _data:tuple = self.subThreadConnection.recv()
                if (len(_data) < 3) and ("Method" == _data[0]) and (None != _data[1]):      # If we have received a method to run and no arguments were required or given in the form of None
                    _data= (_data[0], _data[1], None)                                                      # set the 3rd index of _data to None such that _run() can handle the tuple correctly and run the <method> with only the self argument.

            except Exception as e:
                self.twLogger.exception(customRaiser.raiseAEMexception(
                    errCode=-10,
                    errMessage=e
                ))

                isError:bool = self._checkPipeConnectionError()
                if isError:
                    self._reportHandledError(
                        origninalErrCode=-10,
                        originalErrMessage=e,
                        possibleReasonMessgae="Tried to RX a message from MAIN THREAD, checked pipe and returned with an error. Lost connection?",
                        PID=os.getpid(),
                        intention="Kill thread/process.",
                        retries=0
                    )
                    sys.exit(-9999)

                else:
                    self._reportHandledError(
                        origninalErrCode=-10,
                        originalErrMessage=e,
                        possibleReasonMessgae="Tried to RX a message from MAIN THREAD, checked pipe and returned with no error. Timming issue?",
                        PID=os.getpid(),
                        intention="Continue with waiting for the next message.",
                        retries=0
                    )
                    return self.rxMessage()

            
            # Data structure:
            # [0] -> ("Method", "ACKN", "DISREG")
            # [1] -> (<method object>|None)
            # [2] -> (*args|None)

            match _data[0]:
                case "Method":
                    # The main thread has requested a method to be run in this sub-thread and should be executed with the arguments passed
                    try:
                        self.twLogger.debug("Matched _data[0] to being a method - inform the main thread/process we are starting to run a method")
                        #self.txMessage(("ACKN", None))                      # Inform MAIN THREAD we got the message okay.
                        self.txMessage(("STATUS", "RUN"))                   # Update the sub-thread' status with the main thread.
                        self._run(_data[0], _data[1], _data[2])             # Should not return from this, rather move on to waiting. Status will be updated in _run()
                        # BUG method gets run twice here
                        return None
                    
                    except Exception as e:
                        self.twLogger.exception(customRaiser.raiseAEMexception(
                            errCode=-30,
                            errMessage=e
                        ))
                        
                        isError = self._checkPipeConnectionError()

                        if isError:
                            # report error and kill
                            self._reportHandledError(
                                origninalErrCode=-30,
                                originalErrMessage=e,
                                possibleReasonMessgae="Likely an issue when trying to transmit to the main thread our new status or ACKN of method data.",
                                PID=os.getpid(),
                                intention="Kill thread/process - data pipe found to have errors.",
                                retries=0
                            )
                            sys.exit(-9999)

                        else:
                            # tx "DISREG" to main thread, update flag and report error
                            self._reportHandledError(
                                origninalErrCode=-30,
                                originalErrMessage=e,
                                possibleReasonMessgae="Likely an issue when running the target method which would have been handled previously.",
                                PID=os.getpid(),
                                intention="Inform the MAIN THREAD with a DISREG message and continue with waiting for the next task.",
                                retries=0
                            )
                            self.txMessage(("DISREG", None))

                #case "ACKN":
                    # ACKN - Acknoledge data from main thread
                    # Return 0 to show MAIN THREAD acknowledged our last message/data
                    #return 0

                case "DISREG":
                    # DISREG - Disregarded data sent by sub thread
                    # Return -1 to show no data was processed and an error condition was met
                    return -1

                case _:
                    self.twLogger.exception(customRaiser.raiseAEMexception(
                        errCode=-30,
                        errMessage="Defualt match case reached in match data[0]! RXed data will be DISREG!"
                    ))

            return None # Should not reach a return condition, however it is included for completeness. If this function returns its likely the sub-thread will expire.


        def txMessage(self, dataToTX:tuple) -> None:
            '''
            Send data in Tuple (pickleable) to main thread.
            '''

            # Data structureL
            # [0] - ("FLAG", "STATUS", "DATA")
            # [1] - (flagID|("CLEAR", "SET", "RUN", "IDLE")|any|None)

            if len(dataToTX) < 2:
                self.twLogger.exception(customRaiser.raiseAEMexception(
                    errCode=-40,
                    errMessage=f"Length of tuple too short to TX data! Message will be disregarded!\nMessage tried to send was: {dataToTX}"
                ))

            # Check if we are sending data pertaining to a FLAG and update the status accordingly.
            if "FLAG" == dataToTX[0]:
                try:
                    match dataToTX[1]:
                        case 0:                                     # Nothing to do with flag 0 - put in here for completeness/handling a zero state transition.
                            pass

                        case -2:                                    # -2 is indicating a handled error and that the program will now continue normally.
                            self.txMessage(("STATUS", "CLEAR"))
                        
                        case _:                                     # The defualt case indicates any status other than 0 or -2 which is indicitive of an error state being raised.
                            self.txMessage(("STATUS", "SET"))

                except Exception as e:
                    self.twLogger.exception(customRaiser.raiseAEMexception(
                        errCode=-40,
                        errMessage=e
                    ))
                
                    self._reportHandledError(
                        origninalErrCode=-40,
                        originalErrMessage=e,
                        possibleReasonMessgae=f"Tried to TX a flag and failed during the match case. Data was: {dataToTX}",
                        PID=os.getpid(),
                        intention="Call txMessage again and set the flag to -1.",
                        retries=0
                    )
                    return self.txMessage(("FLAG", -1))
            
            try:
                self.subThreadConnection.send(dataToTX)
        
            except Exception as e:
                self.twLogger.exception(customRaiser.raiseAEMexception(
                    errCode=-40,
                    errMessage=e
                ))

                isError = self._checkPipeConnectionError()

                if isError:
                    self._reportHandledError(
                        origninalErrCode=-40,
                        originalErrMessage=e,
                        possibleReasonMessgae=f"Tried to TX and failed. Status of pipe is BAD.",
                        PID=os.getpid(),
                        intention="Kill thread/process now",
                        retries=0
                    )
                    sys.exit(-9999)

                else:
                    self._reportHandledError(
                        origninalErrCode=-40,
                        originalErrMessage=e,
                        possibleReasonMessgae=f"Tried to TX and failed. Status of pipe is OKAY.",
                        PID=os.getpid(),
                        intention="Call wait and re-send to retry the data tx. Will re-try upto 5 times.",
                        retries=0
                    )
                    wasSent:bool = self._waitAndReSend(dataToTX)
                    self.twLogger.warning(f"Managed to re-send data: {wasSent}")
                    if not wasSent:
                        self.twLogger.critical(customRaiser.raiseAEMexception(
                            errCode=-9999,
                            errMessage="UNABLE TO RE SEND DATA KILLING THREAD/PROCESS"
                        ))
                        sys.exit(-9999)

            finally:
                self.twLogger.debug(f"Subthread txed data: {dataToTX}")
                return None 


        def waitNextTask(self) -> None:
            '''
            Serve as a blocking method, wait until a message is ready to be rx'ed.
            '''
            dataToRead:bool = False
            breakCondition: bool = False
            while not breakCondition:
                # Qurey if data is ready to be read from the pipe at 4Hz.
                # Loop breaks when data is found and rxMessage() is called.
                #self.twLogger.debug("Waiting - nothing to do")
                dataToRead = self.subThreadConnection.poll(0.0001)
            
                try:
                    if not dataToRead: continue
                    self.twLogger.debug("Have data to read and parse, attempting to read from pipe now.")
                    _ret = self.rxMessage()
                    self.twLogger.debug(f"return value from rxMessage while waiting was: {_ret}")

                    if -1 == _ret:
                        self.twLogger.exception(customRaiser.raiseAEMexception(
                            errCode=-60,
                            errMessage="Received a DISREG! Will continue to monitor for new messages." # [ ] - In future this should maybe retry an action if it fails.
                        ))

                except Exception as e:
                    self.twLogger.exception(customRaiser.raiseAEMexception(
                        errCode=-1,
                        errMessage=e
                    ))
                    
                    isError = self._checkPipeConnectionError()

                    if isError:
                        self._reportHandledError(
                            origninalErrCode=-1,
                            originalErrMessage=e,
                            possibleReasonMessgae="Something went wrong when handling a previous exception OR something bad happened while waiting for the next task. Found a bad pipe too - unhandeld pipe exception somewhere?",
                            PID=os.getpid(),
                            intention="Kill thread/process now"
                        )
                        sys.exit(-9999)

                    else:
                        self._reportHandledError(
                            origninalErrCode=-1,
                            originalErrMessage=e,
                            possibleReasonMessgae="Something went wrong when handling a previous exception OR something bad happened while waiting for the next task.",
                            PID=os.getpid(),
                            intention="Report the error to file and MAIN THREAD and continue"
                        )
                        self.txMessage(("FLAG", -1))
        
    return targetWrapper(loggingQeue, loggingLevel, pipe, name, testwareName, methods)


# --------------------------------------------------------------------------------------


class Threader():
    '''
    Serves as an object to manage the sub-thread/process inside of the main thread/process.

    Will facilitate the following:
        1. Finding methods to use in a supplied class that is to be run on the sub-thread/process
        2. Creating the sub-thread/process
        3. Logging records for communication to/from the sub-thread/process inside of the main thread/process
        4. Terminating and re-joining the sub-thread/process into the main thread/process when the application is done with it
    '''

    def __init__(self, targetClass:object, reportsTo: str, loggingQueue:multiprocessing.Queue, threadName:str, testwareName:str, logLevel:any, biDirectional:bool = True, cluserSize:int = 1, loggerObject:logging.Logger = None, args=None) -> None:
        '''
        Create new thread with datapipe and return to caller.
        Class object should contain new process ID and list of callable methods from within the target class being run as subprocess.

        Queue us used to move logging data between threads/processes and all report back to a particular sub-thread/process that handels logging to outputs.
        '''

        #Internal classwide vars
        self._targetClass:object = targetClass
        self._duplex:bool = biDirectional
        self._logLevel:any = logLevel
        self._clusterSize:int = cluserSize
        self._raiseCustomException:object = customRaiser.raiseAEMexception

        # Accessable class vars
        self.mainThreadConnection:multiprocessing.connection.Connection = None
        self.subThreadConnection:multiprocessing.connection.Connection = None
        self.methods:dict = {}
        self.subProcess:multiprocessing.Process = None
        self.logger:logging.Logger = loggerObject
        self.newThreadName:str = threadName
        self.loggingQueue:multiprocessing.Queue = loggingQueue
        self.testwareName:str = testwareName
        self.reportsToThread:str = reportsTo
        self.args = args

        # Run setup methods
        self.defineMethods()
        self.createPipe()

        # Determine how many workers/threads to create
        if 1 == self._clusterSize: self.createProcess()
        else: self.createParallel()

        return None


    def createPipe(self) -> None:
        '''
        Creates communication objects for main and sub thread.
        If original argument requires 2-way communication (duplex),
        it will be set here.
        '''
        self.logger.info("Creating pipe to child")
        pipe = multiprocessing.Pipe(duplex=self._duplex)

        #Set ends of pipe
        self.mainThreadConnection = pipe[0]
        self.subThreadConnection = pipe[1]

        return None


    def defineMethods(self) -> None:
        '''
        Validate callable methods are present that do not include "__" (dunder) in the
        mothd name. If no valid callable methods are found, the class is to terminate the setup process.
        Sets a dict of valid methods.
        '''
        self.logger.info("Looking for callable methods for child thread")
        #targetInstance = self._targetClass()
        for method_list_item in dir(self._targetClass):
            if method_list_item.startswith("__"): continue
            method = getattr(self._targetClass, method_list_item)
            if callable(method): self.methods[method_list_item] = method
            self.logger.debug(f"Found callable method: {method_list_item} in {self._targetClass}")
        
        if None == self.methods: self.terminate("No valid methods to call in target class")

        return None
        

    def createProcess(self) -> None:
        '''
        Create and start a new sub-thread using the target class.
        This thread will be idle until it is given commands via messaging.
        '''
        self.logger.info("Starting new thread with queue for logging")

        if None != self.args:
            self.subProcess = multiprocessing.Process(name=str(self._targetClass.__name__),
                                                  target=generateTargetWrapper,
                                                  args=(self._targetClass, self.loggingQueue, self._logLevel, self.subThreadConnection, self.newThreadName, self.testwareName, self.methods, self.args))
        # MAKE A NEW ONE HERE WITH ABILITY FOR MULTIPLE CUSTOM ARGS, or get process name inside of dynaic class
        else:
            self.subProcess = multiprocessing.Process(name=str(self._targetClass.__name__),
                                                  target=generateTargetWrapper,
                                                  args=(self._targetClass, self.loggingQueue, self._logLevel, self.subThreadConnection, self.newThreadName, self.testwareName, self.methods))
        
        self.subProcess.start()
        self.logger.debug("Thread started")

        return None


    def createParallel(self) -> None:
        '''
        NOT IMPLIMENTED
        '''

        # [ ] - Something to impliment in the future

        raise NotImplementedError
    

    def sendToSubThread(self, message:tuple) -> None:
        '''
        Serves as the method with the "MAIN THREAD" end of the pipe accessable, which also rests inside the MAIN THREAD
        for communication to the subthread/process. Follows a strict message pattern as tuple.
        '''
        
        self.logger.debug(f"Sending message to subthread: {message}")
        self.mainThreadConnection.send(message)


    def receiveFromSubThread(self) -> tuple|None|bool:
        '''
        Serves as the method with the "MAIN THREAD" end of the pipe accessable, which also rests inside the MAIN THREAD
        for communication from the subthread/process.

        Allows for an option where we are only looking for an acknoledgement signal from the subthread/process. If this is the
        case, the return type changes to bool.
        '''

        self.logger.debug("Looking for message from child thread")
        if not self.mainThreadConnection.poll(0.0005):
            _data = None                                            # Check if there is any data to read
        else:
            _data: any = self.mainThreadConnection.recv()

        return _data


    def terminate(self) -> None:
        '''
        Will immidently try to close/kill the subthread/process that is contained within this
        classes instance.

        This is only accessable from the MAIN THREAD to send a kill signal to the subthread/process.
        '''

        self.logger.debug("Trying to close the thread")
        self.subProcess.terminate()
        while self.subProcess.is_alive():
            pass
        self.logger.debug("Thread is no longer alive, release its resources back to the system")
        self.subProcess.close()

        return None


################################################################

## OTHER CODE ##

################################################################

# EOF