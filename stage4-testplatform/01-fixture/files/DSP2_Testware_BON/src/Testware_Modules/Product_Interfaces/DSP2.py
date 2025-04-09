################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: DSP2.py
# | Date: 2025-03-07
# | Rev: 1.0
# | Change By: Everly Larche
# | ECO Ref: LXP-369
#  ----------------
# | Project Name: DSP2.0 Bed-of-Nails
# | Developer: Everly Larche
# | File Description: Combine some tests into single steps or sub-sequences
#  ----------------
################################################################
################################################################

## LIBRARY USE // EXPECTED INPUT/OUTPUT AND LIMITATIONS ##

################################################################

## SUBCOMPONENT IMPORTS ##
from src.Testware_Modules.Protocols.RS232 import RS232
from src.Core_Testware.TestSteps.testStepDecoder import payload
from src.Core_Testware.UnitUnderTest.UUT import miscInfo
from src.TestwareConstants import THREAD_CARRY_METHOD, THREAD_METHOD, MAIN_THREAD_NAME, DUMMY_PLAYLOAD_DELIVER_TO

from typing import List
from multiprocessing import Process
import time

################################################################

## CLASS DEFINITION AND METHODS ##
class DSP2_Tests:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    # DSP 2.0 Test Class
    Product Interface class to support the testing of the Lx DSP 2.0 Base PCA in a Bed-of-Nails (BON) test fixture.

    Methods in this class that preform test step measurements need to be returned to this process and kept in memory until the
    particular test step call is done, then return the list of measurement data to the primary process where it will be compared to
    the expected value(s), or value range(s) and saved to the slected UUT slot object.
    """

    ### CONSTANTS ###

    ADC_OVERRIDE_12V:float  = 4.829011
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    The value passed to the ADC process API to scale the measured voltage based on HW for nominal 12V measurements.
    """

    ADC_OVERRIDE_5V:float   = 3.169506
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    The value passed to the ADC process API to scale the measured voltage based on HW for nominal 5V measurements.
    """

    ADC_OVERRIDE_3V3:float  = 3.169505
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    The value passed to the ADC process API to scale the measured voltage based on HW for nominal 3.3V measurements.
    """

    INTER_PROCESS_DELAY:float = 0.01
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    A delay used to wait from sending a message to a process in the queue and proforming an action in the present process.
    """

    ADC_SE_PROCESS_NAME:str     = "ADC_A"
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0
    """

    ADC_DIFF_PROCESS_NAME:str   = "ADC-B-DIFF"
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0
    """

    DIO_PROCESS_NAME:str        = "DIO_A"
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0
    """

    SDCARD_PROCESS_NAME:str     = "SD"
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0
    """
    
    ### CONSTANTS ###


    def __init__(self) -> None:
        return None
    

    def _sendProcessRequest(self, processName:str, methodName:str, args:list=[], returnDeliveryToThread:str=DUMMY_PLAYLOAD_DELIVER_TO, overrideDelay:int|None=None) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param processName: The string name of the process we are sending data to. This must match an active process to succseed.
        :param methodName: The method in the remote process to be called by name.
        :param args: Non-keyword argument list for the required args in `methodName` for the remote process. Self is not needed.
        :param returnDeliveryToThread: Points to where the returned data from the remote process (if any) should be put. If set to `DUMMY_PAYLOAD_DELIVER_TO` the response will be dropped in transit.
        :param overrideDelay: Override the pre-set delay between sending the message and continuing with the current process execution. Used to avoid contention.

        :raises RuntimeError: When the txMessage() function is not callable from the current scope. This can happen if this function is run outside the core testware environment.

        ## [Internal] - Send a message to process
        Following the conventions used in the test step json file,
        and subsequent decoder, package and transmit a message via the main process.

        The contents of this method are only avaliable during runtime.
        """

        if not callable(self.txMessage):
            raise RuntimeError(f"Unable to get the atrribute named: txMessage! Is this class being used with the correct dependcies at runtime?\nSelf dump:{self.__dict__}")
        else:
            args = [methodName] + args # prepend the method as the first arg for the process to action

            # Tx the tuple object the process handling in the main process expects
            self.txMessage((THREAD_CARRY_METHOD, payload(
                processName,
                THREAD_METHOD,
                args,
                returnDeliveryToThread
            )))
            if None == overrideDelay: time.sleep(self.INTER_PROCESS_DELAY)
            elif 0 == overrideDelay: pass
            else: time.sleep(overrideDelay)

        return None
    

    def _getProcessData(self, timeoutOverride:float=5.0) -> tuple:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param timeoutOverride: Defualts to 5 second timeout, but can be changed to any float value.

        :raises RuntimeError: When the `subThreadConnection` object is not within scope. This can happen if this function is run outside of the core testware scope.
        
        :returns: Tuple containing the raw, unaltered data from another process. This data should only be that of which we are expecting.

        ## Receive data from another process
        Assumes there will be data to receive, but times out after `timeoutOverride` seconds.

        Acts as an adjascent method to `self.rxMessage()`.
        rxMessage can't be used since it does other processing on the data, such as calling
        a method inside the process if the messages instructs as such. In this case, we need to
        collect data returned from a remote process and act upon it.

        Due to this, if this class is used outside the AEMtestware codebase, this function will fail
        as it relies on variables defined during startup.

        The contents of this method are only avaliable during runtime.
        """

        receivedData = None

        if not callable(self.subThreadConnection.recv):
            raise RuntimeError()
        else:
            timeStart:float = time.time()
            while (timeStart+timeoutOverride) > time.time():
                if not self.subThreadConnection.poll(0.000001): continue # Wait 1µs to see if there is data ready
                receivedData = self.subThreadConnection.recv()
                if None != receivedData: break

            if None == receivedData: receivedData = "-9999"

        return receivedData
    

    def test5VReg(self) -> List[float]:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :returns List[float]: A list of floating point measurements for the 5V rail

        ## 5V Regulation Tests
        By sending requests to other processes, with a class-wide adjustable delay between actions,
        preform the tests required to fufil the 5V multi-measurement step.

        ### Test flow:
        PoE is assumed applied as per prev. test step

        1. Load is off by defualt from Testware init
        2. ADC measurement on 5V line
        3. Apply load via a DIO
        4. ADC measurement on 5V line (repeat of 2)
        5. Disable the load via a DIO
        """

        _measurements:List[float] = []

        # Note: the `self.processName` variable is only accessable at runtime
        self._sendProcessRequest("ADC_A", "measureSignal", ["GOLD_ADC_A_SE_4", False, self.ADC_OVERRIDE_5V], self.name)
        _measurements.append(float(self._getProcessData()))

        self._sendProcessRequest("DIO_A", "writePin", ["DIO_A_3", True])
        
        self._sendProcessRequest("ADC_A", "measureSignal", ["GOLD_ADC_A_SE_4", False, self.ADC_OVERRIDE_5V], self.name)
        _measurements.append(float(self._getProcessData()))

        self._sendProcessRequest("DIO_A", "writePin", ["DIO_A_3", False])

        return _measurements
    

    def test3V3Reg(self) -> List[float]:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :returns List[float]: A list of floating point measurements for the 3V3 rail

        ## 3V3 Regulation tests
        ### Test flow:
        Same as the 5V test with only the ADC line changing for the measurement.
        """

        _measurements:List[float] = []

        self._sendProcessRequest("ADC_A", "measureSignal", ["GOLD_ADC_A_SE_2", False, self.ADC_OVERRIDE_3V3], self.name)
        _measurements.append(float(self._getProcessData()))

        self._sendProcessRequest("DIO_A", "writePin", ["DIO_A_3", True])
        
        self._sendProcessRequest("ADC_A", "measureSignal", ["GOLD_ADC_A_SE_2", False, self.ADC_OVERRIDE_3V3], self.name)
        _measurements.append(float(self._getProcessData()))

        self._sendProcessRequest("DIO_A", "writePin", ["DIO_A_3", False])


        return _measurements
    

    #def _WDItoggle(self, processName:str, netName:str, period:float) -> None:
    #    """
    #    .. versionadded:: 1.0
    #    .. versionchanged:: 1.0
    #
    #    :param self: A copy of the active self object of which contains the needed pipe connections (mem addresses of process message queues)
    #    :param processName: The target process name for preforming the toggles on.
    #    :param netName: The name of the goldilcks DIO net for preforming this action on.
    #    :param period: Adjust the full period of the waveform produced by this method. Defualt is 0.1s (10Hz).
    #
    #    ## Watchdog Interrupt Toggle
    #    Toggles the WDI signal on the DSP2.0 to prevent the watchdog IC from preforming a reset
    #    while testing parts of the reset circuit.
    #
    #    This is acomplished by calling this method as a procces target under `multiprocessing.Process`
    #    such that this task can be run in parallel with the other portions of the test in `testResetCricuit`.
    #
    #    Multiple requests will be made per seccond by more than one process to the same I2C device (the DIO IC(s))
    #    and this application implimentation relies on the Linux Kernal-Mode driver to queue the requests in the order
    #    they were received in.
    #
    #    To end the toggling, the process is to be killed.
    #    """
    #
    #    while True:
    #        self._sendProcessRequest(processName, "writePin", [netName, False])
    #        time.sleep(period/2)
    #        self._sendProcessRequest(processName, "writePin", [netName, True])
    #        time.sleep(period/2)
    #
    #    return None
    

    def testLEDs(self) -> List[float]:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :returns List[float]: A list of floating point measurements for each of the LED bias voltages.

        ## LED Tests
        ### Test flow:
        All active tests, when test for particular LED is done, disable it.
        Defualt state for all LEDs should be OFF
        1. Test D6
        2. Test D7-1
        3. Test D7-2
        4. Test D4 (no control)
        5. Test D5 (no control)
        """

        _measurements:List[float] = []

        self._sendProcessRequest("DIO_A", "writePin", ["DIO_A_14", True])

        self._sendProcessRequest("ADC_A", "measureSignal", ["GOLD_ADC_A_SE_6", False, self.ADC_OVERRIDE_3V3], self.name)
        _measurements.append(float(self._getProcessData()))

        self._sendProcessRequest("DIO_A", "writePin", ["DIO_A_14", False])
        self._sendProcessRequest("DIO_A", "writePin", ["DIO_A_18", True])

        self._sendProcessRequest("ADC_A", "measureSignal", ["GOLD_ADC_A_SE_12", False, self.ADC_OVERRIDE_5V], self.name)
        _measurements.append(float(self._getProcessData()))

        self._sendProcessRequest("DIO_A", "writePin", ["DIO_A_18", False])
        self._sendProcessRequest("DIO_A", "writePin", ["DIO_A_16", True])

        self._sendProcessRequest("ADC_A", "measureSignal", ["GOLD_ADC_A_SE_10", False, self.ADC_OVERRIDE_5V], self.name)
        _measurements.append(float(self._getProcessData()))

        self._sendProcessRequest("DIO_A", "writePin", ["DIO_A_16", False])

        self._sendProcessRequest("ADC_A", "measureSignal", ["GOLD_ADC_A_SE_14", False, self.ADC_OVERRIDE_5V], self.name)
        _measurements.append(float(self._getProcessData()))

        self._sendProcessRequest("ADC_A", "measureSignal", ["GOLD_ADC_A_SE_13", False, self.ADC_OVERRIDE_3V3], self.name)
        _measurements.append(float(self._getProcessData()))

        return _measurements
    

    def testGPSLoad(self) -> List[float]:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :returns List[float]: A list of floating point measurements for the GPS load LED bias voltages.

        ## GPS Antenna Load Tests
        ### Test flow:
        1. Load is off by defualt during testware init
        2. Measure antenna green led Vbias
        3. Measure antenna red led Vbais
        4. Enable the load
        5. Measure antenna green led Vbias
        6. Measure antenna red led Vbais
        7. Disable the antenna load
        """

        _measurements:List[float] = []

        self._sendProcessRequest("ADC_A", "measureSignal", ["GOLD_ADC_A_SE_7", False, self.ADC_OVERRIDE_5V], self.name)
        _measurements.append(float(self._getProcessData()))

        self._sendProcessRequest("ADC_A", "measureSignal", ["GOLD_ADC_A_SE_9", False, self.ADC_OVERRIDE_5V], self.name)
        _measurements.append(float(self._getProcessData()))

        self._sendProcessRequest("DIO_A", "writePin", ["DIO_A_8", True])

        self._sendProcessRequest("ADC_A", "measureSignal", ["GOLD_ADC_A_SE_7", False, self.ADC_OVERRIDE_5V], self.name)
        _measurements.append(float(self._getProcessData()))

        self._sendProcessRequest("ADC_A", "measureSignal", ["GOLD_ADC_A_SE_9", False, self.ADC_OVERRIDE_5V], self.name)
        _measurements.append(float(self._getProcessData()))

        self._sendProcessRequest("DIO_A", "writePin", ["DIO_A_8", False])

        return _measurements
    

    def _WDItoggle(self) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        ## Toggles the WDI
        Toggles a number of times to ensure the RESET condition is cleared
        and testing can proceed.
        """

        for i in range(0,5,1):
            self._sendProcessRequest("DIO_A", "writePin", ["DIO_A_12", False])
            time.sleep(0.1)
            self._sendProcessRequest("DIO_A", "writePin", ["DIO_A_12", True])

        return None
    

    def testResetCircuit(self) -> List[float]:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :returns List[float]: A list of floating point measurements taken during the reset circuit test.

        ## Reset Circuit Test
        Note: Includes a process spawn to run the WDI toggle in the background.
        It is assumed the Linux Kernal-Mode I2C driver will handle the parallel requests.

        ### Test flow:
        1. Set x High-Z (not possible, use input)
        2. Start the WDI process
        3. Measure reset input net - initial state
        4. Measure the reset LED Vbias - Inactive
        5. Set x low
        6. Measure reset input net - active low
        7. Measure reset LED Vbias - active
        8. Set x High-Z
        9. Kill WDI process
        10. 1-second delay to allow the tripping of the watchdog
        11. Measure reset input net - auto reset state
        """

        _measurements:List[float] = []

        self._sendProcessRequest("DIO_A", "readPin", ["DIO_A_19"], self.name)
        if self._getProcessData(): _measurements.append(3.30)
        else: _measurements.append(0.0)
        #self._WDItoggle()

        self._sendProcessRequest("ADC_A", "measureSignal", ["GOLD_ADC_A_SE_8", False, self.ADC_OVERRIDE_3V3], self.name)
        _measurements.append(float(self._getProcessData()))

        #self._WDItoggle()
        self._sendProcessRequest("DIO_A", "setPinDirection", ["DIO_A_10", True])
        self._sendProcessRequest("DIO_A", "writePin", ["DIO_A_10", False])
        time.sleep(1)

        self._sendProcessRequest("DIO_A", "readPin", ["DIO_A_19"], self.name)
        if self._getProcessData(): _measurements.append(3.30)
        else: _measurements.append(0.0)
        #self._WDItoggle()

        self._sendProcessRequest("ADC_A", "measureSignal", ["GOLD_ADC_A_SE_8", False, self.ADC_OVERRIDE_3V3], self.name)
        _measurements.append(float(self._getProcessData()))
        #self._WDItoggle()

        self._sendProcessRequest("DIO_A", "writePin", ["DIO_A_10", False])
        self._sendProcessRequest("DIO_A", "setPinDirection", ["DIO_A_10", False])
        time.sleep(2)
        self._sendProcessRequest("DIO_A", "readPin", ["DIO_A_19"], self.name)
        if self._getProcessData(): _measurements.append(3.30)
        else: _measurements.append(0.0)


        self._sendProcessRequest("DIO_A", "setPinDirection", ["DIO_A_12", True]) # enable the WDI pin
        self._WDItoggle()
        time.sleep(2)

        self._sendProcessRequest("DIO_A", "readPin", ["DIO_A_19"], self.name)
        if self._getProcessData(): _measurements.append(3.30)
        else: _measurements.append(0.0)

        self._sendProcessRequest("DIO_A", "setPinDirection", ["DIO_A_12", False])

        return _measurements
    

    def addSHT40AsMiscInfo(self) -> tuple:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :returns tuple: A tuple formatted to envoke a carry method in the primary process.

        ## SHT40 as Sub Unit
        This method after calling the `getMfgInformation()` function in the remote process
        responsible for the SHt40, will then pass it on as a carry method to instruct the
        primary process to include this data in the sub unit field of the reports.
        """
    
        # Ask the SHT40 for SN and to send it back here, wait up to 5 seconds for this data
        self._sendProcessRequest("SHT40", "getMfgInformation", returnDeliveryToThread="DSP2")
        serial:str = self._getProcessData()

        unitInformation:miscInfo = miscInfo(
            "SHT40-AD1B-R3 Serial Number",
            text = serial
        )

        return (
            THREAD_CARRY_METHOD,
            payload(
                MAIN_THREAD_NAME,
                THREAD_METHOD,
                ["addMiscInfoToUUT", unitInformation],
                MAIN_THREAD_NAME
            )
        )
    

    def measure1PPS(self) -> int:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :returns int: The number of counts sampled from the bias voltage of the LED for 1PPS.

        Must measure at >= 4Hz
        """

        pulsesCounted: int = 0
        currentState:bool = False
        timeStart:float = time.time()
        endTime:float = timeStart + 30.0

        while (endTime >= time.time()):
            self._sendProcessRequest(self.ADC_SE_PROCESS_NAME, "measureSignal", ["GOLD_ADC_A_SE_11", False, self.ADC_OVERRIDE_3V3], self.name, 0)
            ppsVoltage:float = float(self._getProcessData())

            # On a HIGH (count rising edges)
            # On a LOW, reset the var
            if (False == currentState) and (2.5 < ppsVoltage):
                pulsesCounted += 1
                currentState = True
            elif (True == currentState) and (2.5 > ppsVoltage):
                currentState = False

        timeEnd:float = time.time()
        diff: int = round(timeEnd - timeStart)
        if abs(diff - pulsesCounted) > 5: pulsesCounted = -9999

        return pulsesCounted
    

    def enumerateAndTestSDcard(self) -> bool:
        """
        .. versionadded:: 1.0
        .. versionadded:: 1.0

        :returns bool: Returns true or false if the SD card is present or not present respectivly.

        ## Test Presence of SD Card in System
        This is done by calling a method in the SD Card SPI process
        which returns it's identification string or an error string.

        If the identification string is not equal to the error string, it is treated
        as a pass, that we can indeed talk to the SD Card.
        """

        stdSDerrString:str = "-9999"

        self._sendProcessRequest(self.SDCARD_PROCESS_NAME, "getIdentification", returnDeliveryToThread=self.name)
        sdCardIdentification:str = self._getProcessData()

        return (stdSDerrString != sdCardIdentification)

################################################################

## OTHER CODE ##

################################################################

# EOF