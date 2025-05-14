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

# Requirements: 
#  pip install RPi.GPIO
import RPi.GPIO as GPIO
import time
import sys
import subprocess
import traceback

#--------------------------------------------------------------------------------
# Configuration
#--------------------------------------------------------------------------------

# 1. Temperature and fan speed steps Tables
tempSteps =  [ 35, 40, 50, 60 ]    # [°C]
speedSteps = [ 0,  40, 85, 100]    # [%]


# 2. Constants dependant on Hardware setting
FAN_PIN           = 24   # BCM pin used to drive transistor's base
WAIT_TIME         = 3    # [s] Time to wait between each refresh
PWM_FREQ          = 275  # [Hz] Change this value if fan has strange behavior
FAN_HYST          = 1    # [%] Fan speed will change only of the difference of PWM Cycle is higher than hysteresis
FAN_MIN           = 15   # [%] Minimum Fan PWM 
TEMP_FILTER_RATIO = 0.7  # [% / 100] Filtering value between 0 and 1, the higher this value is, the less history is used for new Temp computation. 
FAN_START         = 50   # [%] FAN PWM at initialization
FAN_KICK_MAX      = 25   # [%] Maximal Fan PWM that will get KICK. minimal PWM is defined by FAN_MIN
FAN_KICK_TIME     = 0.1  # [s] Time of boost in low speeds. This is to kick the fan a little bit.
#--------------------------------------------------------------------------------

#--------------------------------------------------------------------------------
# excepthook
#--------------------------------------------------------------------------------
# We need to dismount the GPIO kindly, in case of any exception
def excepthook(etype,value,tb):
    message = ''.join(traceback.format_exception(etype, value, tb))
    if etype == KeyboardInterrupt:
        print("Fan CONTROL interrupted by keyboard")
    else:
        print (message)    
    GPIO.cleanup()
    sys.exit(1)

sys.excepthook = excepthook

#--------------------------------------------------------------------------------
# FanCtrl
#--------------------------------------------------------------------------------
class FanCtrl:
    def __init__(self):
        self.cpuTempOld = self.readSystemTemp()

        # We must set a speed value for each temperature step
        if(len(speedSteps) != len(tempSteps)):
            print("Temp steps table has different size than speed steps table (%d vs %d)" % (len(speedSteps), len(tempSteps)))
            sys.exit(0)

        # Setup GPIO pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(FAN_PIN, GPIO.OUT, initial=GPIO.LOW)
        
        self.fan = GPIO.PWM(FAN_PIN, PWM_FREQ)


    def readSystemTemp(self):
        # Read CPU temperature
        x = subprocess.check_output(["vcgencmd","measure_temp"])
        x = str(x)
        raw_text = x.split('=')[1].strip().replace("'C",'').replace('\\n"','')
        cpuTempFloat = float(raw_text)
        return cpuTempFloat
    
    
    @staticmethod
    def filtered(old, new):
        return ((1.0 - TEMP_FILTER_RATIO) * float(old)) + (TEMP_FILTER_RATIO * float(new))


    def getCpuTemp(self):
        cpuTempNew = self.readSystemTemp()
        cpuTemp = round(self.filtered(self.cpuTempOld, cpuTempNew) ,1 ) # avoid resonance, so the cpuTemp is filtered value
        # Remeber the Cpu Temp
        self.cpuTempOld = cpuTemp
        print ('cpuTemp Old = %1.1f' % self.cpuTempOld)
        print ('cpuTemp = %1.1f' % cpuTemp)
        return cpuTemp
        

    def loop(self):
        fanSpeedOld = FAN_START
        fanSpeed    = FAN_START
        self.fan.start(FAN_START)
        
        while (1):
            print ('========')
            cpuTemp = self.getCpuTemp()

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
                if fanSpeed < FAN_MIN:
                    print ('Requested Duty Cycle too low. Dropped from %d to 0%%' % fanSpeed)
                    fanSpeed = 0
                if fanSpeed > FAN_MIN and fanSpeed < FAN_KICK_MAX:
                    self.fan.ChangeDutyCycle(100)
                    time.sleep(FAN_KICK_TIME)
                    print ('Duty Cycle boosted 100%% for %f sec' % FAN_KICK_TIME)
                self.fan.ChangeDutyCycle(fanSpeed)
                print ('Changed Duty Cycle to %d %%' % fanSpeed)
                fanSpeedOld = fanSpeed                
        
            # Wait until next refresh
            time.sleep(WAIT_TIME)    
        
    def test(self):
        print ('TESTING' )
        self.fan.start(0)
        time.sleep(1)
        counter = 9997
        while 1:        
            duty = (counter % 21 * 5) 
            duty = min(100, duty)
            duty = max(0, duty)

            self.fan.ChangeDutyCycle(duty)
            
            print ('Changed Duty Cycle to %d %%' % (duty) )
            time.sleep(3)
            counter -= 1   


if __name__ == '__main__':
    fctr = FanCtrl()
    
    if '-TEST' in sys.argv:
        fctr.test()
    fctr.loop()
