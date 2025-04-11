################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: testStepDecoder.py
# | Date: 2024-08-15
# | Rev: 0 
# | Change By: Everly Larche
# | ECO Ref:
#  ----------------
# | Project Name: AEM Test & Measurement Platform
# | Developer: Everly Larche
# | File Description:
#  ----------------
################################################################
################################################################

## IMPORT FILES ##
from dataclasses import dataclass
from typing import List
import os, json

################################################################

## CLASS DEFINITION AND METHODS ##
@dataclass
class payload:
    '''
    .. versionadded:: 0.0
    .. versionchanged:: 0.0

    A sub-compoent of a testStep containing the action of this step (ex. to execute a method in a thread/process and giving its arguments if any)
    '''
    
    threadName: str
    action: str
    message: any
    deliverTo: str


@dataclass
class expect:
    '''
    .. versionadded:: 0.0
    .. versionchanged:: 0.4

    A sub-compoent of a testStep containing information about how to determine pass/fail criteria of a step or measurement within a step.
    
    .. NOTE:: The `name` field in this data structure is for matching to a `multiValueTestData` object when a test step has more than one measurement. Otherwise it is defualted to None and does not need to be accounted for.
    '''
    
    type: str|None = None
    units: str|None = None
    compareVal: float|int|str|list|None = None
    compareVal_H: float|int|None = None
    compareVal_L: float|int|None = None
    compareTol: float|None = None
    name: str|None = None


@dataclass
class testStep:
    '''
    .. versionadded:: 0.0
    .. versionchanged:: 0.0

    A data structure for each test step to be preformed. A 1:1 representation of the JSON-formatted step in the testSteps file.
    '''

    step: int
    slotIndex: int
    name: str
    block: bool
    retry: bool
    saveData: bool

    payload:payload
    expect:expect|List[expect]
    
    multipleMeasurements:bool|None = None


# --------------------------------------------------------------------------------------


class TestStepDecoder:
    '''
    .. versionadded:: 0.0
    .. versionchanged:: 0.0

    Used to decode one test step at a time, execute it and move to the next step.\n
    If a test step talks to a thread/process other than the MAIN THREAD - data needs to be stored for the next testStep object to use.\n
    If a testStep is **NONBLOCKING** after the testStep is processed - the next testStep will begin decoding.\n

    *All references to the comaprsion types in this class are from the refernce point of the recorded value from a UUT.*
    '''

    COMP_TYPE_NONE: str|None = None
    '''
    .. versionadded:: 0.0
    .. versionchanged:: 0.0

    Used when expecting nothing to compare against - used in steps where setup actions are being taken such that a reading can be made.'''

    COMP_TYPE_CONTAINS: str = "CONTAINS"
    '''
    ..versionadded:: 0.3
    ..versionchanged:: 0.3

    Used when trying to find a substring in string comparisions.
    '''

    COMP_TYPE_GT: str = "GT"
    '''
    .. versionadded:: 0.0
    .. versionchanged:: 0.0

    Denotes a single-bound **greater-than** comparison to take place.'''

    COMP_TYPE_LT: str = "LT"
    '''
    .. versionadded:: 0.0
    .. versionchanged:: 0.0

    Denotes a single-bound **less-than** comparison to take place.'''

    COMP_TYPE_GTLT: str = "GTLT"
    '''
    .. versionadded:: 0.0
    .. versionchanged:: 0.0

    Denotes a double-bound **greater-than** *or* **less-than** comparison to take place.'''

    COMP_TYPE_GE: str = "GE"
    '''
    .. versionadded:: 0.0
    .. versionchanged:: 0.0

    Denotes a single-bound **greater-than** *or* **equal-to** compairson to take place.'''

    COMP_TYPE_LE: str = "LE"
    '''
    .. versionadded:: 0.0
    .. versionchanged:: 0.0

    Denotes a single-bound **less-than** *or* **equal-to** compairson to take place.'''

    COMP_TYPE_GELE: str = "GELE"
    '''
    .. versionadded:: 0.0
    .. versionchanged:: 0.0

    Denotes a double-bound **greater-than** *or* **equal-to** *or* **less-than** *or* **equal-to** comaprison to take place.'''

    COMP_TYPE_EQ: str = "EQUALS"
    '''
    .. versionadded:: 0.0
    .. versionchanged:: 0.0

    Denotes a exact **equals-to** comparison to take place.'''

    COMP_TYPE_REGEX: str = "REGEX"
    '''
    .. versionadded:: 0.0
    .. versionchanged:: 0.0

    Denotes a **regular-expression** comapirson type should be prossesed'''

    COMP_TYPE_EQ_LIST: str = "EQUALSLIST"
    '''
    .. versionadded:: 0.0
    .. versionchanged:: 0.0

    Denotes a series of **equals-to** comapirsons should take place.'''

    COMP_TYPE_EQ_BOOL: str = "BOOL"
    '''
    .. versionadded:: 0.0
    .. versionchanged:: 0.0

    Denotes a single **true or false (boolean)** comaprison is to take place.
    '''

    MULTI_READING_KEY: str = "Multiple-Measurements"
    """
    .. versionadded:: 0.4
    .. versionchanged:: 0.4
    """


    def __init__(self, testStepFile:os.path, phase:str) -> None:
        # Set class-wide variables
        self.testFilePath: os.path = testStepFile
        self.phase: str = phase

        return None


    def decode(self, index:int) -> testStep:
        '''
        .. versionadded:: 0.0
        .. versionchanged:: 0.0

        Primary interaction method with this class.

        Will take in a test Step index and isolate that step from the JSON file.
        Returns a data object containing all information from the step inside the JSON file to
        be used in the MAIN THREAD.
        '''

        self.index: int = index

        # Open the file and start to process Keys
        with open(self.testFilePath, 'r') as testStepJSON:
            _localCopyJSON:dict = json.load(testStepJSON)

        # Isolate to only the current step
        _localCopyJSON = _localCopyJSON[self.phase]
        _localCopyJSON = _localCopyJSON[self.index]

        try:
            _payload:payload = self.decodePayload(
                partialJSON=_localCopyJSON["Payload"]
            )
            _expect:expect = self.decodeExpect(
                partialJSON=_localCopyJSON["Expect"]
            )

        except Exception:
            pass # Handled at a later point on return

        return testStep(
            step                    = _localCopyJSON["Step"],
            slotIndex               = _localCopyJSON["Test-Slot-Index"],
            name                    = _localCopyJSON["Name"],
            block                   = _localCopyJSON["Blocking-Action"],
            retry                   = _localCopyJSON["Should-Retry"],
            saveData                = _localCopyJSON["Save-Result"],
            multipleMeasurements    = _localCopyJSON.get(self.MULTI_READING_KEY, None),
            payload                 = _payload,
            expect                  = _expect
        )


    def _correctStep(self, stepValue:int) -> bool:
        '''
        .. versionadded:: 0.0
        .. versionchanged:: 0.0
        .. versiondeprecated:: 0.1

        .. WARNING:: This method has not been used and is no longer active.

        Should check to see the key:value pair for "Step"
        matches the current index used on the JSON list.

        If it does not match, return false to throw an ERROR in the MAIN THREAD.
        '''

        raise DeprecationWarning("This method is deprecated")
        
        _correct: bool = False

        if self.index == stepValue: _correct = True

        return _correct


    def decodePayload(self, partialJSON:dict) -> payload:
        '''
        .. versionadded:: 0.0
        .. versionchanged:: 0.0

        Sub-compoent of decode() - translates the payload block of the json-formatted test step and returns it as a python object to be used as a field inside the testStep python object.
        '''
        
        _threadName: str = partialJSON["Thread-Name"]
        _action: str = partialJSON["Action"]
        _message: any = partialJSON["Message"]
        _deliverTo: str = partialJSON["Deliver-To-Thread"]

        if len(_message) <= 1: _message = _message[0]

        return payload(
            _threadName,
            _action,
            _message,
            _deliverTo
        )


    def decodeExpect(self, partialJSON:dict) -> expect:
        '''
        .. versionadded:: 0.0
        .. versionchanged:: 0.4

        Sub-compoent of decode() - translates the expect block of the json-formatted test step and returns it as a python object to be used as a field inside the testStep python object.
        '''
        
        try:
            _type: str = partialJSON["Type"]
            _units: str = partialJSON["Units"]

            try:
                _name = partialJSON["Name"]
            except KeyError:
                _name = None

            try:
                _compareVal = partialJSON["Compare-Value"]
            except KeyError:
                _compareVal = None

            try:
                _compareVal_H = partialJSON["Compare-Value-High"]
            except KeyError:
                _compareVal_H = None

            try:
                _compareVal_L = partialJSON["Compare-Value-Low"]
            except KeyError:
                _compareVal_L = None

            try:
                _compareTol = partialJSON["Compare-Tolerance"]
            except KeyError:
                _compareTol = None

        except Exception as e:
            # Is this a multi measurement block? Try to decode as a list of JSON objects
            _expectList:List[expect] = []
            for i in range(0, len(partialJSON), 1):
                _expectList.append(self.decodeExpect(partialJSON[i]))

            return _expectList

        return expect(
            name            = _name,
            type            = _type,
            units           = _units,
            compareVal      = _compareVal,
            compareVal_H    = _compareVal_H,
            compareVal_L    = _compareVal_L,
            compareTol      = _compareTol
        )


################################################################

## OTHER CODE ##

################################################################

# EOF