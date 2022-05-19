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

def telemetry(ADC,current1,current2):
    start = utime.ticks_ms()
    telemetry = []
    vref=5
    temp_offset = 0#.5 #def C        
    
    #temperature readout:
    for j in range(2):
        total =0
        
        for i in range(10):
            total += ADC.read(j)*vref *100-50
            utime.sleep(0.0001)
        
        
        telemetry.append(total/i - temp_offset)
        
    # current readout before battery
    telemetry.append(current1.vshunt())
    
    # current readout after battery
    telemetry.append(current2.vshunt())
    
    # open voltage
    for k in range(3):
        total = 0
        for i in range(10):
            total+=(ADC.read_diff(k+1))
            utime.sleep(0.0001)
        telemetry.append(total/i)
    end = utime.ticks_ms()
    #print(utime.ticks_diff(end, start)/1000)
    
    return telemetry





#print(telemetry(ADC1,current1,current2))
#print(telemetry(ADC2,current1,current2))



