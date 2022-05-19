def ASCII(frame):
    frame = frame[1:-1]
    #for i in range(len(frame)):
    #    total = total + chr(frame[i])
    #print(type(total))

    frame_new=[]
    i = 0
    looking = True
    number =''
    while looking:
        if frame[i] != 44:
            number = number + chr(frame[i])
            i += 1

        elif frame[i] == 44:
            i += 2
            frame_new.append(float(number))
            number = ''

        if i >= len(frame):
            frame_new.append(float(number))
            looking = False

    return frame_new

