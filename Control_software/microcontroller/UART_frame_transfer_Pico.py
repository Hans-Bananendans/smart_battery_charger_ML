import machine
from telemetry_frame_test import telemetry

import SPI
import utime
from Desperate_test import ina219
from machine import I2C, Pin


ADC1=SPI.ADC(0)
ADC2=SPI.ADC(1)

ina_i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=100000) 
current1 = ina219(0.1,68,5)
current2 = ina219(0.1,64,5)

current1.configure()
current2.configure()

uart = machine.UART(0,115200, tx = Pin(0),rx=Pin(1))


def transfer(data):
    verbose1 = 0
    

    # send frame  length

    uart.write(bytes(str(len(str(data))),'ascii'))

    # wait for acknowkledgement
    waiting = True
    timing =0
    while waiting:
        if timing > 100000:
            waiting = False
            print("OBC offline")
        else:
            if uart.any() != 0:
                acknowledge = uart.read()
                #if verbose1 ==1:
                    #print(acknowledge)
                ack = 1
                waiting = False
                

    if ack == 1:
        # send telemetry frame
        uart.write(bytes(str(data),'ascii'))
        #if verbose1 ==1:
            #print("Frame sent")
        
        
        # wait for acknowledgement
        waiting = True
        timing = 0
        while waiting:
            if timing > 100000:
                print("OBC is unresponsive")
                waiting = False
            
            if uart.any() !=0:
                capacity= uart.read()
                #if verbose1 == 1: 
                    #print(capacity)
                    #print("transfer succesfull")
                waiting = False
                ack = 0
    
    return capacity
            



