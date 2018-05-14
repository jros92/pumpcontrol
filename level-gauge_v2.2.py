#!/usr/bin/python
# Use Python 3

# Credit goes to Matt Hawkins from raspberrypi-spy.co.uk
# Thanks for the awesome tutorial on IoT using the RPi and ThingSpeak.
# I reused his sendData() method to send data to Thingspeak

import os
import sys
import urllib  # URL functions
import urllib2  # URL functions

import logging

import time
from time import sleep
from datetime import datetime

from gpiozero import LED
from gpiozero import Button

# Parameters
threshold_default = 30  # minimum level for pump operation, in per cent (Default = 20)
sleep_time = 30  # frequency to check level, in seconds (Default = 30)

THINGSPEAKKEY = 'C9Z5GCAFI42KFAQK'
THINGSPEAKURL = 'https://api.thingspeak.com/update'

log_file_path = 'logs'
log_file_name = 'log'
csv_file_name = 'csv'


# Pins
SEED_VOLTAGE_PIN_NO = 26
LVL_PIN_NO_ARRAY = [4, 17, 27, 22, 23, 24, 25, 5, 6, 13]    # ordered from 0 to 100
PUMP_PIN_NO = 20
STATUS_LED_PIN_NO = 21


# Get Timestamp
def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")


def print_and_log(message, log_file_path_abs):
    log_file = open(log_file_path_abs, "a+")
    message_string = "{}: {}\n".format(get_timestamp(), message)
    print(message)
    log_file.write(message_string)
    log_file.close()


# Probe the (10) level pins for HIGH or LOW and return boolean array
def probe_level_pins(log_file_path_abs):
    lvlPinNoArray = list(LVL_PIN_NO_ARRAY)
    lvl_pin_values = [False] * len(lvlPinNoArray)

    seedVoltage = LED(SEED_VOLTAGE_PIN_NO)
    seedVoltage.on()
    for x in range(len(lvlPinNoArray)):
        #print_and_log("Checking pin no. {}: GPIO {}".format(x, lvlPinNoArray[x]), log_file_path_abs)
        lvlPin = Button(lvlPinNoArray[x], pull_up=False)
        lvl_pin_values[x] = lvlPin.is_pressed
    seedVoltage.off()
    print_and_log("Level Pin status: {}".format(lvl_pin_values), log_file_path_abs)
    return lvl_pin_values


# First probe GPIO pins, then read the returned value array in reversed order (starting with 100%),
# and break at first HIGH and return its corresponding level [0.0-1.0]
def read_tank_level(log_file_path_abs):
    lvl_pin_values_reversed = list(reversed(list(probe_level_pins(log_file_path_abs))))
    for x in range(len(LVL_PIN_NO_ARRAY)+1):
        if x == len(LVL_PIN_NO_ARRAY):
            break
        if lvl_pin_values_reversed[x]:
            break
    result = (float(len(LVL_PIN_NO_ARRAY)) - x) / float(len(LVL_PIN_NO_ARRAY))
    print_and_log("Detected tank level is {}%".format(result * 100), log_file_path_abs)
    return result


# Turn on pump
def pump_on(pump, log_file_path_abs):
    pump.off() # Pump is ON when LOW
    print_and_log("Pump turned ON", log_file_path_abs)


# Turn off pump
def pump_off(pump, log_file_path_abs):
    pump.on() # Pump is OFF when HIGH
    print_and_log("Pump turned OFF", log_file_path_abs)


# Get textual representation of pump state
def pump_state_textual(pump_state):
    return "ON" if (pump_state == 1) else "OFF"


def send_data_to_thingspeak(url, key, level, pump_state, log_file_path_abs):
    """
  Send event to internet site
  """

    values = {'api_key': key, 'field1': level, 'field2': pump_state}

    postdata = urllib.urlencode(values)
    req = urllib2.Request(url, postdata)

    try:
        # Send data to Thingspeak
        response = urllib2.urlopen(req, None, 5)
        html_string = response.read()
        response.close()

        log = "Successfully sent data: "
        log = log + "{:.1f}".format(level) + ", "
        log = log + "{:.2f}".format(pump_state) + ", "
        log = log + 'Update ' + html_string
    except urllib2.HTTPError as e:
        log = log + 'Error sending data to Thingspeak: Server could not fulfill the request. Error code: ' + e.code
    except urllib2.URLError as e:
        log = log + 'Error sending data to Thingspeak: Failed to reach server. Reason: ' + e.reason
    except:
        log = log + 'Unknown error sending data to Thingspeak'

    print_and_log(log, log_file_path_abs)


def read_threshold_from_file(filepath, log_file_path_abs):
    try:
        cfg_file_threshold = open(filepath, "r")
        threshold = int(cfg_file_threshold.readline())
        cfg_file_threshold.close()
        print_and_log("Successfully read threshold value from file: {}".format(threshold), log_file_path_abs)
    except IOError as threshold_err:
        print_and_log("IOError occurred: threshold could not be read. "
                      "Using default value of {}. Error:\n{}".format(threshold_default, threshold_err), log_file_path_abs)
        return threshold_default
    except ValueError as threshold_err:
        print_and_log("Value Error occurred: threshold could not be read. "
                      "Using default value of {}. Error:\n{}".format(threshold_default, threshold_err), log_file_path_abs)
        return threshold_default
    return threshold


# Main function
def main():
    now = datetime.now()
    my_path = os.path.abspath(os.path.dirname(__file__))
    log_file_path_abs = os.path.join(my_path, "{}/{}_{}.log".format(log_file_path, log_file_name,
                                                                    now.strftime("%Y-%m-%d_%H-%M-%S")))
    csv_file_path_abs = os.path.join(my_path, "{}/{}_{}.csv".format(log_file_path, csv_file_name,
                                                                    now.strftime("%Y-%m-%d_%H-%M-%S")))
    print_and_log("Starting...", log_file_path_abs);

    csv_file = open(csv_file_path_abs, "w+")
    csv_file.write("Time;Level;Pump\n")
    csv_file.close()

    pump = LED(PUMP_PIN_NO, active_high=False)
    #pump_off(pump, log_file)
    status_led = LED(STATUS_LED_PIN_NO)

    # CFG stuff - TODO: quick and dirty for testing, needs to be replaced
    cfg_file_threshold_path_abs = os.path.join(my_path, "threshold.cfg")

    # TODO: Read Thingspeak URL and Key from config file

    # Main Loop
    while True:
        try:
            level = read_tank_level(log_file_path_abs)

            threshold = read_threshold_from_file(cfg_file_threshold_path_abs, log_file_path_abs)
            print_and_log("Using threshold value of: {}".format(threshold), log_file_path_abs)

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

            print_and_log("Current state: Level: {}% | Pump: {}".format(level * 100, pump_state_textual(pumpState)), log_file_path_abs)

            csv_file = open(csv_file_path_abs, "a")
            csv_file.write("{};{};{}\n".format(get_timestamp(), level, pumpState))    # TODO: Store level in Log
            csv_file.close()

            print_and_log("Sending data to Thingspeak...", log_file_path_abs)
            send_data_to_thingspeak(THINGSPEAKURL, THINGSPEAKKEY, level, pumpState, log_file_path_abs)
            sys.stdout.flush()

            status_led.blink()  # Heartbeat TODO: check if this works as intended
            sleep(sleep_time)  # Wait
        # except IOError as e:
        #     print_and_log("File write error occurred: {}".format(e), log_file)
        except Exception as err:
            print_and_log("Error occurred! Exiting...", log_file_path_abs)
            raise err

    # Terminate Program
    print_and_log("Terminating...", log_file_path_abs)

    try:
        csv_file.close()
        log_file.close()
    except:
        print("Unable to close file stream.")
    finally:
        print("Done.")


if __name__ == "__main__":
    logging.basicConfig()
    logger = logging.getLogger()
    try:
        main()
    except Exception as e:
        logger.exception("Main crashed: %s", e)
