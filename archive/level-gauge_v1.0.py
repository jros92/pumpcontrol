#!/usr/bin/python
# Use Python 2 !

# Credit goes to Matt Hawkins from raspberrypi-spy.co.uk
# Thanks for the awesome tutorial on IoT using the RPi and ThingSpeak.
# I reused his sendData() method to send data to Thingspeak

import os
import sys
import urllib            # URL functions
import urllib2           # URL functions

import time
from time import sleep

from gpiozero import LED
from gpiozero import Button

# Parameters
threshold = 30	# minimum level for pump operation, in per cent
sleep_time = 30	# frequency to check level, in seconds

THINGSPEAKKEY = 'C9Z5GCAFI42KFAQK'
THINGSPEAKURL = 'https://api.thingspeak.com/update'

# Pins
seedVoltagePinNo = 26
lvlPinNoArray0to100 = [4, 17, 27, 22, 23, 24, 25, 5, 6, 13]
pumpPinNo = 16
statusLedPin = 21

# Get Timestamp
def getTimestamp():
	return time.strftime("%Y-%m-%d %H:%M:%S :")

# read GPIO pins starting with 100%, break at first HIGH and return its corresponding level [0-1]
def readTankLevel():
	lvlPinNoArray = list(reversed(lvlPinNoArray0to100))
	seedVoltage = LED(seedVoltagePinNo)
	seedVoltage.on()
	for x in range(11):
		if x == 10: break		
		#print "Checking pin no.", x, ": GPIO" , lvlPinNoArray[x];
		lvlPin = Button(lvlPinNoArray[x], pull_up=False)
		if lvlPin.is_pressed:
			break
	result = (10.0 - x)/10.0
	print "Detected tank level is ", result*100, "%";
	seedVoltage.off()
	return result

def sendData(url,key,field1,field2,level,pump_state):
  """
  Send event to internet site
  """

  values = {'api_key' : key, 'field1' : level, 'field2' : pump_state}

  postdata = urllib.urlencode(values)
  req = urllib2.Request(url, postdata)

  log = time.strftime("%d-%m-%Y,%H:%M:%S") + ","
  log = log + "{:.1f}".format(level) + ","
  log = log + "{:.2f}".format(pump_state) + ","

  try:
    # Send data to Thingspeak
    response = urllib2.urlopen(req, None, 5)
    html_string = response.read()
    response.close()
    log = log + 'Update ' + html_string

  except urllib2.HTTPError, e:
    log = log + 'Server could not fulfill the request. Error code: ' + e.code
  except urllib2.URLError, e:
    log = log + 'Failed to reach server. Reason: ' + e.reason
  except:
    log = log + 'Unknown error'

  print log


print getTimestamp(), "Starting...";

pump = LED(pumpPinNo)
statusLed = LED(statusLedPin)

# Main Loop
while True:
	level = readTankLevel()
	print getTimestamp(), "Level =", level*100, "%";
	# TODO: Store level in Log
	
	# Check level and turn off pump if necessary
	if level*100 < threshold:
		pump.off()
	else:
		pump.on()
	
	sendData(THINGSPEAKURL,THINGSPEAKKEY,'field1','field2',level,0)
	sys.stdout.flush()
	
	statusLed.blink()
	sleep(sleep_time)

# Terminate Program
print getTimestamp(), "Done.";