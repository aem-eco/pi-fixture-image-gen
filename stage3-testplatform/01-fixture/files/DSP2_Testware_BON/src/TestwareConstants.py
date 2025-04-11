################################################################

## CONSTANTS ##
MAIN_THREAD_NAME:str = "MAIN THREAD"
'''
.. versionadded:: 0.0.0

Name used by test steps to identify something should be executed inside the main thread
'''

UI_THREAD_NAME: str = "UI"
'''
.. versionadded:: 0.0.0

Name used by test steps to identify something should be executed on the UI thread.\n
This can also include code inside the main thread such as updating a field in a UUT object from user input on STDIN.
'''

F7_THREAD_NAME: str = "F7CLI"

VERSION:str = "1.0.0"
'''
.. versionadded:: 0.0.0
Version number of the AEM Testware and its components
'''

THREAD_STATUS:str = "STATUS"
'''
.. versionadded:: 0.0.0
'''

THREAD_FLAG: str = "FLAG"
'''
.. versionadded:: 0.0.0
'''

THREAD_METHOD: str = "Method"
'''
.. versionadded:: 0.0.0
'''

THREAD_CARRY_METHOD: str = "CARRY_METHOD"
'''
.. versionadded:: 0.0.0
'''

THREAD_DATA: str = "DATA"
'''
.. versionadded:: 0.0.0
'''

THREAD_ACKN: str = "ACKN"
'''
.. versionadded:: 0.0.0
.. deprecated:: 0.0.0
'''

PRE_TEST_PHASE: str = "Pre-Test"
'''
.. versionadded:: 0.0.0

Key of once of the three primary elements inside a test step json file.\n
the value matching "Pre-Test" will be a list of test steps formatted as JSON. This key therefore is the indication of the testing phase.\n
All test step json files for all fixtures must contain this key.'''

MAIN_TEST_PHASE: str = "Test-Steps"
'''
.. versionadded:: 0.0.0

Key of once of the three primary elements inside a test step json file.\n
the value matching "Test-Steps" will be a list of test steps formatted as JSON. This key therefore is the indication of the testing phase.\n
All test step json files for all fixtures must contain this key.\n
*This is the bulk of the test step file and contains all tests for UUT(s) to pass or fail*'''

POST_TEST_PHASE: str = "Post-Test-Steps"
'''
.. versionadded:: 0.0.0

Key of once of the three primary elements inside a test step json file.\n
the value matching "Post-Test-Steps" will be a list of test steps formatted as JSON. This key therefore is the indication of the testing phase.\n
All test step json files for all fixtures must contain this key.\n
*This is where cleanup tasks can be done to prepare for another run or to gracefully shutdown systems on a UUT.*\n
**No steps affecting the outcome of the test may be done in this phase.**'''

N_RESET_FIXTURE_TRIGGER: str = "CLOSE"
'''
.. versionadded:: 0.0.0

This string is the trigger keyword for closing this AEM Testware application. If at the very end of a test step file, the designer wishes to ask for another run or to close the application, this string may be typed into the console to gracefully shutdown the fixture.\n
*The string is case-sensitive*'''

DUMMY_PLAYLOAD_DELIVER_TO: str = "_"
"""
.. versionadded:: 0.0.2
.. versionchanged:: 0.0.2
"""