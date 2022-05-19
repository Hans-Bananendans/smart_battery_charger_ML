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

ADC = ADC1 #default ADC 

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

instructions[0] = 1
instructions[1] = 0
instructions[2] = 0

mode = 0

########################## MAIN LOOP ################################################
running = True
recovering_counter =0
checked = False

while running:
    print(instructions)
    
    if mode == 0: # Idle/Recovery mode
        if instructions[0] == 0:
            print("system = healthy")
            running = False
            
            # Recovery section
        else: #Re-01
            if error_log[1] == 0 and checked == False : #E-02-02
            
                readout_1 =  telemetry(ADC1,current1,current2)  #Re-02
                readout_2 =  telemetry(ADC2,current1,current2)  #Re-02
                
                total = 0
                # check if frames produce the same numbers
                for i in range (len(readout_1)):
                    total += abs(readout_1[i]-readout_2[i])
                
                if total >= 1.0: # TBC value
                    
                    print("triggerd")
                    # ADC1 is considered broken -> E-02
                    
                    print("ADC1 produces faulty numbers, system reconfigured to ADC2") #E-02-01
                    
                    # Reconfigure to use ADC2 only
                    ADC = ADC2
                    print('ADC2 now operational')
                    
                    error_log[1] = 1
                    #print(error_log)
                    checked = True
                else:
                    checked = True
                    print("ADC is not the problem")
                    
            #print("other recovery procedures")
            readout_1 =  telemetry(ADC1,current1,current2)  #Re-02
            #print(readout_1)
            
            if readout_1[0] >= max_temp  or readout_1[1] >= max_temp:  #either temperature sensors is too hihg enter error code E-04
                print("E-04: Battery is too hot to operate safely")
                error_log[3] += 1
                
                
                #Decision to make, do we want to keep the code here? or do we want it to fully loop on itself?
                cooling = True
                while cooling:
                    readout_1 = telemetry(ADC,current1,current2)
                    print("current temperature: ",readout_1[0], " deg")
                    utime.sleep(0.5)
                    if readout_1[0] < max_temp:
                        cooling= False
                
                print("Recovery succesfull")
                instructions[0] = 0        
           
            elif readout_1[0] <= min_temp  or readout_1[1] <= min_temp:  #either temperature sensors is too low enter error code E-05
                print("E-05: Battery is too cold to operate safely")
                error_log[4] += 1
                
                
                #Decision to make, do we want to keep the code here? or do we want it to fully loop on itself?
                heating = True
                heater.high()
                print("Heating switched ON")
                while heating:
                    readout_1 = telemetry(ADC1,current1,current2)
                    #print(readout_1)
                    print("Current temperature: ", readout_1[1], " deg")
                    utime.sleep(0.5)
                    if readout_1[1] > min_temp:
                        heating = False
                        heater.low()
                        
                print("Recovery succesfull")
                instructions[0] = 0  
               
                    # no more voltage regulator sensed. do we include error code E-01?
            else:
                print("recovering")
                #print(recovering_counter)
                recovering_counter += 1
                if recovering_counter>=10:
                    mode = 3
    else:
        running = False
            

      
        
        
        
        # ------ end of recovery section
print("while loop ended")
print(mode)
        
charging_switch.low()
discharging_switch.low()
heater.low()