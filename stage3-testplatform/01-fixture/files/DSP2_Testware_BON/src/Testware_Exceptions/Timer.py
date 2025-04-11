################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: Timer.py
# | Date: 2024-12-23
# | Rev: 0 
# | Change By: Everly Larche
# | ECO Ref:
#  ----------------
# | Project Name: AEM Test & Measurement Platform
# | Developer: Everly Larche
# | File Description: Wrapper/decorator function to apply a timeout to functions within the same thread.
#  ----------------
################################################################
################################################################

## IMPORT FILES ##
import time

################################################################

## CLASS DEFINITION AND METHODS ##
def ApplyTimeoutSeconds(timeoutValue:float):
    '''
    
    '''

    def functionWrap(func):
        timeStart:float = time.perf_counter()
        return func()
    
    
    
    return


################################################################

## OTHER CODE ##

################################################################

# EOF