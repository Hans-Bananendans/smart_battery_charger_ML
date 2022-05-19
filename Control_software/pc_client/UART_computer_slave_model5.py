import serial
from Dec_converter import ASCII
import time
import sys
from statistics import mean
import numpy as np
from tensorflow.keras.models import load_model
from EstimationFunction import estimateCapacity
import os

#Load capacity estimation model

dischargemodel = load_model(os.path.join(os.getcwd(),'Discharging Model'))
chargemodel_CC = load_model(os.path.join(os.getcwd(), 'Charging Voltage Model'))

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


threshold = 0.01 #A

ser = serial.Serial()

ser.port = 'COM7'
ser.baudrate = 115200
ser.open()




length1 = 2
header_received =0
nominal_capacity = 3.35 #Ah #TBC

counter = 0 
while True:
    if header_received == 0: 
        waiting = True
        timing=0
        while waiting:
            
            # timeout 
            timing += 1
            if timing > 10000000:
                waiting = False
                print("Pico offline")
            
            
            # see if the header is received
            if ser.in_waiting == length1:
                frame_length = ser.read(length1)
                #print("Frame will be of length:", frame_length)
                frame_length = int(frame_length)
                ser.write(bytes('Frame length received','ascii'))
                header_received = 1
                waiting = False
            

    # header is received
    if header_received == 1: 
        if ser.in_waiting == frame_length:
            frame = ser.read(frame_length)
            telemetry = ASCII(list(frame))
            print(telemetry)

            temp1 = telemetry[0]
            temp2 = telemetry[1]

            current1 = telemetry[2]
            current2 = telemetry[3]

            voltage1 = telemetry[4]
            voltage2 = telemetry[5]
            voltage3 = telemetry[6]

            temperature = (temp1 + temp2)/2 +273.15 #in Kelvin (taking the average over two sensors)

            voltage = (voltage1 + voltage2 + voltage3)/3 # TMR implementation?

            if current1 >= threshold and current2 <= threshold:
                charging = True
                current = current1
            elif current1<= threshold and current2>= threshold:
                charging = False 
                current = current2
            else:
                current=0
                charging = True
                
            capacity_percentage = estimateCapacity(current,voltage,temperature,nominal_capacity,charging)[1] # nominal capactity TBC!
            
            
            #ser.write(bytes("frame received","ascii"))
            ser.write(bytes(str(capacity_percentage),"ascii"))
            header_received = 0



            
