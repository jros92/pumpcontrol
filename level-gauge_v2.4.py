#!/usr/bin/python
# Use Python 3
# Written for the Raspberry Pi Zero W (2018) running Raspbian
# Copyright 2018 Joerg R. Schmidt

# Credit goes to Matt Hawkins from raspberrypi-spy.co.uk
# Thanks for the awesome tutorial on IoT using the RPi and ThingSpeak.
# I reused his sendData() method to send data to Thingspeak

import os
import sys
import resource
import traceback
import logging

import urllib  # URL functions
import urllib2  # URL functions

import time
from time import sleep
from datetime import datetime

from gpiozero import LED
from gpiozero import Button

# Parameters ###########################################################################################################

# Default minimum level for pump operation, in percent (Default = 30);
# overwritten with user-specified value if possible
threshold_default = 30
# Frequency to check level, in seconds (Default = 30)
sleep_time = 30

THINGSPEAKKEY = 'C9Z5GCAFI42KFAQK'
THINGSPEAKURL = 'https://api.thingspeak.com/update'

log_file_path = 'logs'  # cannot be left empty
log_file_name = ''   # prefix for log file name
csv_file_name = ''   # prefix for csv file name


# Pins
SEED_VOLTAGE_PIN_NO = 26
LVL_PIN_NO_ARRAY = [4, 17, 27, 22, 23, 24, 25, 5, 6, 13]    # ordered from 0 to 100
PUMP_PIN_NO = 20
STATUS_LED_PIN_NO = 21

########################################################################################################################

# FUNCTION DEFINITIONS #################################################################################################


# Get Timestamp
def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")


def print_and_log(message, log_file_path_abs):
    print(message)
    try:
        log_file = open(log_file_path_abs, "a+")
        message_string = "{}: {}\n".format(get_timestamp(), message)
        log_file.write(message_string)
        log_file.close()
    except IOError as e:
        print("Could not write to Log file. IOError occurred: {}".format(e))


def write_to_csv(message, csv_file_path_abs, log_file_path_abs):
    try:
        csv_file = open(csv_file_path_abs, "a+")
        csv_file.write("{}\n".format(message))
        csv_file.close()
    except IOError as e:
        print_and_log("Could not write to CSV. IOError occurred: {}".format(e), log_file_path_abs)


# Probe the (10) level pins for HIGH or LOW and return boolean array
def probe_level_pins(lvl_pin_array, seed_voltage, log_file_path_abs):
    lvl_pin_values = [False] * len(list(lvl_pin_array))

    seed_voltage.on()

    for x in range(len(lvl_pin_array)):
        #print_and_log("Checking pin no. {}: GPIO {}".format(x, lvlPinNoArray[x]), log_file_path_abs)
        lvl_pin_values[x] = lvl_pin_array[x].is_pressed

    seed_voltage.off()
    print_and_log("Level Pin status: {}".format(lvl_pin_values), log_file_path_abs)

    return lvl_pin_values


# First probe GPIO pins, then read the returned value array in reversed order (starting with 100%),
# and break at first HIGH and return its corresponding level [0.0-1.0]
def read_tank_level(lvl_pin_array, seed_voltage, log_file_path_abs):
    lvl_pin_values_reversed = list(reversed(list(probe_level_pins(lvl_pin_array, seed_voltage, log_file_path_abs))))
    lvl_pin_cnt = len(lvl_pin_array)

    for x in range(lvl_pin_cnt+1):
        if x == lvl_pin_cnt:
            break
        if lvl_pin_values_reversed[x]:
            break
    result = (float(lvl_pin_cnt) - x) / float(lvl_pin_cnt)
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

        log_str = "Successfully sent data: "
        log_str = log_str + "{:.1f}".format(level) + ", "
        log_str = log_str + "{:.2f}".format(pump_state) + ", "
        log_str = log_str + 'Update ' + html_string
    except urllib2.HTTPError as e:
        # Thrown when URL or Key are wrong
        log_str = 'Error sending data to Thingspeak: Server could not fulfill the request. Error code: {}'.format(e.code)
    except urllib2.URLError as e:
        # Thrown when no internet connection
        log_str = 'Error sending data to Thingspeak: Failed to reach server. Reason: {}'.format(e.reason)
    except:
        log_str = 'Unknown error sending data to Thingspeak'

    print_and_log(log_str, log_file_path_abs)


def read_threshold_from_file(filepath, log_file_path_abs):
    try:
        cfg_file_threshold = open(filepath, "r")
        threshold = int(cfg_file_threshold.readline())
        cfg_file_threshold.close()
        print_and_log("Successfully read threshold value from file: {}".format(threshold), log_file_path_abs)
    except IOError as threshold_err:
        print_and_log("IOError occurred: threshold could not be read. "
                      "Using default value of {}. Error:\n{}"
                      .format(threshold_default, threshold_err), log_file_path_abs)
        return threshold_default
    except ValueError as threshold_err:
        print_and_log("Value Error occurred: threshold could not be read. "
                      "Using default value of {}. Error:\n{}"
                      .format(threshold_default, threshold_err), log_file_path_abs)
        return threshold_default
    return threshold


# MAIN FUNCTION ########################################################################################################
def main():
    now = datetime.now()
    my_path = os.path.abspath(os.path.dirname(__file__))
    log_file_path_abs = os.path.join(my_path, "{}/{}{}.log".format(log_file_path, log_file_name,
                                                                    now.strftime("%Y-%m-%d_%H-%M-%S")))
    csv_file_path_abs = os.path.join(my_path, "{}/{}{}.csv".format(log_file_path, csv_file_name,
                                                                    now.strftime("%Y-%m-%d_%H-%M-%S")))
    print_and_log("Starting...", log_file_path_abs);

    write_to_csv("Time;Level;Pump", csv_file_path_abs, log_file_path_abs)

    try:
        # Set stack size limit to maximum possible
        resource.setrlimit(resource.RLIMIT_STACK, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
        print_and_log("Successfully increased stack size to maximum.", log_file_path_abs)
    except Exception as e:
        print_and_log("Unable to increase stack size. Reason: {}. Continuing...".format(e), log_file_path_abs)

    # Create devices using GPIOZERO library
    try:
        pump = LED(PUMP_PIN_NO, active_high=False)
        #pump_off(pump, log_file)
        status_led = LED(STATUS_LED_PIN_NO)
        seed_voltage = LED(SEED_VOLTAGE_PIN_NO)
        lvl_pin_cnt = len(list(LVL_PIN_NO_ARRAY))
        lvl_pin_array = [LED] * lvl_pin_cnt
        for x in range(lvl_pin_cnt):
            #print_and_log("Checking pin no. {}: GPIO {}".format(x, lvlPinNoArray[x]), log_file_path_abs)
            lvl_pin_array[x] = Button(LVL_PIN_NO_ARRAY[x], pull_up=False)
        print_and_log("Done initializing GPIO devices. Using {} level pins.".format(lvl_pin_cnt),
                      log_file_path_abs);
    except Exception as e:
        print_and_log("Unable to create devices: {}. Exiting...".format(e), log_file_path_abs)
        return 1

    # CFG stuff - TODO: quick and dirty for testing, needs to be replaced
    cfg_file_threshold_path_abs = os.path.join(my_path, "threshold.cfg")

    # TODO: Read Thingspeak URL and Key from config file

    # Heartbeat TODO: check if this works as intended (when program crashes...)
    status_led.blink()

    # Main Loop
    while True:
        try:
            # Read Level
            level = read_tank_level(lvl_pin_array, seed_voltage, log_file_path_abs)

            # Read Threshold from File
            threshold = read_threshold_from_file(cfg_file_threshold_path_abs, log_file_path_abs)
            print_and_log("Using threshold value of: {}".format(threshold), log_file_path_abs)

            # Control pump
            pump_state = 0
            if level * 100 < threshold:
                #pump_off(pump, log_file)
                pump.off()
                pump_state = 0
            else:
                #pump_on(pump, log_file)
                pump.on()
                pump_state = 1

            print_and_log("Current state: Level: {}% | Pump: {}".format(level * 100, pump_state_textual(pump_state)),
                          log_file_path_abs)

            write_to_csv("{};{};{}\n".format(get_timestamp(), level, pump_state), csv_file_path_abs, log_file_path_abs)

            # Send Data to Thingspeak
            print_and_log("Sending data to Thingspeak...", log_file_path_abs)
            send_data_to_thingspeak(THINGSPEAKURL, THINGSPEAKKEY, level * 100, pump_state, log_file_path_abs)
            sys.stdout.flush()

            print_and_log("Waiting {} seconds until next check...".format(sleep_time), log_file_path_abs)
            sleep(sleep_time)  # Wait
        except Exception as err:
            print_and_log("An unknown error occurred! Exiting...", log_file_path_abs)
            print_and_log(traceback.format_exc(), log_file_path_abs)
            raise err

    # Terminate Program
    print_and_log("Terminating...", log_file_path_abs)

    print("Done.")
    return 0


if __name__ == "__main__":
    logging.basicConfig()
    logger = logging.getLogger()
    try:
        main()
    except Exception as e:
        logger.exception("Main crashed: %s\n%s", e, traceback.format_exc())
