################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: Test_Process.py
# | Date: 2025-04-04
# | Rev: 1.1
# | Change By: Everly Larche
# | ECO Ref:
#  ----------------
# | Project Name: AEM Test & Measurement Platform
# | Developer: Everly Larche
# | File Description: The standard wats converter core.
#  ----------------
################################################################
################################################################

## IMPORT FILES ##
from ..Core.WSJFconverter import *
from ...UnitUnderTest.UUT import SingleTestReport, MultiTestReport, multiMeasurementData
from ...TestSteps.testStepDecoder import TestStepDecoder

from typing import List, Tuple

################################################################

## CLASS DEFINITION AND METHODS ##
class Test_Process:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    # WATS Core Process
    The basic and required implimentation of the WATS process. To be adapted on or switched out for another file if
    a fixture were to require it. The file is dynamically loaded and therefore it could be concived in the future if multiple
    processes were needed, it can be acomplished.
    """

    def __init__(self):
        self.subSequ: List[Sub_Sequence] = []
        self.testSteps: List [Test_Step] = []

        return None
    

    def createElements(self, uutInfo:aemUUT) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param uutInfo: An AEM UUT object containing the required test step information.

        ## Create Elements
        Function that itterates through a uut object and generates a list of all the steps executed in the
        sequence. Identifies single or multi-measurement steps and actions them accordingly.
        """

        # create the structure here, ex. create sub-sequences with test steps of a given range etc.
        for stepResult in uutInfo.testStepResults:
            try:

                if isinstance(stepResult, MultiTestReport):
                    self.testSteps.append(self.generateMultiStep(stepResult))
                elif isinstance(stepResult, SingleTestReport):
                    self.testSteps.append(self.generateSingleStep(stepResult))

            except Exception as e:
                continue # TODO - impliment correct error handling for a custom implimentation

        return None
    

    def generateWATSmeasurmentBlock(self, step:MultiTestReport|SingleTestReport) -> Tuple[str, String_Measurement|Numeric_Measurement|Boolean_Measurement]:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.1

        :param step: Either a single or multi-measurement data type containing the test information to be parsed.

        :returns tuple: Tuple containing the data <stepName, stepData> using the WATS custom datatypes.

        :raises IndexError: If the defualt case in the match array is reached. This can happen if the step type is invalid.

        ## Generate WATS Measurement Blocks
        Used to create the body of a WATS `Test_Step` object based on the type of comparitor used in the AEM testStep/expect objects and number of measurements taken.

        ..NOTE:: This method is able to handle either a single-measurement or multi-measurement test step.
        """

        _measurementBlockToReturn:String_Measurement|Numeric_Measurement|Boolean_Measurement|List[String_Measurement|Numeric_Measurement|Boolean_Measurement] = None

        _units = step.units
        _comparisonObject = step.comparison
        _dataValue = step.recordedValue

        # multi measurement steps have names for each measurement, if we cant decode it
        # its likely that we are working with a single measurement block and should ignore this.
        try:
            _name = step.comparison.name
        except:
            _name = None

        _measurementResult: bool = self.determineWATSstatusCode(step.result)
        
        # TODO - remove multiple-xyz copies, not needed with current looped implimentation in caller method
        # TODO - support equal list compop

        match _comparisonObject.type:
            case TestStepDecoder.COMP_TYPE_GT:                                                  #### #### GREATER THAN TYPE (Numeric only)
                
                if not isinstance(_dataValue, list):                                            #### Single-Numeric
                    s_type = CODES.STEP_TYPE_NUMERIC_LIMIT_SINGLE                               #
                    _measurementBlockToReturn = Numeric_Measurement(                            #
                        value       = _dataValue,                                               #
                        compOp      = CODES.COMPARISON_OPERATOR_GREATER_THAN,                   #
                        status      = _measurementResult,                                       #
                        unit        = _units,                                                   #
                        name        = _name,                                                     #
                        lowLimit    = _comparisonObject.compareVal_L                            #
                    )                                                                           ####

                elif isinstance(_dataValue, list):                                              #### Multiple-Numeric
                    s_type = CODES.STEP_TYPE_NUMERIC_LIMIT_MULTIPLE                             #
                    for individualDataValue in _dataValue:                                      #
                        _subDataValue: multiMeasurementData = individualDataValue               #
                                                                                                #
                        _measurementBlockToReturn.append(Numeric_Measurement(                   #
                            value       = _subDataValue.recordedValue,                          #
                            compOp      = CODES.COMPARISON_OPERATOR_GREATER_THAN,               #
                            status      = self.determineWATSstatusCode(_subDataValue.result),   #
                            unit        = _subDataValue.units,                                  #
                            name        = _subDataValue.name,                                   #
                            lowLimit    = _subDataValue.comparison.compareVal_L                 #
                        ))                                                                      ####

            case TestStepDecoder.COMP_TYPE_LT:                                                  #### #### LESS THAN TYPE (Numeric only)
                
                if not isinstance(_dataValue, list):                                            #### Single-Numeric
                    s_type = CODES.STEP_TYPE_NUMERIC_LIMIT_SINGLE                               #
                    _measurementBlockToReturn = Numeric_Measurement(                            #
                        value       = _dataValue,                                               #
                        compOp      = CODES.COMPARISON_OPERATOR_LESS_THAN,                      #
                        status      = _measurementResult,                                       #
                        unit        = _units,                                                   #
                        name        = _name,                                                    #
                        lowLimit    = _comparisonObject.compareVal_H                            #
                    )                                                                           ####

                elif isinstance(_dataValue, list):                                              #### Multiple-Numeric
                    s_type = CODES.STEP_TYPE_NUMERIC_LIMIT_MULTIPLE                             #
                    for individualDataValue in _dataValue:                                      #
                        _subDataValue: multiMeasurementData = individualDataValue               #
                                                                                                #
                        _measurementBlockToReturn.append(Numeric_Measurement(                   #
                            value       = _subDataValue.recordedValue,                          #
                            compOp      = CODES.COMPARISON_OPERATOR_LESS_THAN,                  #
                            status      = self.determineWATSstatusCode(_subDataValue.result),   #
                            unit        = _subDataValue.units,                                  #
                            name        = _subDataValue.name,                                   #
                            highLimit    = _subDataValue.comparison.compareVal_L                #
                        ))                                                                      ####

            case TestStepDecoder.COMP_TYPE_GTLT:                                                #### #### GREATER THAN OR LESS THAN TYPE (Numeric only)
                
                if not isinstance(_dataValue, list):                                            #### Single-Numeric
                    s_type = CODES.STEP_TYPE_NUMERIC_LIMIT_SINGLE                               #
                    _measurementBlockToReturn = Numeric_Measurement(                            #
                        value       = _dataValue,                                               #
                        compOp      = CODES.COMPARISON_OPERATOR_GREATER_THAN_LESS_THAN,         #
                        status      = _measurementResult,                                       #
                        unit        = _units,                                                   #
                        name        = _name,                                                     #
                        lowLimit    = _comparisonObject.compareVal_L,                           #
                        highLimit   = _comparisonObject.compareVal_H                            #
                    )                                                                           ####

                elif isinstance(_dataValue, list):                                              #### Multiple-Numeric
                    s_type = CODES.STEP_TYPE_NUMERIC_LIMIT_MULTIPLE                             #
                    for individualDataValue in _dataValue:                                      #
                        _subDataValue: multiMeasurementData = individualDataValue               #
                                                                                                #
                        _measurementBlockToReturn.append(Numeric_Measurement(                   #
                            value       = _subDataValue.recordedValue,                          #
                            compOp      = CODES.COMPARISON_OPERATOR_GREATER_THAN_LESS_THAN,     #
                            status      = self.determineWATSstatusCode(_subDataValue.result),   #
                            unit        = _subDataValue.units,                                  #
                            name        = _subDataValue.name,                                   #
                            lowLimit    = _subDataValue.comparison.compareVal_L,                #
                            highLimit   = _subDataValue.comparison.compareVal_H                 #
                        ))                                                                      ####

            case TestStepDecoder.COMP_TYPE_GE:                                                  #### #### GREATER THAN TYPE (Numeric only)
                
                if not isinstance(_dataValue, list):                                            #### Single-Numeric
                    s_type = CODES.STEP_TYPE_NUMERIC_LIMIT_SINGLE                               #
                    _measurementBlockToReturn = Numeric_Measurement(                            #
                        value       = _dataValue,                                               #
                        compOp      = CODES.COMPARISON_OPERATOR_GREATER_EQUAL,                  #
                        status      = _measurementResult,                                       #
                        unit        = _units,                                                   #
                        name        = _name,                                                     #
                        lowLimit    = _comparisonObject.compareVal_L                            #
                    )                                                                           ####

                elif isinstance(_dataValue, list):                                              #### Multiple-Numeric
                    s_type = CODES.STEP_TYPE_NUMERIC_LIMIT_MULTIPLE                             #
                    for individualDataValue in _dataValue:                                      #
                        _subDataValue: multiMeasurementData = individualDataValue               #
                                                                                                #
                        _measurementBlockToReturn.append(Numeric_Measurement(                   #
                            value       = _subDataValue.recordedValue,                          #
                            compOp      = CODES.COMPARISON_OPERATOR_GREATER_EQUAL,              #
                            status      = self.determineWATSstatusCode(_subDataValue.result),   #
                            unit        = _subDataValue.units,                                  #
                            name        = _subDataValue.name,                                   #
                            lowLimit    = _subDataValue.comparison.compareVal_L                 #
                        ))                                                                      ####

            case TestStepDecoder.COMP_TYPE_LE:                                                  #### #### LESS THAN TYPE (Numeric only)
                
                if not isinstance(_dataValue, list):                                            #### Single-Numeric
                    s_type = CODES.STEP_TYPE_NUMERIC_LIMIT_SINGLE                               #
                    _measurementBlockToReturn = Numeric_Measurement(                            #
                        value       = _dataValue,                                               #
                        compOp      = CODES.COMPARISON_OPERATOR_LESS_EQUAL,                     #
                        status      = _measurementResult,                                       #
                        unit        = _units,                                                   #
                        name        = _name,                                                    #
                        lowLimit    = _comparisonObject.compareVal_H                           #
                    )                                                                           ####

                elif isinstance(_dataValue, list):                                              #### Multiple-Numeric
                    s_type = CODES.STEP_TYPE_NUMERIC_LIMIT_MULTIPLE                             #
                    for individualDataValue in _dataValue:                                      #
                        _subDataValue: multiMeasurementData = individualDataValue               #
                                                                                                #
                        _measurementBlockToReturn.append(Numeric_Measurement(                   #
                            value       = _subDataValue.recordedValue,                          #
                            compOp      = CODES.COMPARISON_OPERATOR_LESS_EQUAL,                 #
                            status      = self.determineWATSstatusCode(_subDataValue.result),   #
                            unit        = _subDataValue.units,                                  #
                            name        = _subDataValue.name,                                   #
                            highLimit    = _subDataValue.comparison.compareVal_L                #
                        ))                                                                      ####

            case TestStepDecoder.COMP_TYPE_GELE:                                                #### #### GREATER THAN OR EQUAL TO OR LESS THAN OR EQUAL TO TYPE (Numeric only)
                
                if not isinstance(_dataValue, list):                                            #### Single-Numeric
                    s_type = CODES.STEP_TYPE_NUMERIC_LIMIT_SINGLE                               #
                    _measurementBlockToReturn = Numeric_Measurement(                            #
                        value       = _dataValue,                                               #
                        compOp      = CODES.COMPARISON_OPERATOR_GREATER_EQUAL_LESS_EQUAL,       #
                        status      = _measurementResult,                                       #
                        unit        = _units,                                                   #
                        name        = _name,                                                     #
                        lowLimit    = _comparisonObject.compareVal_L,                           #
                        highLimit   = _comparisonObject.compareVal_H                            #
                    )                                                                           ####

                elif isinstance(_dataValue, list):                                              #### Multiple-Numeric
                    s_type = CODES.STEP_TYPE_NUMERIC_LIMIT_MULTIPLE                             #
                    for individualDataValue in _dataValue:                                      #
                        _subDataValue: multiMeasurementData = individualDataValue               #
                                                                                                #
                        _measurementBlockToReturn.append(Numeric_Measurement(                   #
                            value       = _subDataValue.recordedValue,                          #
                            compOp      = CODES.COMPARISON_OPERATOR_GREATER_EQUAL_LESS_EQUAL,   #
                            status      = self.determineWATSstatusCode(_subDataValue.result),   #
                            unit        = _subDataValue.units,                                  #
                            name        = _subDataValue.name,                                   #
                            lowLimit    = _subDataValue.comparison.compareVal_L,                #
                            highLimit   = _subDataValue.comparison.compareVal_H                 #
                        ))                                                                      ####

            case TestStepDecoder.COMP_TYPE_EQ:                                                  #### #### EQUAL TO TYPES

                if isinstance(_dataValue, str):                                                 #### Single-String
                    s_type = CODES.STEP_TYPE_STRING_VALUE_SINGLE                                #
                    _measurementBlockToReturn = String_Measurement(                             #
                        value       = _dataValue,                                               #
                        compOp      = CODES.COMPARISON_OPERATOR_IGNORE_CASE,                    #
                        status      = _measurementResult,                                       #
                        name        = _name,                                                     #
                        limit       = _comparisonObject.compareVal                              #
                    )                                                                           ####

                elif isinstance(_dataValue, list) and isinstance(_dataValue[0], str):           #### Multi-String
                    s_type = CODES.STEP_TYPE_STRING_VALUE_MULTIPLE                              #
                    for individualDataValue in _dataValue:                                      #
                        _subDataValue: multiMeasurementData = individualDataValue               #
                                                                                                #
                        _measurementBlockToReturn.append(String_Measurement(                    #
                            value   = _subDataValue.recordedValue,                              #
                            compOp  = CODES.COMPARISON_OPERATOR_IGNORE_CASE,                    #
                            status  = self.determineWATSstatusCode(_subDataValue.result),       #
                            limit   = _subDataValue.comparison.compareVal                       #
                        ))                                                                      ####

                elif isinstance(_dataValue, float|int):                                         #### Single-Numeric
                    s_type = CODES.STEP_TYPE_NUMERIC_LIMIT_SINGLE                               #
                    _measurementBlockToReturn = Numeric_Measurement(                            #
                        value       = _dataValue,                                               #
                        compOp      = CODES.COMPARISON_OPERATOR_EQUAL,                          #
                        unit        = _units,                                                   #
                        status      = _measurementResult,                                       #
                        name        = _name,                                                     #
                        matchValue  = _comparisonObject.compareVal,                             #
                        lowLimit    = _comparisonObject.compareVal                              # --> Required for EQ operation in WATS
                    )                                                                           ####

                elif isinstance(_dataValue, list) and isinstance(_dataValue[0], float|int):     #### Multi-Numeric
                    s_type = CODES.STEP_TYPE_NUMERIC_LIMIT_MULTIPLE                             #
                    for individualDataValue in _dataValue:                                      #
                        _subDataValue: multiMeasurementData = individualDataValue               #
                                                                                                #
                        _measurementBlockToReturn.append(Numeric_Measurement(                   #
                            value       = _subDataValue.recordedValue,                          #
                            compOp      = CODES.COMPARISON_OPERATOR_EQUAL,                      #
                            unit        = _subDataValue.units,                                  #
                            name        = _subDataValue.name,                                   #
                            matchValue  = _subDataValue.comparison.compareVal                   #
                        ))                                                                      ####

            case TestStepDecoder.COMP_TYPE_REGEX:                                               #### #### REGEX TYPES (Strings only, single only)
                if not isinstance(_dataValue, str):                                             #
                    raise TypeError(f"The type of {_dataValue.__class__} is not supported!")    #
                                                                                                #
                s_type = CODES.STEP_TYPE_STRING_VALUE_SINGLE                                    #
                _measurementBlockToReturn = String_Measurement(                                 #
                    value = _dataValue,                                                         #
                    compOp = CODES.COMPARISON_OPERATOR_IGNORE_CASE,                             #
                    status = _measurementResult,                                                #
                    name = _name,                                                                #
                    limit = _comparisonObject.compareVal                                        #
                )                                                                               ####

            case TestStepDecoder.COMP_TYPE_EQ_BOOL:                                             #### #### BOOLEAN TYPES (Single-Measurements only)
                if not isinstance(_dataValue, bool):
                    raise TypeError(f"The type of {_dataValue.__class__} is not supported!")
                
                s_type = CODES.STEP_TYPE_PASSFAIL_SINGLE
                _measurementBlockToReturn = Boolean_Measurement(
                    status = _measurementResult,
                    name = _name
                )

            case _:
                raise IndexError(f"Unknown comparison type of {_comparisonObject.type} used! Unable to continue parsing WATS objects.")

        return (s_type, _measurementBlockToReturn)
    

    def determineWATSstatusCode(self, passFail:bool) -> str:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param passFail: A boolean denoting the final status of a particular block.

        ## Matching the WATS Status Code
        Function takes in a boolean denoting the final status of the block and returns the appropriate WATS code.
        """

        if passFail:
            s_status = CODES.STATUS_CODE_PASSED
        else:
            s_status = CODES.STATUS_CODE_FAILED

        return s_status


    def generateMultiStep(self, stepResult:MultiTestReport) -> Test_Step:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        .. WARNING:: Multi-measurement test steps with reagrds to WATS do not support concurent boolean measurements.

        :param stepResult: A multistepreport that needs to be converted into a WATS object.

        :returns Test_Step: A new WATS Test_Step object from the multitestreport the function was passed.
        """

        # FAILS WITH EQUAL LIST OBJECTS

        s_status:str = self.determineWATSstatusCode(stepResult.result)

        s_type:str = ""
        _listOfMeasurementBlocks:List[String_Measurement|Numeric_Measurement] = []
        for measurement in stepResult.measurements:
           s_type, block = self.generateWATSmeasurmentBlock(measurement)
           _listOfMeasurementBlocks.append(block)
        
        _strMeas = None
        _numMeas = None
        _boolMeas = None
        if isinstance(_listOfMeasurementBlocks[0], String_Measurement):
            _strMeas = _listOfMeasurementBlocks
        elif isinstance(_listOfMeasurementBlocks[0], Numeric_Measurement):
            _numMeas = _listOfMeasurementBlocks

        return Test_Step(
            id                  = stepResult.stepIndex,
            name                = stepResult.stepName,
            status              = s_status,
            stepType            = s_type,
            start               = None,
            totTime             = stepResult.durationOfStepSeconds,
            group               = CODES.GROUP_MAIN,
            errorCode           = None,
            errorMessage        = None,
            causedSeqFailure    = stepResult.causedTotalFailure,
            causedUUTFailure    = stepResult.causedTotalFailure,
            reportText          = None,
            interactiveExeNum   = None,
            numericMeas         = _numMeas,
            stringMeas          = _strMeas,
            booleanMeas         = _boolMeas
        )


    def generateSingleStep(self, stepResult:SingleTestReport) -> Test_Step:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param stepResult: A singletestreport that needs to be converted into a WATS object.

        :returns Test_Step: A new WATS Test_Step object from the singletestreport the function was passed.
        """

        s_status:str = self.determineWATSstatusCode(stepResult.result)
        s_type, _measurementBlock = self.generateWATSmeasurmentBlock(stepResult)

        s_numeric_meas = None
        s_string_meas = None
        s_bool_meas = None

        if isinstance(_measurementBlock, Numeric_Measurement): s_numeric_meas = _measurementBlock
        elif isinstance(_measurementBlock, String_Measurement): s_string_meas = _measurementBlock
        elif isinstance(_measurementBlock, Boolean_Measurement): s_bool_meas = _measurementBlock
        else:
            raise TypeError(f"The type of {_measurementBlock.__class__} is not supported!")
        
        return Test_Step(
            id                  = stepResult.stepIndex,
            name                = stepResult.stepName,
            status              = s_status,
            stepType            = s_type,
            start               = None,
            totTime             = stepResult.durationOfStepSeconds,
            group               = CODES.GROUP_MAIN,
            errorCode           = None,
            errorMessage        = None,
            causedSeqFailure    = stepResult.causedTotalFailure,
            causedUUTFailure    = stepResult.causedTotalFailure,
            reportText          = None,
            interactiveExeNum   = None,
            numericMeas         = s_numeric_meas,
            stringMeas          = s_string_meas,
            booleanMeas         = s_bool_meas
        )
    

    def generateRootSequenceCall(self, uutInfo:aemUUT) -> Root_Seqeunce:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param uutInfo: The AEM UUT object that will create the base of the root sequence.

        :returns Root_Sequence: The object version of the WATS root sequence.
        """

        r_status = self.determineWATSstatusCode(uutInfo.overallResult)

        return Root_Seqeunce(
            id=0,
            name="MainSequence Callback",
            status=r_status, # dynmaic
            stepType="SequenceCall",
            totTime=uutInfo.durationOfRun,
            group="M",
            reportText=None,
            blocks=self.testSteps,
            callback=Sequence_Call(
                name="Main",
                version="1.0",
                path="~/DSP2_Testware/configurations/dsp2_bon_test_steps.json"
            )
        )

################################################################

## OTHER CODE ##

################################################################

# EOF