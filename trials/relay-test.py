#!/usr/bin/python
# Use Python 3 !

from gpiozero import LED
from time import sleep

print "Starting...";

pump = LED(20)
pump.on()
ledG = LED(21)

print "Init complete";
sleep(3)

while True:
	ledG.blink()
		
	pump.off()
	print "Pump turned on.";
	sleep(3)
	pump.on()
	print "Pump turned off.";
	sleep(5)

print "Done.";