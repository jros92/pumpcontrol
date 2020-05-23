#!/usr/bin/python
# Use Python 3

import csv
from time import sleep
from datetime import datetime, date, time, timedelta


"""A timer to turn on pump operation for a set period of time, then turn it off.

Attributes:
    end_time: The time at which the timer expires.
"""


"""Functions to manipulate the time interval"""

def add_time(timer_filepath, log_file_path_abs, days = 0, hours = 0, minutes = 0, seconds = 0):
    """Add time to the timer's time interval"""
    current_end_time = read_end_time(timer_filepath, log_file_path_abs)
    new_end_time = current_end_time + timedelta(days = days, hours = hours, minutes = minutes, seconds = seconds)
    write_end_time(timer_filepath, new_end_time, log_file_path_abs)


def subtract_time(timer_filepath, log_file_path_abs, days = 0, hours = 0, minutes = 0, seconds = 0):
    """Subtract time from the timer's time interval"""
    current_end_time = read_end_time(timer_filepath, log_file_path_abs)
    new_end_time = current_end_time - timedelta(days = days, hours = hours, minutes = minutes, seconds = seconds)
    write_end_time(timer_filepath, new_end_time, log_file_path_abs)

def reset_time_interval(timer_filepath, log_file_path_abs, days = 0, hours = 0, minutes = 0, seconds = 0):
    """Reset timer to specified time interval"""
    new_end_time = datetime.now() + timedelta(days = days, hours = hours, minutes = minutes, seconds = seconds)
    write_end_time(timer_filepath, new_end_time, log_file_path_abs)


"""Functions to retrieve information about the time interval"""

def is_pump_desired(timer_filepath, log_file_path_abs):
    """Check if time is over or not, return True or False"""
    end_time = read_end_time(timer_filepath, log_file_path_abs)
    return datetime.now() < end_time


def read_end_time(timer_filepath, log_file_path_abs):
    """Read end time from file"""
    try:
        timer_file = open(timer_filepath, "r")
        timer_endtime = int(timer_file.readline())
        timer_file.close()
        print_and_log("Successfully read timer end time from file: {}".format(timer_endtime), log_file_path_abs)
    except IOError as timer_err:
        print_and_log("IOError occurred: timer end time could not be read. "
                      "Using default value of {}. Error:\n{}"
                      .format(0, timer_err), log_file_path_abs)
        return 0
    except ValueError as timer_err:
        print_and_log("Value Error occurred: timer end time could not be recognized as an integer."
                      "Using default value of {}. Error:\n{}"
                      .format(0, timer_err), log_file_path_abs)
        return 0
    return timer_endtime


# TODO: Finish and test
# def get_end_time(timer_filepath, log_file_path_abs):
#     """Time left on the timer in seconds"""
#     end_time = read_end_time(timer_filepath, log_file_path_abs)
#     result = "{}".format(end_time.strftime("%A, %d %B %Y"))
#     return result


def get_time_left_seconds(timer_filepath, log_file_path_abs):
    """Time left on the timer in seconds"""
    end_time = read_end_time(timer_filepath, log_file_path_abs)
    return (end_time - datetime.now())


# #TODO: Finish and Test
# def get_time_left_textual(timer_filepath, log_file_path_abs):
#     """Time left on the timer in textual form"""
#     time_left_seconds = get_time_left_seconds(timer_filepath, log_file_path_abs)
#     #timedelta?
#     #return 


# def write_end_time(self):
#     datetime.utcfromtimestamp(ts)
#     try:
#         mode_file = open(timer_file_path, "w")
#         mode_file.write(new_mode)
#         mode_file.close()
#         print("Successfully wrote new control mode to file: {}".format(new_mode))
#     except IOError as mode_err:
#         print("IOError occurred: control mode could not be written. Error:\n{}".format(mode_err))
#     except ValueError as mode_err:
#         print("Value Error occurred: control mode could not be written. Error:\n{}".format(mode_err))



# def main():
#     """For testing purposes"""
#     pump_desired = is_pump_desired()
#     print(pump_desired)
#     return pump_desired


# if __name__ == "__main__":
#     """For testing purposes"""
#     print("Now: " + str(datetime.now()))
#     new_timer = Timer(timedelta(hours = 3))
#     print("Pump desired? " + str(new_timer.is_pump_desired()))
#     print("End time: " + str(new_timer.get_end_time()))
#     print("Time left: " + str(new_timer.time_left()))

#     new_timer.add_time(hours = 0.5)
#     print("Pump desired? " + str(new_timer.is_pump_desired()))
#     print("End time: " + str(new_timer.get_end_time()))
#     print("Time left: " + str(new_timer.time_left()))

#     new_timer.subtract_time(hours = 4)
#     print("Pump desired? " + str(new_timer.is_pump_desired()))
#     print("End time: " + str(new_timer.get_end_time()))
#     print("Time left: " + str(new_timer.time_left()))

#     new_timer.reset_time_interval(minutes = 4)
#     print("Pump desired? " + str(new_timer.is_pump_desired()))
#     print("End time: " + str(new_timer.get_end_time()))
#     print("Time left: " + str(new_timer.time_left()))
#     print("***Sleeping for 2 seconds***")
#     sleep(2)
#     print("Time left: " + str(new_timer.time_left()))

#     new_timer.subtract_time(minutes = 3, seconds = 50)
#     print("Pump desired? " + str(new_timer.is_pump_desired()))
#     print("End time: " + str(new_timer.get_end_time()))
#     print("Time left: " + str(new_timer.time_left()))
#     print("***Sleeping for 10 seconds***")
#     sleep(10)
#     print("Pump desired? " + str(new_timer.is_pump_desired()))
#     print("End time: " + str(new_timer.get_end_time()))
#     print("Time left: " + str(new_timer.time_left()))