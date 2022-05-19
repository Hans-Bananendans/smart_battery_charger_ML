import serial

ser = serial.Serial()

ser.port = 'COM7'
ser.baudrate = 115200
ser.open()


length1 = 2
header_received =0

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
            print(frame)
            ser.write(bytes("frame received","ascii"))
            header_received = 0
