################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: UUT.py
# | Date: 2024-10-24
# | Rev: 1
# | Change By: Everly Larche
# | ECO Ref:
#  ----------------
# | Project Name: AEM Test & Measurement Platform
# | Developer: Everly Larche
# | File Description: A data class for storing all information about a UUT
#  ----------------
################################################################
################################################################

## IMPORT FILES ##
from dataclasses import dataclass
from typing import List
from datetime import datetime as DT

from ..TestSteps.testStepDecoder import expect

################################################################

## CLASS DEFINITION AND METHODS ##
@dataclass
class multiMeasurementData:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    .. NOTE:: Must be matched with a `expect` object at time of report gen. matched by `name` field.
    """

    name: str
    """
    The uniquie (to this test step) name of the measurement. Non-optional in WATS multi-measurement steps.
    """

    result: bool
    """
    The pass/fail status of the individual measurement.
    """

    units: str
    """
    The string representation of the measurement unit.
    """

    recordedValue: str|float|int
    """
    The measurement value, supports alpha-numeric values.
    """

    comparison: expect
    """
    The limits of the measurement.
    """


@dataclass
class MultiTestReport:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0
    """

    stepName: str
    """
    The name of the step to be reported.
    """

    stepIndex: int
    """
    The unique integer index of the step.
    """

    result: bool
    """
    The overall result of this step (top-level pass/fail from the measurements).
    """

    causedTotalFailure: bool
    """
    Did a signle measurement in this step cause the UUT to fail the entire sequence?
    """

    durationOfStepSeconds: float
    """
    The total time of the multi-test step, including the time to complete all measurements.
    """

    measurements: List[multiMeasurementData]
    """
    The list of measurement fields to be placed in the report as dropdown of the step.
    """


@dataclass
class SingleTestReport:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    The SingleTestReport dataclass is a sub-object of the AEM UUT dataclass and is designed
    with WATS data conversion in mind.
    """

    stepName: str
    """
    The name of the step to be reported.
    """

    stepIndex: int
    """
    The unique integer index of the step.
    """

    result: bool
    """
    The result of the measurement.
    """

    causedTotalFailure: bool
    """
    Did the measurement in this step cause the UUT to fail the entire sequence?
    """

    comparison: expect
    """
    The limits of the measurement.
    """

    recordedValue: str|float|int|bool
    """
    The alpha-numeric or boolean value recorded in this step.
    """

    units: str
    """
    The string representation of the measurement unit.
    """

    durationOfStepSeconds: float
    """
    The total time to execute and continue on from this step.
    """


@dataclass
class subUUT:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    The subUUT dataclass is a sub-object of the AEM UUT dataclass and is designed
    with the WATS key names so a 1:1 transfer using .__dict__ may occur.
    """

    pn: str
    """
    The part number of the sub UUT (a sub unit that will or does have a test report in WATS and is included in the current UUT assembly).
    """

    rev: str
    """
    The revision of the sub UUT.
    """

    sn: str
    """
    The serial number of the sub UUT.
    """

    partType: str = "Sub-Assembly"
    """
    For WATS reports, what kind of part is this? Defualt to Sub-Assembly.
    """


@dataclass
class miscInfo:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    The miscInfo dataclass is a sub-object of the AEM UUT dataclass and is designed
    with the WATS key names so a 1:1 transfer using .__dict__ may occur.
    """

    description: str
    """
    The info description is the name of the field (ex. Firmware Version).
    """

    typedef: str
    
    numeric: int
    """
    Fills the numeric value field in a WATS report. MUST be an int.
    """

    text: str
    """
    Fills the text field of the misc info line in a WATS report. This can be any valid string.
    """


@dataclass
class UUT:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    # AEM UUT Dataclass
    - Contains all core information about a UUT
    - Used by multiple components to access data about a UUT
    - Can be instanced for mutiple units in a single run of a fixture or calibrator
    """

    model: str
    """
    The model or PN string of the current UUT.
    """

    rev: str|None
    """
    The revision of the model or PN under test. Can be None.
    """

    serialNumber: str
    """
    The serial number of the current UUT. Must be a string to acomodate multiple SN formats.
    """

    batchSerialNumber: str
    """
    Batch serial number of the current UUT as a string to acomodate multiple SN formats.
    """

    testSlot: int|None
    """
    The slot index of the current UUT. Optional, set to None if not used.
    """

    fixtureName: str
    """
    The name of the fixture used to test the current UUT.
    """

    fixtureSerialNumber: str
    """
    The string of the fixture serial number used to test the current UUT.
    """

    user: str
    """
    The user or operator initials who is running the test.
    """

    subUUTs: List[subUUT]|None
    """
    A list of sub unit objects used to created a higherarchy view in WATS. May be initialized to None or never used.
    """

    miscInfo: List[miscInfo]|None
    """
    A list of misc objects containing information related to a UUT or sub unit. May be initlialized to None or never used.
    """

    testStepResults: List[SingleTestReport|MultiTestReport]
    """
    The complete list of the tests the UUT has undergone. Required.
    """

    overallResult: bool
    """
    The final pass/fail value of the UUT.
    """

    durationOfRun: float
    """
    The length in seconds since the start of the test until the last step has been completed.
    """

    startDatetime: DT
    """
    The start datetime of the test for the current UUT. Required for WATS reports and used to determine file names.
    """

    endDatetime: DT|None
    """
    The end datetime of the test for the current UUT. Optional field and typically not used over duration.
    """


################################################################

## OTHER CODE ##

################################################################

# EOF