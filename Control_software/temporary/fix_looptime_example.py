from utime import sleep_ms, ticks_ms

# Each loop will have AT LEAST this length:
LOOP_TIME = 2000 # [ms]
LIMIT_LOOP = True # In the code, you can inhibit the loop limitation by setting this to False


def some_function(duration, ms=True, verbose=True):
    if ms: # Unit is [ms]
        sleep_ms(duration)
    else: #Assume unit is [s]
        sleep(1000*duration)
        
    if verbose:
        print("some_function ran for {} ms".format(duration))



while True:
    # Record time in [ms] at start of loop
    t0 = ticks_ms() # [ms]
    
    
    
    # ==== YOUR CODE HERE ====
    
    # Run some function:
    some_function(600) # Runs for 600 ms
    
    # ========================
    
    
    
    # Calculate loop time and sleep if needed:
    tloop = ticks_ms() - t0
    if tloop < LOOP_TIME and LIMIT_LOOP:
        sleep_ms(LOOP_TIME-tloop)
    
    # print("Loop ended, lasting for {} ms".format(ticks_ms()-t0))
