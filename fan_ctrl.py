###############################################################################
# 
# This program is derived from fan_ctrl.py, which was copied from
# https://www.instructables.com/PWM-Regulated-Fan-Based-on-CPU-Temperature-for-Ras/
#
# Thank you for the hard work, Aerandir14
# 
# This program is free software: you can redistribute it and/or modify it how you like.
# The source did not specify the license, therefore I am not specifying it either.
#
# I have reworked the script to suite my needs:
# - specify initial fan PWM
# - use functions
# - changed logic for processor temp measurement.
#
###############################################################################

import RPi.GPIO as GPIO
import time
import sys
import subprocess

#--------------------------------------------------------------------------------
# Configuration
#--------------------------------------------------------------------------------

# 1. Temperature and fan speed steps Tables
tempSteps =  [ 30, 40, 50, 60 ]    # [°C]
speedSteps = [ 25, 35, 85, 100]    # [%]


# 2. Constants dependant on Hardware setting
FAN_PIN           = 24   # BCM pin used to drive transistor's base
WAIT_TIME         = 3    # [s] Time to wait between each refresh
PWM_FREQ          = 75   # [Hz] Change this value if fan has strange behavior
FAN_HYST          = 1    # [%] Fan speed will change only of the difference of PWM Cycle is higher than hysteresis
TEMP_FILTER_RATIO = 0.7  # [% / 100] Filtering value between 0 and 1, the higher this value is, the less filtering is used for new Temp computation. 
FAN_START         = 50   # [%] FAN PWM at initialization
#--------------------------------------------------------------------------------

class Static: # C like static variable behavior
    attrs = []
    def __getattr__ (self, attr):
        if not attr in self.attrs:
            self.attrs.append(attr)
            setattr(self, attr, 0)
        return self.attr
static = Static()

def filtered(old, new):
    return ((1.0 - TEMP_FILTER_RATIO) * float(old)) + (TEMP_FILTER_RATIO * float(new))

def getCpuTemp():
    # Read CPU temperature

    x = subprocess.check_output(["vcgencmd","measure_temp"])
    raw_text = x.split('=')[1].strip().replace("'C",'')

    cpuTempFloat = float(raw_text)
    cpuTempNew = round(cpuTempFloat, 0)

    cpuTemp = filtered(static.cpuTempOld, cpuTempNew) # avoid resonance, so the cpuTemp is filtered value
    # Remeber the Cpu Temp
    static.cpuTempOld = cpuTemp

    print 'cpuTemp Old = %d' % static.cpuTempOld
    print 'cpuTemp = %d' % cpuTemp

    return cpuTemp

def debug():
    # Setup GPIO pin
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(FAN_PIN, GPIO.OUT, initial=GPIO.LOW)
    fan=GPIO.PWM(FAN_PIN, PWM_FREQ)
    fan.start(0)
    time.sleep(1)
    counter = 0
    while 1:        
        duty = (counter%10 * 10) -5
        duty = min(100, duty)
        duty = max(0, duty)
        duty = 50

        fan.ChangeDutyCycle(duty)
        print 'fan Changed Duty Cycle to %d %%' % (duty)
        time.sleep(4)
        counter += 1   

def main():
    fanSpeedOld = FAN_START
    fanSpeed    = FAN_START

    # Setup GPIO pin
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(FAN_PIN, GPIO.OUT, initial=GPIO.LOW)
    fan=GPIO.PWM(FAN_PIN, PWM_FREQ)
    fan.start(fanSpeed)
    
    # We must set a speed value for each temperature step
    if(len(speedSteps) != len(tempSteps)):
        print("Temp steps table has different size than speed steps table (%d vs %d)" % (len(speedSteps), len(tempSteps)))
        sys.exit(0)
    
    try:
        while (1):
            cpuTemp = getCpuTemp()

            # Below first TEMP threshold value, fan will run at MIN speed.
            if(cpuTemp <= tempSteps[0]):
                fanSpeed = speedSteps[0]
    
            # Above last TEMP threshold value, fan will run at MAX speed
            elif(cpuTemp >= tempSteps[-1]):
                fanSpeed = speedSteps[-1]
    
            # If temperature is between 2 steps in speedSteps table, fan speed is calculated by linear interpolation
            else:       
                for i in range(0, len(tempSteps) - 1 ):
                    if((cpuTemp >= tempSteps[i]) and (cpuTemp < tempSteps[i+1])):
                        fanSpeedFloat = (speedSteps[i+1] - speedSteps[i]) / (tempSteps[i+1] - tempSteps[i]) * (cpuTemp - tempSteps[i]) + speedSteps[i]
                        fanSpeed = round(fanSpeedFloat, 0)
    
            if( abs(fanSpeed - fanSpeedOld) > FAN_HYST ):
                fan.ChangeDutyCycle(fanSpeed)
                print 'fan Changed Duty Cycle to %d %%' % fanSpeed
                fanSpeedOld = fanSpeed                
    
            # Wait until next refresh
            time.sleep(WAIT_TIME)    
    
    # If a keyboard interrupt occurs (ctrl + c), the GPIO is set to 0 and the program exits.
    except(KeyboardInterrupt):
        print("Fan CONTROL interrupted by keyboard")
        GPIO.cleanup()
        sys.exit()

if __name__ == '__main__':
    if '-DEBUG' in sys.argv:
        debug()
    main()
