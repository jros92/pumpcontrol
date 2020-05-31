#!/usr/bin/python
# Use Python 3

# Pumpcontrol
# version 3.2

# Written for the Raspberry Pi Zero W (2018) running Raspbian 9
# Copyright 2018-2020 Joerg R. Schmidt

# Credit goes to Matt Hawkins from raspberrypi-spy.co.uk
# Thanks for his tutorial on IoT using the RPi and ThingSpeak.
# I reused the send_data() method to send data to Thingspeak

import os
import sys
import resource
import traceback
import logging

from enum import Enum

import urllib  # URL functions
import urllib2  # URL functions

import time
from time import sleep
from datetime import datetime

from gpiozero import LED
from gpiozero import Button

import pump_scheduler
import pump_timer


# Parameters ###########################################################################################################

# Default minimum level for pump operation, in percent (Default = 20);
# overwritten with user-specified value if possible
threshold_default = 20
# Width of hysteresis in percent (Default = 10)
threshold_delta = 20
# Frequency to check level, in seconds (Default = 30)
sleep_time = 30

THINGSPEAKKEY = ''
THINGSPEAKURL = 'https://api.thingspeak.com/update'

cfg_path = 'cfg'

log_file_path = 'logs'  # cannot be left empty
log_file_name = ''   # prefix for log file name
csv_file_name = ''   # prefix for csv file name


# GPIO Pin Configuration
SEED_VOLTAGE_PIN_NO = 26
LVL_PIN_NO_ARRAY = [4, 17, 27, 22, 23, 24, 25, 5, 6, 13]    # ordered from 0 to 100
PUMP_PIN_NO = 20
STATUS_LED_PIN_NO = 21

########################################################################################################################


class ControlMode(Enum):
    MANUAL = 'MANUAL'
    SCHEDULED = 'SCHEDULED'
    TIMED = 'TIMED'


# GLOBAL VARIABLES #####################################################################################################

DEFAULT_MODE = ControlMode.MANUAL
control_mode = ControlMode.SCHEDULED  # Start in scheduled mode by default


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
        print("Could not write to log file. IOError occurred: {}".format(e))


def write_to_csv(message, csv_file_path_abs, log_file_path_abs):
    try:
        csv_file = open(csv_file_path_abs, "a+")
        csv_file.write("{}\n".format(message))
        csv_file.close()
    except IOError as e:
        print_and_log("Could not write to CSV file. IOError occurred: {}".format(e), log_file_path_abs)


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

    for x in range(lvl_pin_cnt + 1):
        if x == lvl_pin_cnt:
            break
        if lvl_pin_values_reversed[x]:
            break
    result = (float(lvl_pin_cnt) - x) / float(lvl_pin_cnt)
    print_and_log("Detected tank level is {}%".format(result * 100), log_file_path_abs)
    return result


# Turn on pump
def pump_turn_on(pump, log_file_path_abs):
    pump.on()  # Pump is ON when LOW
    print_and_log("Pump turned ON", log_file_path_abs)
    return True


# Turn off pump
def pump_turn_off(pump, log_file_path_abs):
    pump.off()  # Pump is OFF when HIGH
    print_and_log("Pump turned OFF", log_file_path_abs)
    return False


# Get textual representation of pump state
def pump_state_textual(pump_state):
    return "ON" if pump_state else "OFF"


def send_data_to_thingspeak(url, key, level, pump_state, log_file_path_abs):
    """
  Send event to internet site
  """

    print_and_log("Sending data to Thingspeak...", log_file_path_abs)

    values = {'api_key': key, 'field1': level, 'field2': pump_state}

    postdata = urllib.urlencode(values)
    req = urllib2.Request(url, postdata)

    try:
        # Send data to Thingspeak
        response = urllib2.urlopen(req, None, 5)
        html_string = response.read()
        response.close()

        log_str = "Successfully sent data: {:.1f}, {:.2f}".format(level, pump_state) + ", Update " + html_string
    except urllib2.HTTPError as e:
        # Thrown when URL or Key are wrong
        log_str = 'Error sending data to Thingspeak: Server could not fulfill the request. ' \
                  'Error code: {}'.format(e.code)
    except urllib2.URLError as e:
        # Thrown when no internet connection
        log_str = 'Error sending data to Thingspeak: Failed to reach server. Reason: {}'.format(e.reason)
    except:
        log_str = 'Unknown error sending data to Thingspeak'

    print_and_log(log_str, log_file_path_abs)


# TODO: Improve (settings file)
def read_key_from_file(filepath, log_file_path_abs):
    key = ''
    try:
        key_file = open(filepath, "r")
        key = key_file.readline().rstrip()  # Remove newline character before storing the key!
        key_file.close()
        print_and_log("Successfully read key for Thingspeak service from file.", log_file_path_abs)
    except IOError as key_err:
        print_and_log("IOError occurred: Key could not be read. "
                      "Will not be able to send data Continuing anyways. Error:\n{}"
                      .format(key_err), log_file_path_abs)
    except ValueError as key_err:
        print_and_log("Value Error occurred: Key could not be recognized. "
                      "Will not be able to send data Continuing anyways. Error:\n{}"
                      .format(key_err), log_file_path_abs)
    return key


# TODO: Improve (settings file)
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
        print_and_log("Value Error occurred: threshold could not be recognized as an integer. "
                      "Using default value of {}. Error:\n{}"
                      .format(threshold_default, threshold_err), log_file_path_abs)
        return threshold_default
    return threshold


# TODO: Replace, only for testing purposes
def read_mode_from_file(filepath, log_file_path_abs):
    try:
        mode_file = open(filepath, "r")
        mode = ControlMode(mode_file.readline())
        mode_file.close()
        print_and_log("Successfully read desired control mode from file: {}".format(mode), log_file_path_abs)
    except IOError as mode_err:
        print_and_log("IOError occurred: control mode could not be read. "
                      "Using default value of {}. Error:\n{}"
                      .format(ControlMode.MANUAL, mode_err), log_file_path_abs)
        return DEFAULT_MODE
    except ValueError as mode_err:
        print_and_log("Value Error occurred: control mode could not be recognized.  Has to be \"0\", \"1\", or \"2\"."
                      "Using default value of {}. Error:\n{}"
                      .format(pump_state_textual(False), mode_err), log_file_path_abs)
        return DEFAULT_MODE
    return mode


# TODO: Replace, only for testing purposes
def read_pump_on_off(filepath, log_file_path_abs):
    try:
        manctl_file = open(filepath, "r")
        manctl = bool(int(manctl_file.readline()))
        manctl_file.close()
        print_and_log("Successfully read desired pump state from file: {}".format(pump_state_textual(manctl)), log_file_path_abs)
    except IOError as threshold_err:
        print_and_log("IOError occurred: threshold could not be read. "
                      "Using default value of {}. Error:\n{}"
                      .format(pump_state_textual(False), threshold_err), log_file_path_abs)
        return False
    except ValueError as threshold_err:
        print_and_log("Value Error occurred: pump state could not be recognized. Has to be either \"0\" or \"1\". "
                      "Using default value of {}. Error:\n{}"
                      .format(pump_state_textual(False), threshold_err), log_file_path_abs)
        return False
    return manctl


# Read timer end time from file
# TODO: Improve
def read_timer_end_time_from_file(filepath, log_file_path_abs):
    try:
        timer_file = open(filepath, "r")
        timer_end_time = int(timer_file.readline())
        timer_file.close()
        print_and_log("Successfully read timer end time value from file: {}".format(timer_end_time), log_file_path_abs)
    except IOError as timer_end_time_err:
        print_and_log("IOError occurred: timer end time could not be read. "
                      "Using default value of 0. Error:\n{}"
                      .format(timer_end_time_err), log_file_path_abs)
        return 0
    except ValueError as timer_end_time_err:
        print_and_log("Value Error occurred: timer end time could not be recognized as an integer. "
                      "Using default value of 0. Error:\n{}"
                      .format(timer_end_time_err), log_file_path_abs)
        return 0
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
    cfg_file_threshold_path_abs = os.path.join(my_path, cfg_path, "threshold.cfg")
    key_file_path_abs = os.path.join(my_path, cfg_path, "thingspeak_key.cfg")

    # Read key for Thingspeak service
    # TODO: Read Thingspeak URL and Key from config file
    global THINGSPEAKKEY
    THINGSPEAKKEY = read_key_from_file(key_file_path_abs, log_file_path_abs)

    # Manual pump ctl through file TODO: Replace
    manctl_filepath = os.path.join(my_path, cfg_path, "manual_pump_control.cfg")
    schedule_filepath = os.path.join(my_path, cfg_path, "schedule.csv")
    mode_selection_filepath = os.path.join(my_path, cfg_path, "mode_selection.cfg")
    timer_filepath = os.path.join(my_path, cfg_path, "timer.cfg")

    # Initialize pump state variable - pump is always off if not actively pulled LOW by program
    pump_running = False

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

            # Check selected mode of operation
            # global control_mode
            switch_mode(read_mode_from_file(mode_selection_filepath, log_file_path_abs))

            # Control pump
            pump_allowed = is_pump_allowed(level, pump_running, threshold)
            pump_desired = is_pump_desired(manctl_filepath, schedule_filepath, timer_filepath, log_file_path_abs)
            if pump_allowed & pump_desired:
                pump_running = pump_turn_on(pump, log_file_path_abs)
            else:
                pump_running = pump_turn_off(pump, log_file_path_abs)

            # Log Data
            print_and_log("Current state: Level: {}% | Pump: [ALLOWED: {}, DESIRED: {}, RUNNING: {}]"
                          .format(level * 100,
                                  pump_allowed,
                                  pump_desired,
                                  pump_state_textual(pump_running)),
                          log_file_path_abs)

            write_to_csv("{};{};{}".format(get_timestamp(), level, int(pump_running)), csv_file_path_abs, log_file_path_abs)

            # Send Data to Thingspeak
            send_data_to_thingspeak(THINGSPEAKURL, THINGSPEAKKEY, level * 100, int(pump_running), log_file_path_abs)
            sys.stdout.flush()

            # Wait until next check is due
            print_and_log("Waiting {} seconds until next check...".format(sleep_time), log_file_path_abs)
            sleep(sleep_time)
        except Exception as err:
            print_and_log("An unknown error occurred! Exiting...", log_file_path_abs)
            print_and_log(traceback.format_exc(), log_file_path_abs)
            raise err

    # Terminate Program
    print_and_log("Terminating...", log_file_path_abs)

    print("Done.")
    return 0


def is_pump_allowed(level, pump_running, threshold):
    """Determine if pump operation is allowed based on tank level"""
    pump_allowed = pump_running
    if pump_running:
        if level * 100 < threshold:
            # Level fell below lower threshold during pump operation, stop pumping
            pump_allowed = False
    else:
        if level * 100 >= threshold + threshold_delta:
            # Level is above upper threshold, we can start pumping if we want to
            pump_allowed = True
    return pump_allowed


# TODO: Write logic here. Ultimately use WSGI / Django???
def is_pump_desired(manctl_filepath, schedule_filepath, timer_filepath, log_file_path_abs):
    """Determine if pump operation is desired based on active control mode"""
    global control_mode
    if control_mode == ControlMode.MANUAL:
        # read from file
        pump_desired = read_pump_on_off(manctl_filepath, log_file_path_abs)
    elif control_mode == ControlMode.SCHEDULED:
        # read schedule from file and compare current weekday and time with schedule
        # TODO: Add logging path and logging functionality to scheduler
        pump_desired = pump_scheduler.is_pump_desired(schedule_filepath)
    elif control_mode == ControlMode.TIMED:
        # read timer end time from file and compare current time with end time
        pump_desired = pump_timer.is_pump_desired(timer_filepath, log_file_path_abs)
    else:
        raise Exception("Something went terribly wrong. Pump should be turned off now.\n"
                        "Exact Reason: current control mode not recognized.")

    return pump_desired


def switch_mode(desired_mode):
    global control_mode
    old_mode = control_mode

    if old_mode != desired_mode:
        if isinstance(desired_mode, ControlMode):
            control_mode = desired_mode
            print("Mode switched from {} to {}".format(old_mode, control_mode))
            return True
        else:
            print("Desired mode not recognized. Not switching.")

    return False


if __name__ == "__main__":
    logging.basicConfig()
    # logging.basicConfig(level=logging.DEBUG, filename='myapp.log', format='%(asctime)s %(levelname)s: %(message)s')
    logger = logging.getLogger()
    try:
        main()
    except Exception as e:
        logger.exception("Main crashed: %s\n%s", e, traceback.format_exc())
