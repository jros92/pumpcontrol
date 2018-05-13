#!/usr/bin/python
# Use Python 3

# Credit goes to Matt Hawkins from raspberrypi-spy.co.uk
# Thanks for the awesome tutorial on IoT using the RPi and ThingSpeak.
# I reused his sendData() method to send data to Thingspeak

import os
import sys
import urllib  # URL functions
import urllib2  # URL functions

import time
from time import sleep
from datetime import datetime

from gpiozero import LED
from gpiozero import Button

# Parameters
threshold = 30  # minimum level for pump operation, in per cent (Default = 20)
sleep_time = 30  # frequency to check level, in seconds (Default = 30)

THINGSPEAKKEY = 'C9Z5GCAFI42KFAQK'
THINGSPEAKURL = 'https://api.thingspeak.com/update'

log_file_path = 'logs'
log_file_name = 'log'
csv_file_name = 'csv'

# Pins
seedVoltagePinNo = 26
lvlPinNoArray0to100 = [4, 17, 27, 22, 23, 24, 25, 5, 6, 13]
pumpPinNo = 20
statusLedPin = 21


# Get Timestamp
def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")


def print_and_log(message, log_file):
    message_string = "{}: {}\n".format(get_timestamp(), message)
    print(message)
    log_file.write(message_string)


# read GPIO pins starting with 100%, break at first HIGH and return its corresponding level [0-1]
def read_tank_level(log_file):
    lvlPinNoArray = list(reversed(lvlPinNoArray0to100))
    seedVoltage = LED(seedVoltagePinNo)
    seedVoltage.on()
    for x in range(11):
        if x == 10: break
        print_and_log("Checking pin no. {}: GPIO {}".format(x, lvlPinNoArray[x]), log_file)
        lvlPin = Button(lvlPinNoArray[x], pull_up=False)
        if lvlPin.is_pressed:
            break
    result = (10.0 - x) / 10.0
    print_and_log("Detected tank level is {}%".format(result * 100), log_file)
    seedVoltage.off()
    return result


# Turn on pump
def pump_on(pump, log_file):
    pump.off() # Pump is ON when LOW
    print_and_log("Pump turned ON", log_file)


# Turn off pump
def pump_off(pump, log_file):
    pump.on() # Pump is OFF when HIGH
    print_and_log("Pump turned OFF", log_file)


def send_data_to_thingspeak(url, key, field1, field2, level, pump_state, log_file):
    """
  Send event to internet site
  """

    values = {'api_key': key, 'field1': level, 'field2': pump_state}

    postdata = urllib.urlencode(values)
    req = urllib2.Request(url, postdata)

    log = "Successfully sent data,"
    log = log + "{:.1f}".format(level) + ","
    log = log + "{:.2f}".format(pump_state) + ","

    try:
        # Send data to Thingspeak
        response = urllib2.urlopen(req, None, 5)
        html_string = response.read()
        response.close()
        log = log + 'Update ' + html_string
    except urllib2.HTTPError as e:
        log = log + 'Server could not fulfill the request. Error code: ' + e.code
    except urllib2.URLError as e:
        log = log + 'Failed to reach server. Reason: ' + e.reason
    except:
        log = log + 'Unknown error'

    print_and_log(log, log_file)


# Main function
def main():
    now = datetime.now()
    my_path = os.path.abspath(os.path.dirname(__file__))
    log_file_path_abs = os.path.join(my_path, "{}/{}_{}.log".format(log_file_path, log_file_name,
                                                                    now.strftime("%Y-%m-%d_%H-%M-%S")))
    csv_file_path_abs = os.path.join(my_path, "{}/{}_{}.csv".format(log_file_path, csv_file_name,
                                                                    now.strftime("%Y-%m-%d_%H-%M-%S")))
    log_file = open(log_file_path_abs, "w+")
    print_and_log("Starting...", log_file);

    csv_file = open(csv_file_path_abs, "w+")
    csv_file.write("Time;Level;Pump\n")

    pump = LED(pumpPinNo, active_high=False)
    #pump_off(pump, log_file)
    status_led = LED(statusLedPin)

    # Main Loop
    while True:
        try:
            level = read_tank_level(log_file)

            # Turn off pump if necessary
            pumpState = 0
            if level * 100 < threshold:
                #pump_off(pump, log_file)
                pump.off()
                pumpState = 0
            else:
                #pump_on(pump, log_file)
                pump.on()
                pumpState = 1

            pump_state_textual = "ON" if (pumpState == 1) else "OFF"
            print_and_log("Level = {}%, Pump: {}".format(level * 100, pump_state_textual), log_file)
            csv_file.write("{};{};{}\n".format(get_timestamp(), level, pumpState))    # TODO: Store level in Log

            print_and_log("Sending data to Thingspeak...", log_file)
            send_data_to_thingspeak(THINGSPEAKURL, THINGSPEAKKEY, 'field1', 'field2', level, pumpState, log_file)
            sys.stdout.flush()

            status_led.blink()  # Heartbeat TODO: check if this works as intended
            sleep(sleep_time)  # Wait
        except IOError as e:
            print_and_log("File write error occurred: {}".format(e.reason), log_file)
        except:
            print_and_log("Unknown error occurred! Exiting...", log_file)
            break

    # Terminate Program
    print_and_log("Done.", log_file)
    csv_file.close()
    log_file.close()


if __name__ == "__main__":
    main()
