"""
Kasper De Smaele

This script  contains the function to estimate battery SOC, it can be called in a separate file by the user to estimate battery 
capacity based on battery current, voltage, temperature, nominal capacity and charge/discharge state.  
"""

#Imports
import numpy as np
import os
from tensorflow.keras.models import load_model


#Load capacity estimation models
dischargemodel = load_model(os.path.join(os.getcwd(),'Discharging Model'))
chargemodel_CC = load_model(os.path.join(os.getcwd(), 'Charging Voltage Model'))


#Define estimation function
#Input: Current (A), Voltage (V), Temperature (K), Nominal Capacity (Ah), Charge state variable 
#Output: Tuple containing (current capacity estimate in Ah, %capacity estimate of total battery nominal capacity)

#temperarture regression coefficients
a= -1.29012573E-10
b = 2.30623390E-07
c = - 1.71461960E-04
d = 6.78632246E-02
e = -1.50811042E+01
f = 1.78424165E+03
g = - 8.78019915E+04

#current regression coefficients
z = 0.120644574
y = -0.174536454
x = -0.350157288
w = 2.36269085

#Function for temperature factor regression 
def temp_factor(T):
    alpha = (a*T**6) + (b * T**5) + (c * T**4) + (d* T**3) + (e*T**2) + (f*T) +g
    return alpha

#Function for capacity regression
def CV_regression(I): 
    cap = z*I**3 + y*I**2 + x*I + w
    return cap


#Function to estimate battery capacity
#In: current (A), voltage (V), Temperature (K), Battery nominal capacity (Ah), Charging (during charging = True, else = False)
def estimateCapacity(Current, Voltage, Temperature, Nominal_Capacity, Charging):
    
    #Check input range is valid and throw exception if not (limits arbitrary for now)
    if Temperature<252.0 or Temperature>334.0: 
        raise Exception("Temperature out of range")
    elif Voltage<2.75 or Voltage>4.5:
        raise Exception("Voltage out of range")
    elif Current<0.0 or Current>5.0:
        raise Exception("Current out of range")
    
    #Check if charging the battery
    if Charging: 
        
        #check if in constant current section of charging
        if Current>=0.98: 
            #Predict capacity with constant current model 
            cap_est =  chargemodel_CC.predict(np.array([[Voltage]]))[0][0]*temp_factor(Temperature)
            return cap_est, max(0,min(100, int(cap_est/(Nominal_Capacity)*100)))
        
        #Check if in constant voltage section 
        elif Current <0.98:
            #Predict capacity with regression model 
            cap_est = temp_factor(Temperature)*CV_regression(Current)+0.15 #Offset corrects for disconnect between CV and CC models, see documentation
            return cap_est, max(0,min(100,int(cap_est/(Nominal_Capacity)*100)))
            
    #if not charging the battery
    elif not Charging:
        #Predict capacity with discharge model
        current_Cap = dischargemodel.predict(np.array([[Current, Voltage, Temperature]]))[0][0]
        return current_Cap, max(0, min(100, int(current_Cap/(Nominal_Capacity)*100)))
    
    
