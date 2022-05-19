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
'''
print(instructions)

print("calibration_ongoing")
charging_switch.low() # making sure the charging circuit is disconnected
discharging_switch.high() # discharging circuit connected to the battery
telemetry_frame = telemetry(ADC1,current1,current2)
capacity =int( transfer(telemetry_frame))

discharging_switch.low() # discharging circuit disconnected to the battery
print("calibration_complete")
'''
instructions[1] = 0
instructions[2] = 0

mode = 2

########################## MAIN LOOP ################################################
running = True

while running:
    print(instructions)
    if mode ==2:       # Discharging mode
        
        if instructions[2] == 0: # connect charging circuit in case it was not connected. 
            charging_switch.low() # making sure the charging circuit is disconnected
            discharging_switch.high() # discharging circuit connected to the battery
            instructions[2] =1 #NDiCh-05
        
        ##NDiCh-06 assemble telemetry frame
        telemetry_frame = telemetry(ADC1,current1,current2)
        
        
        ##NDiCh-07 check for anomalies
        
        #first check is temperature
        if telemetry_frame[0] >= max_temp or telemetry_frame[1] >= max_temp or telemetry_frame[0] <= min_temp or telemetry_frame[1] <= min_temp:
            instructions[0] = 1
            
        #check charge current sensor read 0
        if  telemetry_frame[2] < -1*no_current_threshold or telemetry_frame[2] > no_current_threshold:
            instructions[0] = 1
    
        #check discharge current sensor reads within okay range
        if telemetry_frame[3] < min_discharging_current or telemetry_frame[3]> max_discharging_current:
            instructions[0] = 1
        
        
        
        ## NDiCh-08 estimate battery capacity (Function)
        capacity = int(transfer(telemetry_frame)) # placeholder value
            
        ## NDiCh-09 check interrupt request -> covered in ISR
        
        
        #-------- Exit conditions ---------#NDiCh-10
        
        # max DOD reached
        if capacity <= max_DOD:
            discharging_switch.low() #NDiCh-11
            instructions[2] = 0 #NDiCh-11
            print("Battery has reached its maximum depth of discharge") #NDiCh-13
            mode = 0 #NDiCh-12
            print("system goes back to Idle")
            
        # discharging interrupted
        elif instructions[2] ==0:
            discharging_switch.low() # IDiCh-01
            #instructions[2] = 0 #IDiCh-01 -> covered by ISR
            print("Battery discharging was interrupted")
            
            mode = 0 # IDiCh-02
        
            print("Succesfull interuption, Current capacity:", capacity,"%")
            print("system goes back to Idle")
        
        # anomaly detected
        elif instructions[0] == 1:
            discharging_switch.low() # ADiCh-01
            print("Anomaly detected, discharging is paused") #ADiCh-04
            mode = 0 #ADiCh-03
            print("system goes back to Idle")
        
      
        else:
            print("battery capacity: ",capacity, "%")
            
            #delay???
    else:
        running = False
        print(mode)
        
        #---- end of discharging mode -----
print("while loop ended")
        
charging_switch.low()
discharging_switch.low()
heater.low()