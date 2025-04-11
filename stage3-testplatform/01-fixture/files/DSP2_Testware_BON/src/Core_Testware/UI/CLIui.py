################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: CLIui.py
# | Date: 2025-04-04
# | Rev: 1.1
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
import os, sys
from termcolor import colored
from typing import List

from ..UnitUnderTest.UUT import miscInfo, subUUT

################################################################

## CLASS DEFINITION AND METHODS ##
class TestwareCLIui:
    """
    .. versionadded:: 1.0
    .. versionchanged:: 1.0

    Adapated code from THS Initial Check UI to serve as
    basic functions of printing to the CLI for the
    AEM Test & Measurement Platform.
    """

    # CONSTANT DEFINES
    CLI_UI_PRINT_TITLE: str                     = "print_Title"
    CLI_UI_PRINT_SPACER: str                    = "print_Spacer"
    CLI_UI_PRINT_Subtitle: str                  = "print_Subtitle"
    CLI_UI_PRINT_INFORMATION_NO_SPACER: str     = "print_Information_No_Spacer"
    CLI_UI_PRINT_INFORMATION_WITH_SPACER: str   = "print_Information_With_Spacer"
    CLI_UI_GET_USER_INPUT: str                  = "get_User_Input"
    CLI_UI_GET_SUB_UUTs: str                    = "get_subUUTs"
    CLI_UI_PRINT_UUT_DETAILS: str               = "print_UUT_Details"
    CLI_UI_PRINT_PASS_FAIL: str                 = "print_Pass_Fail"


    def __init__(self, stdINfileIO) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        Requires that a refernce to the standard input (stdin)
        from the main thread is given as this class will be the soul user of stdin.
        """
        
        self.myStdin = stdINfileIO
        sys.stdin = open(self.myStdin)

        return None


    def print_Title(self, program_Name:str, program_Version:str, test_Version:str=None) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param program_Name: The name of the program running (ex. LxDSP2.0 Bed of Nails)
        :param program_Version: A string representing the verion of the base software (core testware)
        :param test_Version: A string representing the version of the test version (ex. version of the LxDSP2 testware or F7 testware). This param is optional to ensure backwards compatability with older builds.

        Does not return with any data - output only.
        Shows the user via the CLI the main title of the fixture.
        """
        
        self.width:int = os.get_terminal_size().columns
        self.name:str = program_Name
        self.version:str = program_Version
        self.testVersion:str = test_Version

        self.print_Header()
        return None


    def print_Header(self) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        Is a sub component of self.print_Title().
        Left as another method in case we want to re-use it later.
        """
        
        print(colored("#" * self.width, color="light_cyan"))
        print(colored(f"/// {self.name} ///".center(self.width), color="light_cyan"))
        print(colored(f"$$$ Core Version:{self.version} $$$".center(self.width), color="light_cyan"))
        if None != self.testVersion: print(colored(f"$$$ Testware Version:{self.testVersion} $$$".center(self.width), color="light_cyan"))
        print(colored("#" * self.width, color="light_cyan"))
        self.print_Spacer()

        return None


    def print_Spacer(self) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        Prints a divider to the CLI. Used as both,
        primary method and sub-compoent.
        """
        
        print("\n")
        print(colored("-" * self.width, color="blue"))
        print("\n")

        return None


    def print_Subtitle(self, m_String:str) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param m_String: A string to be printed to the CLI as a subtitle. (ex. Main Test Phase)

        Prints a subtitle with the light green coloring, centered in the CLI.
        """
        
        print("\n")
        print(colored(f"{m_String}".center(self.width), color="light_green"))

        return None
    

    def print_Information_No_Spacer(self, param:str, data:str, value:str|List[float|int|str]|None=None) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param param: A String where the parameter to report on is printed with left-allignment
        :param data: A string to be a descriptor of the parameter its reporting on
        :param value: Used when printing data on a completed test step, this can be a single string or a list of datapoints if it was a multi measurement step.

        Prints some information to the CLI for the user.
        Follows the format: <Paramter to report on>...//...<Status or data from paramter>

        Depedning on the data passed, this can be indicated RED if the data == FAILED
        """

        if (None != value) and (not isinstance(value, str)):
            value = str(value)
        elif None == value:
            value = "None"
        
        _stringToPrint: str = ""
        if "FAILED" in data:
            _stringToPrint = colored(f"{param}" + "." * (self.width-(len(param)+1+len(data)+13+len(value))) + f"{data} with value: {value}", color="red")
        elif "PASSED" in data:
            _stringToPrint = colored(f"{param}" + "." * (self.width-(len(param)+1+len(data))) + f"{data}", color="green")
        else:
            _stringToPrint = f"{param}" + "." * (self.width-(len(param)+1+len(data))) + f"{data}"
        print(_stringToPrint)
        return None
    

    def print_Information_With_Spacer(self, param:str, data:str) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param param: A String where the parameter to report on is printed with left-allignment
        :param data: A string to be a descriptor of the parameter its reporting on

        Calls both print_Information_No_Spacer & print_Spacer.
        """
        
        self.print_Information_No_Spacer(param=param, data=data)
        self.print_Spacer()

        return None
    

    def get_User_Input(self, dataFor:str, query:str) -> tuple:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param dataFor: To be passed through to the return tuple, this is the name of the process where the user input needs to be delivered.
        :param query: The prompt to be displayed to the user, printed in yellow text
        :returns tuple: A tuple containing the structure and data needed/expected by the primary process

        Using the stdin file descriptor set in __init__()
        get data and return it plus the thread name it is destined for.

        User input/interactions are colored yellow.
        """
        
        return (input(colored(f"\n{query}:\n>", color="yellow")), dataFor)
    

    def get_subUUTs(self, scan:bool=False) -> tuple:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.1

        .. HINT:: This method is to be used by a test step.
        .. NOTE:: The *expect* block if using inside a test step, should be None.

        :returns: List of subUUT objects to be appened onto the `UUT.subUUT` object list.
        :raises ValueError: When the end of the loop is reached and the length of the new list is 0.
        """

        subUUTsToAdd: List[subUUT] = []
        breakCondition: bool = False

        while (not breakCondition):
            print(colored(f"\n~~~~ Adding sub-unit {len(subUUTsToAdd)} ~~~~", color="light_magenta"))

            ## The following is for scanning in sub units with std barcodes
            if scan:
                barcodeData:str = input(colored("Scan the sub unit using the handheld scanner:\n>", color="yellow")).split("/")
                subUUTsToAdd.append(
                    subUUT(
                        pn = barcodeData[0],
                        rev = barcodeData[1],
                        sn = "".join(barcodeData[2:])
                    )
                )

            else:
                newSubUnitPartNumber:str = input(colored("Sub-Unit Part Number:\n>", color="yellow"))
                newSubUnitSN:str = input(colored("Sub-Unit Serial Number:\n>", color="yellow"))
                newSubUnitRevision:str = input(colored("Sub-Unit Revision:\n>", color="yellow"))

                subUUTsToAdd.append(
                    subUUT(
                        pn = newSubUnitPartNumber,
                        rev = newSubUnitRevision,
                        sn = newSubUnitSN
                    )
                )

            if "n" == input(colored(f"Added {len(subUUTsToAdd)} subUnit(s). To stop adding sub units, press 'n' and ENTER.")):
                breakCondition = True
                break

            if len(subUUTsToAdd) == 0:
                raise ValueError("No subUUT was added!")


        return (subUUTsToAdd, "UUT subUnits")
    

    def print_UUT_Details(self, slot:str, model:str, sn:str, rev:str, fixtureName:str, fixtureSN:str, batchSN:str, user:str, miscInfo:List[miscInfo]|None, subUnits:List[subUUT]|None) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.1

        :param slot: The integer to indicate which slot index the particular UUT is located within.
        :param model: The string of the PN or model name (terms used intechangably, example: F7-G6-AX, 7315.500).
        :param sn: The string of the serial number for the UUT, typically scanned in by the user in a previous step.
        :param rev: The string of the revision for the UUT, typically part of the SN scan done previously.
        :param fixtureName: The name of the fixture from the configuration file or EEPROM of Goldilocks.
        :param fixtureSN: The string of the Goldilocks serial number either from the configuration file or EEPROM.
        :param batchSN: The batch SN from the SN scan done in a prevous step.
        :param user: The user/oeprator initials as typed/scanned in when initializing the test(s).
        :param miscInfo: The list of `UUT.miscInfo` objects contained in the UUT. To be displayed in a listed sequence with its text fields. Will print 'None' in dark-grey if None is passed.
        :param subUnits: The list of `UUT.subUnits` objects contained in the UUT. To be displayed in a listed sequence with its model/sn/rev fields. Will print 'None' in dark-grey if None is passed.

        Used to show a summary of information on a UUT that is to be tested.
        Meant to be used as a confirmation to the user prior to running tests.
        """
        
        _reportWidth = 100
        print("\n"+"-"*_reportWidth)
        print("||" + colored("$$ UUT DETAILS $$".center(_reportWidth-4), color="light_red") + "||\n")
        print("|| "+colored("Fixture Test Slot: ", color="light_magenta")+f"{slot}")
        print("|| "+colored("Model/PN: ", color="light_magenta")+f"{model}")
        print("|| "+colored("Serial Number: ", color="light_magenta")+f"{sn}")
        print("|| "+colored("Revision: ", color="light_magenta")+f"{rev}")
        print("|| "+colored("Batch Number: ", color="light_magenta")+f"{batchSN}")
        print("|| "+colored("Fixture type used to Test UUT: ", color="light_magenta")+f"{fixtureName}")
        print("|| "+colored("Fixture Serial Number used: ", color="light_magenta")+f"{fixtureSN}")
        print("|| "+colored("User of Fixture: ", color="light_magenta")+f"{user}")
        print("||" + "".center(_reportWidth-4) + "||")
        print("||" + colored("$$ Sub Unit(s) $$".center(_reportWidth-4), color="light_red") + "||\n")
        if None == subUnits: print("|| "+colored("None", color="dark_grey"))
        else:
            for subUnit in subUnits:
                print("|| "+colored("Model: ", color="light_magenta")+f"{subUnit.pn}")
                print("|| "+colored("Revision: ", color="light_magenta")+f"{subUnit.rev}")
                print("|| "+colored("Serial Number: ", color="light_magenta")+f"{subUnit.sn}")
                print("|| "+colored("Sub-Unit Type: ", color="light_magenta")+f"{subUnit.partType}\n")
        print("||" + "".center(_reportWidth-4) + "||")
        print("||" + colored("$$ Misc. Info $$".center(_reportWidth-4), color="light_red") + "||\n")
        if None == subUnits: print("|| "+colored("None", color="dark_grey"))
        else:
            for info in miscInfo:
                print("|| "+colored(f"{info.description}: ", color="light_magenta")+f"{info.text}")

        print("-"*_reportWidth)

        return None
    

    def print_Pass_Fail(self, overallPF:bool) -> None:
        """
        .. versionadded:: 1.0
        .. versionchanged:: 1.0

        :param overallPF: Boolean of the final pass fail status of the UUT.

        At the very end of a test sequence, clearly show the user P/F
        and color it accordingly. Only support single UUT at this time.
        """
        
        _finalWidth:int = 60
        _color="red"

        _asciiPASS:list = [
            "  _       __  __  _  _  ".center(self.width),
            " |_) /\  (_  (_  |_ | \ ".center(self.width),
            " |  /--\ __) __) |_ |_/ ".center(self.width)
        ]

        _asciiFAIL:list = [
            " _     ___     _  _".center(self.width),
            "|_ /\   |  |  |_ | \\".center(self.width),
            "| /--\ _|_ |_ |_ |_/".center(self.width)
        ]

        _frame: str = ("@"*_finalWidth).center(self.width)

        _asciiToPrint: list = _asciiFAIL
        if overallPF:
            _color="green"
            _asciiToPrint = _asciiPASS

        print("\n")
        print(colored(_frame, _color))
        print("\n")
        print(colored("FINAL UUT RESULT:".center(self.width), _color))
        print("\n")
        for line in _asciiToPrint: print(colored(line, _color))
        print("\n")
        print(colored(_frame, _color))

        return None


################################################################

## OTHER CODE ##

################################################################

# EOF