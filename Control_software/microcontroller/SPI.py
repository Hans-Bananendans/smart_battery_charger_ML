import machine

class ADC:
    
    def __init__(self, index):
        
        global spi
        spi = machine.SPI(0, # bus id on pinout
                      baudrate= 2000, #1000, #clock frequency of 1KHz
                      polarity=0,    # level the idle clock sits in (low for MCP3008)
                      phase=1, #select faling edges of clock signal
                      bits=8,
                      firstbit=machine.SPI.MSB, #wich bit comes first, what is the order of the bits (MSB = largest number first)
                      sck=machine.Pin(18),
                      mosi=machine.Pin(19),
                      miso=machine.Pin(16)) #note that it uses GPIO pin numbers
        
        if index ==0:
            self.cs=machine.Pin(17,machine.Pin.OUT)
        if index ==1:
            self.cs=machine.Pin(5,machine.Pin.OUT)
        else:
            pass
        
        self.cs.value(1)
        
    def read(self,channel):
        
        if channel < 0 or channel >7:
            return -1
        else:
            self.output_buffer = bytearray(3)              # buffer to collect MCP3008 inputs into
            self.input_buffer =bytearray(3)                 # buffer to collect MCP3008 outputs into
            self.output_buffer[0] = 0x01                     #starting bit inserted
            self.output_buffer[1] = (8+channel)<<4   # add readout instructions to the MCP3008 input buffer
            
            #print(self.output_buffer)
            
            self.cs.value(0)
            spi.write_readinto(self.output_buffer,self.input_buffer)        # write the MCP3008 Input buffer AND record the reply into the MCP3008 Output buffer
            self.cs.value(1)
        
            value = (((self.input_buffer[1]&3)<<8)+self.input_buffer[2])/1024 # convert output buffer into a value
        
        
            return value
        
        
    def read_diff(self,channel_index, is_differential= True):
    
        if channel_index < 0 or channel_index >3:
            return -1
        else:
            self.output_buffer = bytearray(3)              # buffer to collect MCP3008 inputs into
            self.input_buffer =bytearray(3)                 # buffer to collect MCP3008 outputs into
            
            self.output_buffer[0] = 0x01                     #starting bit inserted
                      
            self.output_buffer[1] = int(channel_index<<5)   # add readout instructions to the MCP3008 input buffer
            
            #print(self.output_buffer[0])
            #print(self.output_buffer[1])
            
            self.cs.value(0)
            spi.write_readinto(self.output_buffer,self.input_buffer)        # write the MCP3008 Input buffer AND record the reply into the MCP3008 Output buffer
            self.cs.value(1)
            
            #print(self.input_buffer[0])
            #print(self.input_buffer[1]&3)
            #print(self.input_buffer[2])
            
            voltage = ((((self.input_buffer[1]&3)<<8)+self.input_buffer[2])/1024)*5 # convert output buffer into a value
            
            return voltage

    def readout_all(self):
        # function to read out all channels of the MCP3008 ADC
        
        sensor_values = []
        for channel in range(8):
            sensor_values.append(ADC.read(self,channel))
        return sensor_values
