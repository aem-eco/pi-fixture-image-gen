################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: threadMessenger.py
# | Date: 2024-08-06
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

## COMPONENT USE // EXPECTED INPUT/OUTPUT AND LIMITATIONS // LIBRARY DESIGNED FOR ##

################################################################

## IMPORT FILES ##
import logging

################################################################

## CLASS DEFINITION AND METHODS ##
class AEM_ThreadException(Exception):
    '''
    Custom implimentation of the python Exception class
    '''
    
    def __init__(self, code, message):
        '''
        Is run when raising an expection - to be used to verify the err code is valid and
        throw the exception.
        '''
        
        # Class varibles
        self.code = code
        self.message = message

        # Check if Valid Error Code
        # Key pair of codes is: {Code:int | Severity:str}
        self.validErrorCodes:dict = {
            0:'NONE',
            -1:'ERR/DISREG',
            -2:'ERR-OK',
            -9999:'CRITICAL ERROR',
            -10:"Pipe Message Error",
            -11:"Pipe Okay But Messge Not Sending Error",
            -20:"Execution of Method Object Error",
            -30:"RX Data Parse Error",
            -40:"TX Data Parse Error",
            -50:"Watchdog Elapsed Error",
            -60:"Received a DISREG message"
        }
        
        if not self.checkIfValid(): raise Exception(f"Bad err code {self.code}")

        out:str = f"{self.code}:{self.validErrorCodes[self.code]} | {self.message}"
        
        # Super Init of Exception Class - Throw the Exception
        super().__init__(out)


    def checkIfValid(self) -> bool:
        '''
        Checks the err code passed to constructor is valid.
        '''
        
        if self.code in self.validErrorCodes.keys(): return True
        else: return False



class customRaiser:
        '''
        Used as a wrapper to raising an Exception as to return the exception object
        for logging purposes.
        '''
        
        def raiseAEMexception(self, errCode:int, errMessage:str) -> None:
            try:
                raise AEM_ThreadException(
                    code=errCode,
                    message=errMessage
                )
            
            except AEM_ThreadException as e:
                 return e
            
            

################################################################

## OTHER CODE ##

################################################################

# EOF