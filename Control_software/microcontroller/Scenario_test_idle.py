'''
Main program of Smart battery system as issued by AE4S15
Date: 19-04-2022
Author: Mees Beumer 4648838

'''
######################## INITIALISATION ##################################################
from UART_frame_transfer_Pico import transfer
import machine
from telemetry_frame_test import telemetry

import SPI
import utime
from Desperate_test import ina219
from machine import I2C, Pin



# Define telemetry frames

global instructions

instructions = [0,0,0,0.0] # [Recovery (Y/N), Charging (Y/N), Discharging(Y/N), Capacity (float)]
error_log = [0,0,0,0,0,0,0,0,0,0] # all integer numbers to keep track of errors. Ordered acording to error code [E-01,E-02,......,E-10]


# establish GPIO pinout

ADC1 = SPI.ADC(0) # SPI pins for ADC1
ADC2 = SPI.ADC(1) # SPI pins for ADC2 <--------------------------------------------------- NOTE: problems might arise due to the again defined SPI bus

current1 = ina219(0.1,68,5)  # I2C pins for current sensor 
current2 = ina219(0.1,64,5)  # I2C pins for current sensor <--------------------------------------------------- NOTE: problems might arise due to the again defined I2C bus

ina_i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=100000)  # initialize UART bus 

charging_switch = machine.Pin(12,machine.Pin.OUT)      # pin connecting battery to charging circuit
discharging_switch = machine.Pin(13, machine.Pin.OUT) # pin connecting battery to discharging circuit
heater = machine.Pin(14,machine.Pin.OUT)                    # pin that switches on/off battery heater

charge_req = machine.Pin(6,Pin.IN, Pin.PULL_DOWN)
discharge_req = machine.Pin(7,Pin.IN, Pin.PULL_DOWN)

# set all switches to low, Idle operation (no Error-05)
charging_switch.low()
discharging_switch.low()
heater.low()


# Define variables
max_DOD = 10 # placeholder value!
mode  = 0 # NS-04

# varaibles for anomoly detection
max_temp =30 # placeholder value!
min_temp = 10 # placeholder value!
no_current_threshold = 0.001 # Amp
max_charging_current = 4 # placeholder value!
min_charging_current = 0.01# placeholder value!
max_discharging_current = 4 # placeholder value!
min_discharging_current = 0.01# placeholder value!



# interrupt service routine defenitions

def charge_request_toggle(pin):
    print("triggerd1")
    
    if instructions[1] == 0:
        instructions[1] = 1
        instructions[2] = 0 # extra sure the discharging request is removed.
    elif instructions[1] == 1:
         instructions[1] = 0
         instructions[2] = 0
    print(instructions)
    
def discharge_request_toggle(pin):
    print("triggerd2")
    
    if instructions[2] == 0:
        instructions[2] = 1
        instructions[1] = 0 # extra sure the charging request is removed.
    elif instructions[2] == 1:
         instructions[2] = 0
         instructions[1] = 0
         print(instructions)
    


charge_req.irq(handler = charge_request_toggle , trigger = Pin.IRQ_RISING)
discharge_req.irq(handler = discharge_request_toggle , trigger = Pin.IRQ_RISING)


# Do system check,  TBD... -> shifted towards idle mode, exact same things would be observed
   
    
# get battery cap estimate through short discharge
print(instructions)
print("calibration_ongoing")
charging_switch.low() # making sure the charging circuit is disconnected
discharging_switch.high() # discharging circuit connected to the battery
telemetry_frame = telemetry(ADC1,current1,current2)
capacity =int( transfer(telemetry_frame))

discharging_switch.low() # discharging circuit disconnected to the battery
print("calibration_complete")

instructions[1] = 0
instructions[2] = 0

########################## MAIN LOOP ################################################
running = True

while running:
    if mode == 0: # Idle/Recovery mode
        print(instructions)
        
        
        
        if instructions[0] == 0: # system is not instructed to recover
            # Idle section
            
            ## assemble telemetry frame
            telemetry_frame = telemetry(ADC1,current1,current2)
            
            # Id-01 ## Check for anomalies ->compare telemetry frame against normal one
            
            #first check is temperature
            
            if telemetry_frame[0] >= max_temp or telemetry_frame[1] >= max_temp or telemetry_frame[0] <= min_temp or telemetry_frame[1] <= min_temp:
                instructions[0] = 1
                print("anomaly detected, temp out of range")
                print(instructions)
                running = False
            
            #check both current sensors read 0
            
            if  telemetry_frame[2] < -1*no_current_threshold or telemetry_frame[2] > no_current_threshold or telemetry_frame[3] < -1*no_current_threshold or telemetry_frame[3] > no_current_threshold:
                instructions[0] = 1
                print("anomaly detected")
                running = False
                
            # check the open circuit voltage?
            
            
            capacity = capacity  # Id-03    # (take last known value of the capacity)
            
        
            if instructions[1] == 1:
                    if capacity != 100: # switch condition F of FSM and NCh-04
                
                        mode = 1
                        print("battery put intp charing mode")
                        running = False
                    else:
                        print("battery is already fully charged")
                        instructions[1] = 0
                        
                
            elif instructions[2] == 1:
                if capacity > max_DOD:
                    mode = 2 #NDiCh-04
                    print("battery put into discharge mode")
                    running = False
                else:
                    print("Max DOD reached, please charge battery first")
                    instructions[2] = 0
                    # go automatically to charging? mode =1? 
            
            print("System is Idle") #Id-04
            print("Battery capapacity is:",capacity,"%") #Id-04
            
            
            # repeat taken care of by main loop Id-05
    
        
        
        # ------ end of idle section----------

print("while loop ended")
        
charging_switch.low()
discharging_switch.low()
heater.low()

