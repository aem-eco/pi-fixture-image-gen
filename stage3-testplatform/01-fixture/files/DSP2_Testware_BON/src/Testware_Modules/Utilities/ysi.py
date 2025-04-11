
################################################################
#                ****** AEM Confidential ******
#            ---------------------------------------
# | Filename: ysi.py
# | Date: 2025-01-13
# | Rev: 1.0
# | Change By: R.Crouch
# | ECO Ref: 
#  ----------------
# | Project Name: CTF-62 - AEM T&M Platform - Python3 Library/Codebase
# | Developer: R.Crouch
# | File Description:
#  ----------------
################################################################
################################################################

## COMPONENT USE // EXPECTED INPUT/OUTPUT AND LIMITATIONS // LIBRARY DESIGNED FOR ##
################################################################

# Component Use:    Support code for thermistor calculations in testware.
# Limitations:      Currently using hardcoded coefficients for the YSI 4600.
# Example:
#   import ysi
#   
#   ysiResistance = 10000
#   print("Temp in Celsius =", ysi.toCelsius(ysiResistance))
#   print("Temp in Fahrenheit =", ysi.toFahrenheit(ysiResistance))
#   
#   tempC = -34.18
#   print("YSI Resistance =", ysi.toResistance(tempC))


## IMPORT FILES ##
################################################################
import math
import numpy as np
from scipy.optimize import fsolve

## CLASS DEFINITION AND METHODS ##
################################################################

# YSI Coeffients
ysiA = 0.0010295
ysiB = 0.0002391
ysiC = 0.0000001568

def rEquation(x, y, A, B, C):
    return 1 / (y + 273.15) - A - B * np.log(x) - C * (np.log(x))**3

def toCelsius(resistance:float)->float:
    return 1/ (ysiA + ysiB * math.log(resistance,math.e) + ysiC * math.pow(math.log(resistance,math.e),3) ) - 273.15

def toFahrenheit(resistance:float)->float:
    tempC = toCelsius(resistance)
    return (tempC * 9/5) + 32

def toResistance(tempC:float)->float:
    solution = fsolve(rEquation, 1.0, args=(tempC, ysiA, ysiB, ysiC))
    return float(solution[0])

## OTHER CODE ##
################################################################

# EOF
