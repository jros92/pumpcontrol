#!/usr/bin/python
# Use Python 3 !

from gpiozero import LED
from gpiozero import Button
from time import sleep

seedVoltagePinNo = 26
lvlPinNoArray = [4, 17, 27, 22, 10, 9, 11, 5, 6, 13]

def readTankLevel():
	seedVoltage = LED(seedVoltagePinNo)
	seedVoltage.on()
	for x in range(0,10):
		if x == 10: break
		lvlPin = Button(lvlPinNoArray[x], pull_up=False)
		if lvlPin.is_pressed:
			break
	if x == 10: result = 0
	else: result = (x+1.0)/10.0
	print "Detected tank level is ", result*100, "%";
	seedVoltage.off()
	return result


print "Starting...";


button = Button(16, pull_up=False)
button.wait_for_press()
print("The button was pressed!")

level = readTankLevel()
print "Level = ", level;



# Now start blinking...
ledR = LED(20)
ledG = LED(21)

ledR.blink()

for x in range(0,3):
	ledG.blink()
	sleep(1)

while True:
	ledG.on()
	sleep(1)
	ledG.off()
	sleep(1)
	ledR.on()
	sleep(1)
	ledR.off()
	sleep(1)

print "Done.";