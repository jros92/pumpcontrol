#!/usr/bin/python
# Use Python 2 !

from gpiozero import LED
from gpiozero import Button
from time import sleep

# Parameters
threshold = 30	# minimum level for pump operation, in per cent
sleep_time = 5	# frequency to check level, in seconds

# Pins
seedVoltagePinNo = 26
lvlPinNoArray0to100 = [4, 17, 27, 22, 23, 24, 25, 5, 6, 13]
pumpPinNo = 16
statusLedPin = 21

# read GPIO pins starting with 100%, break at first HIGH and return its corresponding level [0-1]
def readTankLevel():
	lvlPinNoArray = list(reversed(lvlPinNoArray0to100))
	seedVoltage = LED(seedVoltagePinNo)
	seedVoltage.on()
	for x in range(11):
		if x == 10: break		
		print "Checking pin no.", x, ": GPIO" , lvlPinNoArray[x];
		lvlPin = Button(lvlPinNoArray[x], pull_up=False)
		if lvlPin.is_pressed:
			break
	result = (10.0 - x)/10.0
	print "Detected tank level is ", result*100, "%";
	seedVoltage.off()
	return result


print "Starting...";

pump = LED(pumpPinNo)
statusLed = LED(statusLedPin)

while True:
	level = readTankLevel()
	print "Level =", level*100, "%";
	# TODO: Store level in Log
	
	# Check level and turn off pump if necessary
	if level*100 < threshold:
		pump.off()
	else:
		pump.on()
		
	statusLed.blink()
	sleep(sleep_time)

print "Done.";