'''
Main program of Smart battery system as issued by AE4S15
Date: 19-04-2022
Author: Mees Beumer 4648838

'''
######################## INITIALISATION ##################################################
import sys
import time
import machine
import MCP_3008
from SPI import ADC
from I2C_practice import INA219
from telemetry_frame_test import telemetry
from UART_frame_transfer_Pico import transfer


# Define telemetry frames

instructions = [0,0,0,0.0] # [Recovery (Y/N), Charging (Y/N), Discharging(Y/N), Capacity (float)]
error_log = [0,0,0,0,0,0,0,0,0,0] # all integer numbers to keep track of errors. Ordered acording to error code [E-01,E-02,......,E-10]


# establish GPIO pinout

ADC1 = ADC(0) # SPI pins for ADC1
ADC2 = ADC(1) # SPI pins for ADC2 <--------------------------------------------------- NOTE: problems might arise due to the again defined SPI bus

I_sensor_1 = INA219(0)  # I2C pins for current sensor 
I_sensor_2 = INA219(1)  # I2C pins for current sensor <--------------------------------------------------- NOTE: problems might arise due to the again defined I2C bus

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
max_DOD = 80 # placeholder value!
mode  = 0 # NS-04

# varaibles for anomoly detection
max_temp =30 # placeholder value!
min_temp = 10 # placeholder value!
no_current_threshold = 0.001 # Amp
max_charging_current = 4 # placeholder value!
min_charging_current = 3# placeholder value!
max_discharging_current = 4 # placeholder value!
min_discharging_current = 3# placeholder value!



# interrupt service routine defenitions

def charge_request_toggle(instructions):
    
    if instructions[1] == 0:
        instructions[1] = 1
        instructions[2] = 0 # extra sure the discharging request is removed.
    elif instructions[1] == 1:
         instructions[1] = 0
        instructions[2] = 0
    
    return instructions
    
def discharge_request_toggle(instructions):
    
    if instructions[2] == 0:
        instructions[2] = 1
        instructions[1] = 0 # extra sure the charging request is removed.
    elif instructions[2] == 1:
         instructions[2] = 0
        instructions[1] = 0
    
    return instructions
    
    



charge_req.irq(handler = charge_request_toggle , trigger = Pin.IRQ_RISING)
discharge_req.irq(handler = discharge_request_toggle , trigger = Pin.IRQ_RISING)


# Do system check,  TBD... -> shifted towards idle mode, exact same things would be observed
   
    
# get battery cap estimate through short discharge

charging_switch.low() # making sure the charging circuit is disconnected
discharging_switch.high() # discharging circuit connected to the battery
telemetry_frame = telemetry(ADC1)
capacity = transfer(telemtry_frame)
discharging_switch.low() # discharging circuit disconnected to the battery



########################## MAIN LOOP ################################################
running = True

while running:
    if mode == 0: # Idle/Recovery mode
        
        
        
        if instruction[0] == 0: # system is not instructed to recover
            # Idle section
            
            ## assemble telemetry frame
            telemetry_frame = telemetry(ADC1)
            
            # Id-01 ## Check for anomalies ->compare telemetry frame against normal one
            
            #first check is temperature
            
            if telemetry_frame[0] >= max_temp or telemetry_frame[1] >= max_temp or telemetry_frame[0] <= min_temp or telemetry_frame[1] <= min_temp:
                instructions[0] = 1
            
            #check both current sensors read 0
            
            if  telemetry_frame[2] < -1*no_current_threshold or telemetry_frame[2] > no_current_threshold or telemetry_frame[3] < -1*no_current_threshold or telemetry_frame[3] > no_current_threshold:
                instructions[0] = 1
            
            # check the open circuit voltage?
            
            
            capacity = capacity  # Id-03    # (take last known value of the capacity)
            
        
            if instructions[1] == 1:
                    if capacity != 100: # switch condition F of FSM and NCh-04
                
                        mode = 1
                    else:
                        print("battery is already fully charged")
                        
                
            elif instructions[2] == 1:
                if capacity > max_DOD:
                    mode = 2 #NDiCh-04
                else:
                    print("Max DOD reached, please charge battery first")
                    # go automatically to charging? mode =1? 
            
            print("System is Idle") #Id-04
            print("Battery capapacity is:",capacity,"%") #Id-04
            
            ##delay?
            
            # repeat taken care of by main loop Id-05
    
        
        
        # ------ end of idle section----------
        
        
        
        # Recovery section
        else: #Re-01
            if error_log[1] == 0: #E-02-02
            
                readout_1 =  telemetry(ADC1)  #Re-02
                readout_2 =  telemetry(ADC2)  #Re-02
                
                # check if frames produce the same numbers
                for i in range (len(readout_1)):
                    total += abs(readout_1[i]-readout_2[i])
                
                if total >= 1.5: # TBC value
                    # ADC1 is considered broken -> E-02
                    
                    print("ADC1 produces faulty numbers, system reconfigured to ADC2") #E-02-01
                    
                    # Reconfigure to use ADC2 only
                    
                    error_log[1] = 1
                    
                else: #Re-03
                    if readout_1[0] >= max_temp  or readout_1[1] >= max_temp:  #either temperature sensors is too hihg enter error code E-04
                        print("E-04: Battery is too hot to operate safely")
                        error_log[3] += 1
                        
                        
                        #Decision to make, do we want to keep the code here? or do we want it to fully loop on itself?
                        cooling = True
                        while cooling:
                            print("current temperature: ",readout_1[0], " deg")
                            utime.sleep(1)
                            if readout_1[0] < max_temp:
                                cooling= False
                        
                        print("Recovery succesfull")
                        instruction[0] = 0        
                   
                    if readout_1[0] <= min_temp  or readout_1[1] <= min_temp:  #either temperature sensors is too low enter error code E-05
                       print("E-05: Battery is too cold to operate safely")
                        error_log[4] += 1
                        
                        
                        #Decision to make, do we want to keep the code here? or do we want it to fully loop on itself?
                        heating = True
                        heater.high()
                        print("Heating switched ON")
                        while heating:
                            print("Current temperature: ", readout_1[0], " deg")
                            utime.sleep(1)
                            if readout_1[0] > min_temp:
                                heating = False
                                heater.low()
                                
                        print("Recovery succesfull")
                        instructions[0] = 0  
                       
                    # no more voltage regulator sensed. do we include error code E-01?
               
               else:
                   mode = 3
           
           
      
        
        
        
        # ------ end of recovery section
        
        
        
        
        
        
    elif mode ==1:       # Charging mode
        
        #connect charging if it was not connected
        if instructions[1] == 0: # connect charging circuit in case it was not connected. 
            discharging_switch.low() # making sure the discharging circuit is disconnected
            charging_switch.high() # charging circuit connected to the battery
            instructions[1] =1 #NCh-05
        #now the charging circuit is connected
        
        ##NCh-06 assemble telemetry frame 
        telemetry_frame = telemetry(ADC1)
        
        
        
            
        #NCh-07 check for anomalies 

        #first check is temperature
        if telemetry_frame[0] >= max_temp or telemetry_frame[1] >= max_temp or telemetry_frame[0] <= min_temp or telemetry_frame[1] <= min_temp:
            instructions[0] = 1
            
        #check discharge current sensor read 0
        if  telemetry_frame[3] < -1*no_current_threshold or telemetry_frame[3] > no_current_threshold:
            instructions[0] = 1
    
        #check charge current sensor reads within okay range
        if telemetry_frame[2] < min_charing_current or telemetry_frame[2]> max_charging_current:
            instructions[0] = 1
            
    

        
        ## NCh-08 estimate battery capacity (Function)
        capacity = transfer(telemetry_frame) # placeholder value
            
        ## NCh-09 check interrupt request -> covered in ISR
            
        
        #-------- exit conditions -------- NCh-10
        
        # battery is fully charged
        if capcity => 100: #NCh-12
            charging_switch.low() # NCh-11
            instructions[1] = 0 #NCh-11
            print("Battery has reached its maximum capacity") #NCh-13
            mode = 0
        
        
        # charging is interupted
        if instructions[1] == 0:
            charging_switch.low() # ICh-01
            #instructions[1] = 0 #ICh-01 covered in the ISR
            print("Battery charging was interrupted")
            
            mode = 0 # ICh-02
        
            print("Succesfull interuption, Current capacity:", capacity,"%")
        
        
        # anomaly detected
        if instructions[0] == 1:
            charging_switch.low() # ACh-01
            print("Anomaly detected, charging is paused") #ACh-04
            mode = 0 #ACH-03
        
        else:
            print("battery capacity: ",capacity, "%")
            
            #delay???
            
        
        
        #---- end of charging mode -----
        
        
        
        
    elif mode ==2:       # Discharging mode
        
        if instructions[2] == 0: # connect charging circuit in case it was not connected. 
            charging_switch.low() # making sure the charging circuit is disconnected
            discharging_switch.high() # discharging circuit connected to the battery
            instructions[2] =1 #NDiCh-05
        
        ##NDiCh-06 assemble telemetry frame
        telemetry_frame = telemetry(ADC1)
        
        
        ##NDiCh-07 check for anomalies
        
        #first check is temperature
        if telemetry_frame[0] >= max_temp or telemetry_frame[1] >= max_temp or telemetry_frame[0] <= min_temp or telemetry_frame[1] <= min_temp:
            instructions[0] = 1
            
        #check charge current sensor read 0
        if  telemetry_frame[2] < -1*no_current_threshold or telemetry_frame[2] > no_current_threshold:
            instructions[0] = 1
    
        #check discharge current sensor reads within okay range
        if telemetry_frame[3] < min_discharing_current or telemetry_frame[3]> max_discharging_current:
            instructions[0] = 1
        
        
        
        ## NDiCh-08 estimate battery capacity (Function)
        capacity = transfer(telemetry_frame) # placeholder value
            
        ## NDiCh-09 check interrupt request -> covered in ISR
        
        
        #-------- Exit conditions ---------#NDiCh-10
        
        # max DOD reached
        if capacity <= max_DOD:
            discharging_switch.low() #NDiCh-11
            instruction[2] = 0 #NDiCh-11
            print("Battery has reached its maximum depth of discharge") #NDiCh-13
            mode = 0 #NDiCh-12
            
        # discharging interrupted
        if instructions[2] ==0:
            discharging_switch.low() # IDiCh-01
            #instructions[2] = 0 #IDiCh-01 -> covered by ISR
            print("Battery charging was interrupted")
            
            mode = 0 # IDiCh-02
        
            print("Succesfull interuption, Current capacity:", capacity,"%")
        
        # anomaly detected
        if instructions[0] == 1:
            discharging_switch.low() # ADiCh-01
            print("Anomaly detected, discharging is paused") #ADiCh-04
            mode = 0 #ADiCh-03
        
      
        else:
            print("battery capacity: ",capacity, "%")
            
            #delay???
        
        
        #---- end of discharging mode -----
        
        
        
        
        
        
    elif mode ==3:       # shut down mode
        
        running = False # UF-03
        # add fault instruction in error log #UF-01
        print ("Unrecoverable Failure occured. System safely shut down") # UF-02
        