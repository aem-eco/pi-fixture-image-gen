################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: exportAsCSV.py
# | Date: 2024-10-24
# | Rev: 0 
# | Change By: Everly Larche
# | ECO Ref: CTF-75
#  ----------------
# | Project Name: AEM Test & Measurement Platform
# | Developer: Everly Larche
# | File Description: generates a CSV file object to represent all test report data for export to a file-system
#  ----------------
################################################################
################################################################

## COMPONENT USE // EXPECTED INPUT/OUTPUT AND LIMITATIONS // LIBRARY DESIGNED FOR ##

################################################################

## IMPORT FILES ##
import csv, datetime, os

from ..UnitUnderTest.UUT import UUT as aemUUT
from ..UnitUnderTest.UUT import SingleTestReport, MultiTestReport
from ..UnitUnderTest.UUT import subUUT as subUnitType
from ..UnitUnderTest.UUT import miscInfo as miscInfoType

################################################################

## CLASS DEFINITION AND METHODS ##
class CreateCSV:
    '''
    .. versionadded:: 0.3
    .. versionchanged:: 0.4

    Impliments the following components of file creation:
    - Taking in aemUUT object data
    - Writing aemUUT object data to a temp csv file on the system

    With the csv as a file on the system under .temp (local) - the file can be used to copy to either:
    1. A local mountable drive
    2. Read into a bytes object to move to Sharepoint Online

    .. NOTE:: Beyond creating the temp file, this class does not impliment any of the above functions.
    '''

    ENCODING: str = "utf-8"
    '''.. versionadded:: 0.3
    .. versionchanged:: 0.3
    Type of string encoding for data inside the csv'''

    TEMP_PATH: str = ".temp"
    '''.. versionadded:: 0.3
    .. versionchanged:: 0.3
    Local refernce from main.py to the temp folder for writing the csv to for transfer elsewhere.'''

    def __init__(self, unitData:aemUUT) -> None:
        self.unitData = unitData

        return None
    

    def genCSV(self) -> os.PathLike:
        '''
        .. versionadded:: 0.3
        .. versionchanged:: 0.4

        Using data from an aemUUT object this method will then create a temp file
        continaing the final csv report output. The returned filepath is to the temp file
        so that it can be actioned upon in another class or method.
        '''

        path: os.PathLike = os.path.join(os.getcwd(), self.TEMP_PATH, (str(self.unitData.serialNumber+'-'+datetime.datetime.now().isoformat()).replace('/', '-').replace(':', '-').replace('.', '-')+".csv"))
        dirPath: os.PathLike = os.path.join(os.getcwd(), self.TEMP_PATH)
        if not os.path.exists(dirPath): os.mkdir(dirPath)

        with open(path, 'w', encoding=self.ENCODING) as file:
            reportWriter = csv.writer(
                file
            )

            reportWriter.writerow(["=== START REPORT ==="])
            reportWriter.writerow(["=== HEADER ==="])
            reportWriter.writerow(["AEM Test & Measurement Platform"])
            reportWriter.writerow(["UUT Report"])
            reportWriter.writerow(["Platform Version:x.x.x"])
            reportWriter.writerow([f"Report Date:{datetime.datetime.now().isoformat()}"])
            reportWriter.writerow(["=== END HEADER ==="])

            reportWriter.writerow([''])
            
            reportWriter.writerow(["=== UUT INFORMATION ==="])
            reportWriter.writerow(['UUT Part Number', self.unitData.model])
            reportWriter.writerow(['UUT Revision', self.unitData.rev])
            reportWriter.writerow(['Batch', self.unitData.batchSerialNumber])
            reportWriter.writerow(['Serial Number', self.unitData.serialNumber])
            reportWriter.writerow(['User Initials', self.unitData.user])
            reportWriter.writerow(['Test Slot (Channel)', self.unitData.testSlot])
            reportWriter.writerow(['Run Start Datetime', self.unitData.startDatetime])
            reportWriter.writerow(['Run Duration (sec)', self.unitData.durationOfRun])
            reportWriter.writerow(["=== END UUT INFORMATION ==="])
            
            reportWriter.writerow([''])

            reportWriter.writerow(["=== SUB UUT INFORMATION ==="])
            if isinstance(self.unitData.subUUTs, list):
                for subUUT in self.unitData.subUUTs:
                    if not isinstance(subUUT, subUnitType): raise TypeError(f"Type: {subUUT.__class__} is not a vlaild subunit type!")
                    reportWriter.writerow(['Part Number', subUUT.pn])
                    reportWriter.writerow(['Part Revision', subUUT.rev])
                    reportWriter.writerow(['Serial Number', subUUT.sn])
                    reportWriter.writerow(['Part Type', subUUT.partType])
            reportWriter.writerow(["=== END SUB UUT INFORMATION ==="])

            reportWriter.writerow([''])

            reportWriter.writerow(["=== MISC INFORMATION ==="])
            if isinstance(self.unitData.miscInfo, list):
                for miscInfo in self.unitData.miscInfo:
                    if not isinstance(miscInfo, miscInfoType): raise TypeError(f"Type: {miscInfo.__class__} is not a vlaild miscInfo type!")
                    reportWriter.writerow(['MiscInfo', miscInfo.description, miscInfo.text, miscInfo.numeric, miscInfo.typedef])
            reportWriter.writerow(["=== END MISC INFORMATION ==="])

            reportWriter.writerow([''])

            reportWriter.writerow(["=== TEST STEPS ==="])
            for testStep in self.unitData.testStepResults:
                # Common elements are done here
                reportWriter.writerow(['Step Index', testStep.stepIndex])
                reportWriter.writerow(['Step Name', testStep.stepName])
                reportWriter.writerow(['Result (bool)', testStep.result])
                reportWriter.writerow(['Step Duration (sec)', testStep.durationOfStepSeconds])

                if isinstance(testStep, SingleTestReport):
                    reportWriter.writerow(['Using Units', testStep.units])
                    reportWriter.writerow(['Comparison Type', testStep.comparison.type])
                    reportWriter.writerow(['Recorded Value', testStep.recordedValue])
                    reportWriter.writerow(['Direct Comparison Value', testStep.comparison.compareVal])
                    reportWriter.writerow(['Tolerance Used', testStep.comparison.compareTol])
                    reportWriter.writerow(['High Limit', testStep.comparison.compareVal_H])
                    reportWriter.writerow(['Low Limit', testStep.comparison.compareVal_L])
                elif isinstance(testStep, MultiTestReport):
                    for measurement in testStep.measurements:
                        reportWriter.writerow(['-->', 'Measurement Name', measurement.name])
                        reportWriter.writerow(['-->', 'Result (bool)', measurement.result])
                        reportWriter.writerow(['-->', 'Units', measurement.units])
                        reportWriter.writerow(['-->', 'Value', measurement.recordedValue])
                        reportWriter.writerow(['-->', 'Comparison Type', measurement.comparison.type])
                        reportWriter.writerow(['-->', 'Direct Comparison Value', measurement.comparison.compareVal])
                        reportWriter.writerow(['-->', 'Tolerance Used', measurement.comparison.compareTol])
                        reportWriter.writerow(['-->', 'High Limit', measurement.comparison.compareVal_H])
                        reportWriter.writerow(['-->', 'Low Limit', measurement.comparison.compareVal_L])

                else:
                    raise TypeError(f"Type of test step: {testStep.stepName} does not match SingleTestReport or MultiTestReport!")
            
            reportWriter.writerow(["=== END TEST STEPS ==="])
            reportWriter.writerow(['=== END OF REPORT ==='])

        return path

################################################################

## OTHER CODE ##

################################################################

# EOF