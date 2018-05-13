#!/usr/bin/python
# Use Python 3 !

from gpiozero import LED
from time import sleep

print "Starting...";

ledR = LED(20)
ledG = LED(21)

print "Init complete";
sleep(3)


ledG.on()
sleep(1)
ledG.off()
sleep(1)
ledR.on()
sleep(1)
ledR.off()
sleep(1)

print "Done.";