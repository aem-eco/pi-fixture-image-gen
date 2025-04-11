################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: WSJFconverter.py
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

## COMPONENT USE // EXPECTED INPUT/OUTPUT AND LIMITATIONS // LIBRARY DESIGNED FOR ##

################################################################

## IMPORT FILES ##
from typing import List
from dataclasses import dataclass
from importlib import import_module
import uuid

from ...UnitUnderTest.UUT import subUUT, miscInfo
from ...UnitUnderTest.UUT import UUT as aemUUT
from .watsConfig import aemWATSconfiguration

################################################################

## CLASS DEFINITION AND METHODS ##
class CODES:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    # WATS Constant Codes
    To be used within the AEM TEst & Measurement platform implimentation of the WSJF.
    In the event of an update to the WATS platform, these constants should be updated to propegate through the testware.
    """
    
    TYPE_UUT: str = "T"
    """
    The type of report to be created when uploadting the WSJF. T == Test Report.
    """

    STATUS_CODE_PASSED: str = "P"
    """
    The string value WATS uses to denote a PASS in either the report or a test step.
    """

    STATUS_CODE_FAILED: str = "F"
    """
    The string value WATS uses to denote a FAIL in either the report or a test step.
    """

    STATUS_CODE_ERROR: str = "E"
    """
    The string value WATS uses to denote an ERROR in the final report or a test step.
    """

    STATUS_CODE_TERMINATED: str = "T"
    """
    The string value WATS uses to denote the test was TERMINATED.
    """

    # ------------------------------------------------------------------------- #

    GROUP_STARTUP: str = "S"
    """
    Used when creating a sequence. This differentiates the recorded values in setup/startup to main or cleanup.
    """

    GROUP_MAIN: str = "M"
    """
    Used when creatating a seqeunce. This differentiates the recorded values in setup/startup or cleanup. Main is the primary and defualt sequence type.
    """

    GROUP_CLEANUP: str = "C"
    """
    Used when creating a sequence. This differentiates the recorded values in setup/startup or main.
    """

    # ------------------------------------------------------------------------- #

    STEP_TYPE_NUMERIC_LIMIT_SINGLE: str = "ET_NLT"
    """
    Code to denote a string test value type.
    """

    STEP_TYPE_NUMERIC_LIMIT_MULTIPLE: str = "ET_MNLT"
    """
    Code to denote a string test value type.
    """

    STEP_TYPE_STRING_VALUE_SINGLE: str = "ET_SVT"
    """
    Code to denote a string test value type.
    """

    STEP_TYPE_STRING_VALUE_MULTIPLE: str = "ET_MSVT"
    """
    Code to denote a string test value type.
    """

    # ------------------------------------------------------------------------- #

    STEP_TYPE_PASSFAIL_SINGLE: str = "ET_PFT"
    """
    Code to denote a booleantest value type.
    """

    STEP_TYPE_PASSFAIL_MULTIPLE: str = "ET_MPFT"
    """
    Code to denote a booleantest value type.
    """

    # ------------------------------------------------------------------------- #

    COMPARISON_OPERATOR_EQUAL: str = "EQ"
    """
    Code to denote a operator type of EQUALS.
    """

    COMPARISON_OPERATOR_NOT_EQUAL: str = "NE"
    """
    Code to denote a operator type of NOT EQUALS.
    """

    COMPARISON_OPERATOR_GREATER_THAN: str = "GT"
    """
    Code to denote a operator type of GREATER THAN.
    """

    COMPARISON_OPERATOR_LESS_THAN: str = "LT"
    """
    Code to denote a operator type of LESS THAN.
    """

    COMPARISON_OPERATOR_GREATER_EQUAL: str = "GE"
    """
    Code to denote a operator type of GREATER THAN OR EQUALS.
    """

    COMPARISON_OPERATOR_LESS_EQUAL: str = "LE"
    """
    Code to denote a operator type of LESS THAN OR EQUALS.
    """

    COMPARISON_OPERATOR_GREATER_THAN_LESS_THAN: str = "GTLT"
    """
    Code to denote a operator type of GREATER THAN OR LESS THAN.
    """

    COMPARISON_OPERATOR_GREATER_EQUAL_LESS_EQUAL: str = "GELE"
    """
    Code to denote a operator type of GREATER THAN OR EQUAL TO OR LESS THAN OR EQUAL TO.
    """

    COMPARISON_OPERATOR_GREATER_EQUAL_LESS_THAN: str = "GELT"
    """
    Code to denote a operator type of GREATER THAN OR EQUAL TO OR LESS THAN.
    """

    COMPARISON_OPERATOR_GREATER_THAN_LESS_EQUAL: str = "GTLE"
    """
    Code to denote a operator type of GREATER THAN OR LESS THAN OR EQUAL TO.
    """

    COMPARISON_OPERATOR_LESS_THAN_GREATER_THAN: str = "LTGT"
    """
    Code to denote a operator type of LESS THAN OR GREATER THAN.
    """

    COMPARISON_OPERATOR_LESS_EQUAL_GREATER_EQUAL: str = "LEGE"
    """
    Code to denote a operator type of LESS THAN OR EQUAL TO OR GREATER THAN OR EQUAL TO.
    """

    COMPARISON_OPERATOR_LESS_EQUAL_GREATER_THAN: str = "LEGT"
    """
    Code to denote a operator type of LESS THAN OR EUQAL TO OR GREATER THAN.
    """

    COMPARISON_OPERATOR_LESS_THAN_GREATER_EQUAL: str = "LTGE"
    """
    Code to denote a operator type of LESS THAN OR GREATER THAN OR EQUAL TO.
    """

    COMPARISON_OPERATOR_LOG: str = "LOG"
    """
    Code to denote a value which there is no comparitor, just record the value.
    """

    COMPARISON_OPERATOR_CASE_SENSITIVE: str = "CASESENSIT"
    """
    Code to denote a operator type of string case senstitive.
    """

    COMPARISON_OPERATOR_IGNORE_CASE: str = "IGNORECASE"
    """
    Code to denote a operator type of string non-case sensitive.
    """

    # ------------------------------------------------------------------------- #

    JSON_KEY_TYPE: str = "type"
    """
    A key value in WSJF to denote the report type.
    """

    JSON_KEY_RESULT: str = "result"
    """
    A key value in WSJF to denote the final pass/fail status of the UUT.
    """

    JSON_KEY_ROOT: str = "root"
    """
    A key value in WSJF to denote the root sequence callback.
    """

    JSON_KEY_PART_NUMBER: str = "pn"
    """
    A key value in WSJF to denote the UUT part number (also refered to as model in code).
    """

    JSON_KEY_REVISION: str = "rev"
    """
    A key value in WSJF to denote the revision of the UUT.
    """

    JSON_KEY_SERIAL_NUMBER: str = "sn"
    """
    A key value in WSJF to denote the serial number of the UUT.
    """

    JSON_KEY_PROCESS_CODE: str = "processCode"
    """
    A key value in WSJF to denote the WATS process code used for this test type. REQUIRED & MUST MATCH THE VALID CODES ON aem.wats.com.
    """

    JSON_KEY_LOCATION: str = "location"
    """
    A key value in WSJF to describe the location of the fixture (ex. DSP2 Assembly Line).
    """

    JSON_KEY_PURPOSE: str = "purpose"
    """
    A key value in WSJF to describe the purpose the fixture or test process in the line.
    """

    JSON_KEY_MACHINE_NAME: str = "machineName"
    """
    A key value in WSJF to describe the physical fixture machine name.
    """

    JSON_KEY_START_TIME_LOCAL: str = "start"
    """
    A key value in WSJF to indicate the local start time of the test.
    """

    JSON_KEY_START_TIME_UTC: str = "startUTC"
    """
    A key value in WSJF to indicate the UTC start time of the test.
    """

    JSON_KEY_PROCESS_NAME: str = "processName"
    """
    A key value in WSJF to denote the WATS process name used for this test type. REQUIRED & MUST MATCH THE VALID PROCESS NAMES ON aem.wats.com.
    """

    JSON_KEY_MISC_INFO: str = "miscInfos"
    """
    A key value in WSJF to store misc information fields for this UUT.
    """

    JSON_KEY_SUB_UNITS: str = "subUnits"
    """
    A key value in WSJF to store sub unit information fields for this UUT. If the sub unit contains reports on aem.wats.com, they will be linked in a higherarchy.
    """

    JSON_KEY_UUT: str = "uut"
    """
    A key value in WSJF to information fields for this UUT.
    """

    JSON_KEY_USER: str = "user"
    """
    A key value in WSJF to store the initials of the user/operator.
    """

    JSON_KEY_EXEC_TIME: str = "execTime"
    """
    A key value in WSJF to store the number of seconds it took to complete the root sequence.
    """

    JSON_KEY_BATCH_SERIAL_NUMBER: str = "batchSN"
    """
    A key value in WSJF to store the batch of the UUT.
    """

    JSON_KEY_TEST_SOCKET_INDEX: str = "testSocketIndex"
    """
    A key value in WSJF to store which slot this UUT was installed into if multiple exist on the fixture.
    """

    JSON_KEY_FIXTURE_ID: str = "fixtureID"
    """
    A key value in WSJF to store the fixture ID.
    """

    JSON_KEY_ERROR_CODE: str = "errorCode"
    """
    A key value in WSJF to store a fixture-spesific error code.
    """

    JSON_KEY_ERROR_MESSAGE: str = "errorMessage"
    """
    A key value in WSJF to store a fixture-spesific error message.
    """

    JSON_KEY_BATCH_FAIL_COUNT: str = "batchFailCount"

    JSON_KEY_BATCH_LOOP_INDEX: str = "batchLoopIndex"

    JSON_KEY_STEP_CAUSED_UUT_FAIL: str = "stepIdCausedUUTFailure"
    """
    A key value in WSJF to denote which step ID caused the report as a whole to indicated FAILED.
    """

    JSON_KEY_COMMENT: str = "comment"
    """
    A key value in WSJF to store a comment or custom string in a report.
    """

    JSON_KEY_DESCRIPTION: str = "description"

    JSON_KEY_TYPEDEF: str = "typedef"

    JSON_KEY_NUMERIC: str = "numeric"

    JSON_KEY_TEXT: str = "text"

    JSON_KEY_PART_TYPE: str = "partType"
    """
    A key value in WSJF to indicate the sub unit part type (ex. assembly).
    """

    JSON_KEY_NAME: str = "name"
    """
    A key value in WSJF to store the name of a test step.
    """

    JSON_KEY_STATUS: str = "status"
    """
    A key value in WSJF to store the result of a test step (pass/fail).
    """

    JSON_KEY_STEP_TYPE: str = "stepType"
    """
    A key value in WSJF to store the type of test for the current step.
    """

    JSON_KEY_GROUP: str = "group"

    JSON_KEY_TOT_TIME: str = "totTime"

    JSON_KEY_CAUSED_SEQUENCE_FAILURE: str = "causedSeqFailure"
    """
    A key value in WSJF to indicate if this step caused the whole sequence failure, vs whole test failure or none.
    """

    JSON_KEY_REPORT_TEXT: str = "reportText"
    JSON_KEY_INTERACTIVE_EXE_NUM: str = "interactiveExeNum"
    JSON_KEY_STEPS: str = "steps"
    """
    A key value in WSJF to store the list of test steps for the current sequence.
    """

    JSON_KEY_NUMERIC_MEASUREMENT: str = "numericMeas"
    """
    A key value in WSJF to denote the type of test for the current step is numeric.
    """

    JSON_KEY_STRING_MEASUREMENT: str = "stringMeas"
    """
    A key value in WSJF to denote the type of test for the current step is string based.
    """

    JSON_KEY_BOOLEAN_MEASUREMENT: str = "booleanMeas"
    """
    A key value in WSJF to denote the type of test for the current step is a boolean.
    """

    JSON_KEY_ADDITIONAL_RESULTS: str = "additionalResults"
    JSON_KEY_SEQUENCE_CALL: str = "seqCall"
    JSON_KEY_CALL_EXECUTEABLE: str = "exeCall"
    JSON_KEY_MESSAGE_POPUP: str = "messagePopup"
    JSON_KEY_CHART: str = "chart"
    JSON_KEY_ATTACHMENT: str = "attachment"
    JSON_KEY_LOOP: str = "loop"
    JSON_KEY_ID: str = "id"
    """
    A key value in WSJF to store the UID of the report as will be generated by the UID python class.
    """

    # ------------------------------------------------------------------------- #

@dataclass
class Chart:
    """
    # NOT IMPLIMENTED
    """
    pass


@dataclass
class Action_Step:
    """
    # NOT IMPLIMENTED
    """
    pass


@dataclass
class Base_Measurement:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    Constant fields present in multiple other WATS implimentation data structures.
    Not designed to be used on its own.
    """

    value: int|float|str
    """
    The recorded measurement.
    """

    compOp: str
    """
    The type of comparison operation to be had on the value.
    """

    status: str
    """
    The pass/fail status of the current step.
    """


@dataclass
class Numeric_Measurement(Base_Measurement):
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    :inherits: Base_Measurement

    Used within a Test_Step to represent all the data needed for a numeric measurement of any comparison type.
    Not designed to be used on its own - this is a subcomponent of a Test_Step dataclass.
    """

    unit: str|None
    """
    String version of the  units used for the measured value.
    """

    name: str|None
    """
    The name of the measurement, required if used in a `multi-measurement`, otherwise should be `None`.
    """
    
    matchValue: int|float|None = None
    """
    Direct comparison value, equals or not equals to comparisons.
    """

    lowLimit: int|float|None = None
    """
    Lower bound on a ranged operator.
    """

    highLimit: int|float|None = None
    """
    Upper bound on a ranged operator.
    """


@dataclass
class String_Measurement(Base_Measurement):
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    :inherits: Base_Measurement

    Used within a Test_Step to represent all the data needed for a string measurement of any comparison type.
    Not designed to be used on its own - this is a subcomponent of a Test_Step dataclass.
    """

    name: str|None
    """
    Name of the string measurement.
    """

    limit: str
    """
    String limit - the expected string to receive in the value field, or REGEX operation value (custom addon to WATS).
    """


@dataclass
class Boolean_Measurement:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    Used within a Test_Step to represent all the data needed for a boolean measurement.
    Not designed to be used on its own - this is a subcomponent of a Test_Step dataclass.
    """

    status: bool
    """
    The value in this case is the status (boolean pass/fail).
    """

    name: str|None
    """
    Name of the boolean measurement.
    """


@dataclass
class Test_Step:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    Used within a sequence (typically) or on its own.
    Utilizes multiple sub dataclasses to organize and structure all data required for a WATS test step.
    """

    id: int
    """
    Unique ID of the test step (taken from the test step.json file as the index).
    """

    name: str
    """
    Name of the test, different from the name of the measurement.
    """


    status: str
    """
    Pass/fail status of the step as a whole.
    """

    stepType: str
    """
    Step type name as defined in test step JSON file.
    """

    start: str
    """
    Start time of the step stored as a string.
    """

    totTime: float
    """
    Total execution time of the step for reporting in WATS.
    """

    group: str
    """
    The group identifier of what sequence category this step is contained within.
    """


    errorCode: int
    """
    Error code if applicable to a step that resulted in an error.
    """

    errorMessage: str
    """
    Error message if applicable to a step that resulted in an error.
    """


    causedSeqFailure: bool
    """
    Denotes if this step is reported as a failure, the whole sequence should be failed.
    """

    causedUUTFailure: bool
    """
    Denotes if this step is reported as a failure, the whole UUT report should be failed.
    """


    reportText: str|None
    interactiveExeNum: int|None


    numericMeas: Numeric_Measurement|List[Numeric_Measurement]|None = None
    """
    Either a single or  list of multiple numerical measurements contained within this step. Set to None if another type is used.
    """

    stringMeas: String_Measurement|List[String_Measurement]|None = None
    """
    Either a single or  list of multiple string measurements contained within this step. Set to None if another type is used.
    """

    booleanMeas: Boolean_Measurement|None = None
    """
    Either a single numerical measurement contained within this step. Set to None if another type is used. Does not support multiple measurements.
    """


@dataclass
class Sequence_Call:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    Sub component of a Sub_Sequence or Root_Sequence.
    The aformentioned must include a Sequence_Call to be considiered valid by WATS.
    """

    name: str
    """
    Name of the sequence ex. Main Sequence
    """

    version: str
    """
    The version number of the sequence, should be tied to the version of the test step file.
    """

    path: str
    """
    Path to the sequence file. Should point to the test step file.
    """


@dataclass
class Sub_Sequence:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    Used inside the Root_Sequence as a "step" to create structured steps and sub-steps inside the final WATS report.
    The Sub_Sequence will contain a list of Test_Steps to contain individual tests/measurements.
    """

    id: int
    """
    A unique ID for the sub-sequence since it is contained in the same list as test steps.
    """

    name: str
    """
    Name reference to the sub-sequence.
    """


    status: str
    """
    Pass/fail status of this sub-sequence.
    """

    stepType: str
    """
    The type of sequence, called stepType since this can be listed alongside test steps and must report in a similar way.
    """


    start: str
    """
    Start datetime as a string when the sequence was started/called.
    """
    totTime: float
    """
    Total execution time of all steps contained within this sub-sequence.
    """

    group: str
    """
    The WATS group type the sub-sequence falls into ex 'M' for main.
    """


    errorCode: int
    """
    Reported fixture-spesific error code if an error is encountered during this sequence.
    """

    errorMessage: str
    """
    Reported fixture-spesific error message if an error is encountered during this sequence.
    """


    causedSeqFailure: bool
    """
    If the failure of this sub-sequence should cause the parent sequence to fail.
    """

    causedUUTFailure: bool
    """
    If the failure of this sub-sequence should fail the UUT report.
    """


    reportText: str


    steps: List[Test_Step]
    """
    List of steps contained within this sub-sequence call.
    """

    seqCall: Sequence_Call
    """
    The WATS sequence call type field.
    """


@dataclass
class Root_Seqeunce:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    The Root_Sequence is the top-level item in the WSJF that will contain all Sub_Sequence items
    and Test_Steps. "blocks" are a list of either Sub_Sequences (typically) or Test_Steps (un-structured list of only Test_Steps)
    """

    id: int
    """
    A uniquie ID to assign to the root_sequence.
    """


    name: str
    """
    Name of the root_sequence callback.
    """

    status: str
    """
    Pass/fail status of the root_seqeunce. Matches the p/f status for the UUT.
    """

    stepType: str
    """
    The step type for the root_sequence.
    """


    totTime: float
    """
    Total execution time of the root_sequence, should match the total time for the whole report.
    """


    group: str
    reportText: str|None


    blocks: List[Test_Step|Sub_Sequence]
    """
    The list of both steps and sub_sequences contained in the root_sequence.
    """

    callback: Sequence_Call
    """
    WATS callback type field.
    """


@dataclass
class UUT:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    The UUT dataclass is placed into the root of the WSJF and contains header information for the final report.
    Fields may duplicate the aemUUT object and that is by design, although go by a different name in some cases.
    """

    user: str
    """
    User or operator initals.
    """

    execTime: float
    """
    Total time to pass the UUT through the fixture process.
    """

    batchSN: str
    """
    The units batch serial number.
    """

    testSocketIndex: int
    """
    Slot index the UUT was installed into if the fixture contains more than one.
    """

    fixtureId: str
    """
    The ID of the fixture used to test the unit.
    """

    errorCode: int
    """
    Top-level error code from the fixture if applicable.
    """

    errorMessage: str
    """
    Top-level error message from the fixture if applicable.
    """

    stepIdCausedUUTFailure: int
    """
    Identifies the step ID that caused the UUT to fail if applicable. Will be shown as a link in the report and will take a user to the position in the report where the failure occured.
    """

    comment: str
    """
    Top-level comment in the report header. Can be used to indicate special circumstances or similar. Filterable.
    """


@dataclass
class WSJF:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    The top-level WATS object containing all other dataclasses/structures in this module.
    This object will be directly used to convert info the JSON format for final upload to WATS.
    """

    type: str
    """
    The WATS test type, typically 'T' for test report.
    """

    result: str
    """
    The final report pass/fail status.
    """


    pn: str
    """
    The part number or model name of the UUT contained in the report.
    """

    sn: str
    """
    The serial number of the UUT contained in the report.
    """

    rev: str
    """
    The revision of the UUT contained in the report.
    """


    processCode: int
    """
    The valid WATS process code this report is alligned with. REQUIRED & MUST MATCH aem.wats.com.
    """

    processName: str|None
    """
    The valid WATS process name this report is alligned with. REQUIRED & MUST MATCH aem.wats.com.
    """


    location: str
    """
    Location of the fixture.
    """

    purpose: str
    """
    Definition of why this fixture exists and what it acomplishes.
    """

    machineName: str
    """
    The name of the physical fixture machine.
    """

    start: str
    """
    The start datetime as a string.
    """


    miscInfos: List[miscInfo]|None
    """
    A list of misc info line items, or None if there are no fields to add to the header of the report.
    """

    subunits: List[subUUT]|None
    """
    A list of the sub units contained inside of the current UUT, added to the report header and links devices with reports inside of WATS into a higherarchy.
    """

    uut: UUT
    """
    The UUT object containing some of the header information.
    """


    root: Root_Seqeunce
    """
    The root sequence containing all non UUT information from a fixture.
    """


class ObjectToJson:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    # ObjectToJson
    Constructed only with a string argument to the process module for the spesisfic fixture,
    this class will handle all of the object creations/conversions into a dict-like or JSON format.
    - designed to be a dynamically loaded/imported module into the WATS class using importlib.import_module()
    - not meant to be used on its own - this class is a sub-component of another class
    """

    def __init__(self, processFileToUse:str):
        # Dynamically get the WATS process python file here and use its generate functions

        try:
            self.process = import_module(
                name = processFileToUse
            )
            self.process = getattr(self.process, processFileToUse.split('.')[-1])
            self.process = self.process()
        except Exception as e:
            pass #TODO


    def createObjectified(self, aemUUT:aemUUT, WATSfixtureConfig:aemWATSconfiguration) -> WSJF:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param aemUUT: The aemUUT object containing all of the test data for this report.
        :param WATSfixtureConfig: The configuration for the fixture regarding WATS reports.

        :returns WSJF: The object-version of the WATS standard JSON format file. To be converted from this form into the JSON data via `.__dict__` calls on its objects.

        Using the aemUUT object and configuration for WATS, this method will create the fully
        object-oriented version of the WSJF for later use in another method to translate from an object to a dict-like or JSON file/var
        """

        self.process.createElements(aemUUT)                                     # Calls from the implimented dynamic-loading process python file
        _root: Root_Seqeunce = self.process.generateRootSequenceCall(aemUUT)    # for the particular fixture in use

        # Generating miscUUT and subUUT lists are not needed (prev. implimentation)
        # as the new objects used in the base aemUUT dataclass is now in a format for a straight <>.__dict__
        # python call to create the JSON list elements for the sub-units and miscInfos in WATS

        if aemUUT.overallResult:
            _result: str = CODES.STATUS_CODE_PASSED     # Translate a bool to the WATS code
        else:                                           # WATS will not understand a boolean passed, requires use of codes
            _result: str = CODES.STATUS_CODE_FAILED     #

        watsUUT: UUT = UUT(                             # Create Report header data structure (WATS UUT)
            user=aemUUT.user,                           #
            execTime=aemUUT.durationOfRun,              #
            batchSN=aemUUT.batchSerialNumber,           #
            testSocketIndex=aemUUT.testSlot,            #
            fixtureId=WATSfixtureConfig.machineName,    #
            errorCode=None,                             # TODO
            errorMessage=None,                          # TODO
            stepIdCausedUUTFailure=None,                # TODO
            comment=None                                # TODO
        )
        
        return WSJF(                                                    # Create the top-level WSJF Object and return it to the caller
            type = WATSfixtureConfig.type,                              #
            result = _result,                                           #
            pn = aemUUT.model,                                          #
            sn = aemUUT.serialNumber,                                   #
            rev = aemUUT.rev,                                           #
            processCode = WATSfixtureConfig.processCode,                # Must be a valid and ACTIVE process code inside the WATS cloud instance to be accepted
            processName = WATSfixtureConfig.processName,                # Must be a valid and ACTIVE process name inside the WATS cloud instance to be accepted
            location = WATSfixtureConfig.location,                      #
            purpose = WATSfixtureConfig.purpose,                        #
            machineName = WATSfixtureConfig.machineName,                #
            start = aemUUT.startDatetime.strftime('%Y/%m/%dT%H:%M:%S'), #
            miscInfos = aemUUT.miscInfo,                                #
            subunits = aemUUT.subUUTs,                                  #
            uut = watsUUT,                                              #
            root = _root                                                #
        )
    

    def _decodeSingleAndMultiTestStep(self, block:Test_Step) -> dict:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param block: Takes in a test step (single or milti) referenced as a 'block' and converts its data into a dictionary.

        :returns dict: The dictionary version of the test step data.

        :raises TypeError: When if there is no valid measurement found. Valid measurements are: Numeric, String, and Boolean.

        Taking a single Test_Step object this method will then preform the translation into
        a JSON or dict-like element to be used inside the final WSJF file.
        """
        
        _tempTop: dict = {}
        _tempTop[CODES.JSON_KEY_NAME]                    =  block.name
        _tempTop[CODES.JSON_KEY_ID]                      =  block.id
        _tempTop[CODES.JSON_KEY_STATUS]                  =  block.status
        _tempTop[CODES.JSON_KEY_STEP_TYPE]               =  block.stepType
        _tempTop[CODES.JSON_KEY_START_TIME_LOCAL]        =  block.start
        _tempTop[CODES.JSON_KEY_TOT_TIME]                =  block.totTime
        _tempTop[CODES.JSON_KEY_GROUP]                   =  block.group
        _tempTop[CODES.JSON_KEY_ERROR_CODE]              =  block.errorCode
        _tempTop[CODES.JSON_KEY_ERROR_MESSAGE]           =  block.errorMessage
        _tempTop[CODES.JSON_KEY_CAUSED_SEQUENCE_FAILURE] =  block.causedSeqFailure
        _tempTop[CODES.JSON_KEY_STEP_CAUSED_UUT_FAIL]    =  block.causedUUTFailure
        _tempTop[CODES.JSON_KEY_REPORT_TEXT]             =  block.reportText
        _tempTop[CODES.JSON_KEY_INTERACTIVE_EXE_NUM]     =  block.interactiveExeNum

        if isinstance(block.numericMeas, list):
            _tempTop[CODES.JSON_KEY_NUMERIC_MEASUREMENT] = []
            for measurement in block.numericMeas:
                _tempTop[CODES.JSON_KEY_NUMERIC_MEASUREMENT].append(measurement.__dict__)
        elif isinstance(block.numericMeas, Numeric_Measurement):
            _tempTop[CODES.JSON_KEY_NUMERIC_MEASUREMENT] = [block.numericMeas.__dict__]

        if isinstance(block.stringMeas, list):
            _tempTop[CODES.JSON_KEY_STRING_MEASUREMENT] = []
            for measurement in block.stringMeas:
                _tempTop[CODES.JSON_KEY_STRING_MEASUREMENT].append(measurement.__dict__)
        elif isinstance(block.stringMeas, String_Measurement):
            _tempTop[CODES.JSON_KEY_STRING_MEASUREMENT] = [block.stringMeas.__dict__]

        if isinstance(block.booleanMeas, Boolean_Measurement):
            _tempTop[CODES.JSON_KEY_BOOLEAN_MEASUREMENT] = [block.booleanMeas.__dict__]

        return _tempTop
    

    def convertObjectifiedToWSJF(self, objectifiedWSJF:WSJF) -> dict:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param objectifiedWSJF: The python object version of the WATS standard JSON format file.

        :returns dict: The final WATS standard JSON file to be PUT into WATS.

        :raises TypeError: When the roots steps are invalid in their type, accepted types are: `Test_Step`, and `Sub_Sequence`.

        Taking in a Object-oriented version of the WSJF, this method will translate and return the full dict-like or JSON report to be uploaded to WATS.
        This method will also be responsible for generating the UUID for each report going into the WATS platform. The selected mode for the UUID is MACADDRESS + Time generation.
        See Python's documentation of the UUID class for more infomation.

        Additionaly, this method will also be the place where the sub-units and misc infos are finally put into the dict-like or JSON format.
        Until this point they have existed as a aemSubUUT or aemMiscInfoBlock.
        """

        wsj: dict = {}

        if None == objectifiedWSJF.processName: wsj[CODES.JSON_KEY_PROCESS_NAME] = None
        else:                                   wsj[CODES.JSON_KEY_PROCESS_NAME] = objectifiedWSJF.processName

        if None == objectifiedWSJF.subunits:    wsj[CODES.JSON_KEY_SUB_UNITS] = None
        else:                                   wsj[CODES.JSON_KEY_SUB_UNITS] = [subUnit.__dict__ for subUnit in objectifiedWSJF.subunits]

        if None == objectifiedWSJF.miscInfos:   wsj[CODES.JSON_KEY_MISC_INFO] = None
        else:                                   wsj[CODES.JSON_KEY_MISC_INFO] = [infoItem.__dict__ for infoItem in objectifiedWSJF.miscInfos]

        wsj[CODES.JSON_KEY_ID]                  = str(uuid.uuid1())             # Top-level report elements
        wsj[CODES.JSON_KEY_TYPE]                = objectifiedWSJF.type          #
        wsj[CODES.JSON_KEY_RESULT]              = objectifiedWSJF.result        #
        wsj[CODES.JSON_KEY_PART_NUMBER]         = objectifiedWSJF.pn            #
        wsj[CODES.JSON_KEY_SERIAL_NUMBER]       = objectifiedWSJF.sn            #
        wsj[CODES.JSON_KEY_REVISION]            = objectifiedWSJF.rev           #
        wsj[CODES.JSON_KEY_PROCESS_CODE]        = objectifiedWSJF.processCode   #
        wsj[CODES.JSON_KEY_LOCATION]            = objectifiedWSJF.location      #
        wsj[CODES.JSON_KEY_PURPOSE]             = objectifiedWSJF.purpose       #
        wsj[CODES.JSON_KEY_MACHINE_NAME]        = objectifiedWSJF.machineName   #
        wsj[CODES.JSON_KEY_START_TIME_LOCAL]    = objectifiedWSJF.start         #
        wsj[CODES.JSON_KEY_UUT]                 = objectifiedWSJF.uut.__dict__  #

        # Final top-level report element is the root. This needs to be parsed out and then put into the wsj variable for final return.
        _rootAsDict: dict = {}

        _rootAsDict[CODES.JSON_KEY_GROUP]           = CODES.GROUP_MAIN
        _rootAsDict[CODES.JSON_KEY_STEP_TYPE]       = "SequenceCall"            # These are typical names for the varibles in the WATS documentation.
        _rootAsDict[CODES.JSON_KEY_NAME]            = "MainSequence Callback"   # The upload may not work corerctly without these.
        _rootAsDict[CODES.JSON_KEY_STATUS]          = objectifiedWSJF.result
        _rootAsDict[CODES.JSON_KEY_ID]              = objectifiedWSJF.root.id
        _rootAsDict[CODES.JSON_KEY_TOT_TIME]        = objectifiedWSJF.root.totTime
        _rootAsDict[CODES.JSON_KEY_REPORT_TEXT]     = objectifiedWSJF.root.reportText
        _rootAsDict[CODES.JSON_KEY_SEQUENCE_CALL]   = objectifiedWSJF.root.callback.__dict__

        _rootStepsDictList: List[dict] = []
        for block in objectifiedWSJF.root.blocks:
            # The for-loop will run for all the steps inside the root object
            # This will be either the Sub_Seqeunce calls or the Test_Steps

            _isTestStepOnly = isinstance(block, Test_Step)

            if _isTestStepOnly: _rootStepsDictList.append(self._decodeSingleAndMultiTestStep(block=block))
            elif not _isTestStepOnly:
                _temp: dict = {}

                _temp[CODES.JSON_KEY_ID]                        = block.id
                _temp[CODES.JSON_KEY_NAME]                      = block.name
                _temp[CODES.JSON_KEY_STATUS]                    = block.status
                _temp[CODES.JSON_KEY_STEP_TYPE]                 = block.stepType
                _temp[CODES.JSON_KEY_START_TIME_LOCAL]          = block.start
                _temp[CODES.JSON_KEY_TOT_TIME]                  = block.totTime
                _temp[CODES.JSON_KEY_GROUP]                     = block.group
                _temp[CODES.JSON_KEY_ERROR_CODE]                = block.errorCode
                _temp[CODES.JSON_KEY_ERROR_MESSAGE]             = block.errorMessage
                _temp[CODES.JSON_KEY_CAUSED_SEQUENCE_FAILURE]   = block.causedSeqFailure
                _temp[CODES.JSON_KEY_STEP_CAUSED_UUT_FAIL]      = block.causedUUTFailure
                _temp[CODES.JSON_KEY_REPORT_TEXT]               = block.reportText
                _temp[CODES.JSON_KEY_SEQUENCE_CALL]             = block.seqCall.__dict__

                _tempListOfSteps: List[dict] = []
                for step in block.steps:
                    # If one of our root steps is a Sub_Sequence we need to
                    # decode all of it's steps. These could be more nested Sub_Sequences (not supported in this version)
                    # or Test_Steps. All of these need to become dict-like and saved into the "top-level" root dict-like.

                    _tempListOfSteps.append(self._decodeSingleAndMultiTestStep(block=step))
                _temp[CODES.JSON_KEY_STEPS] = _tempListOfSteps

                _rootStepsDictList.append(_temp)

            # If the object attempmting to be decoded is not a Sub_Sequence or a Test_Step
            # we raise a TypeError.
            else: raise TypeError 

            _rootAsDict[CODES.JSON_KEY_STEPS] = _rootStepsDictList

        wsj[CODES.JSON_KEY_ROOT] = _rootAsDict

        return wsj

################################################################

## OTHER CODE ##

################################################################

# EOF