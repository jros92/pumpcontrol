#!/usr/bin/python
# Use Python 3

import csv
from time import sleep
from datetime import datetime, date, time, timedelta
# import pytz
# from tzlocal import get_localzone

import logging
import traceback

"""A timer to turn on pump operation for a set period of time, and turn it off after that time interval elapsed ("the timer expired").

Attributes:
    end_time: The time at which the timer expires. Stored as a unix timestamp in timer.cfg in the CFG directory.
"""


"""Functions to manipulate the time interval"""

def add_time(timer_filepath, log_file_path_abs, days = 0, hours = 0, minutes = 0, seconds = 0):
    """Add time to the timer's time interval"""
    current_end_time_unix = read_end_time(timer_filepath, log_file_path_abs)
    current_end_time_dt = datetime.fromtimestamp(current_end_time_unix)

    # If timer is currently expired, reset the timer to now and add the time
    if current_end_time_dt < datetime.now():
        current_end_time_dt = datetime.now()
        # otherwise, just add the time

    time_to_add_dt = timedelta(days = days, hours = hours, minutes = minutes, seconds = seconds)
    new_end_time = current_end_time_dt + time_to_add_dt
    new_end_time_unix = int(new_end_time.timestamp())
    print("Added time ({}). New end time is now: {} / unix: {}".format(time_to_add_dt, new_end_time, new_end_time_unix))
    write_end_time(timer_filepath, new_end_time_unix, log_file_path_abs)

# TODO: Finish and test - needs to be logical, should it be possible to go negative?
# def subtract_time(timer_filepath, log_file_path_abs, days = 0, hours = 0, minutes = 0, seconds = 0):
#     """Subtract time from the timer's time interval"""
#     current_end_time = read_end_time(timer_filepath, log_file_path_abs)
#     new_end_time = current_end_time - timedelta(days = days, hours = hours, minutes = minutes, seconds = seconds)
#     write_end_time(timer_filepath, new_end_time, log_file_path_abs)

# TODO: Write and test
# def set_timer_end_time_dt(timer_filepath, log_file_path_abs, end_time_dt):

def set_timer_time_left(timer_filepath, log_file_path_abs, days = 0, hours = 0, minutes = 0, seconds = 0):
    """Reset the timer to a specified time interval"""
    current_end_time_dt = datetime.now()
    time_to_add_dt = timedelta(days = days, hours = hours, minutes = minutes, seconds = seconds)
    new_end_time = current_end_time_dt + time_to_add_dt
    new_end_time_unix = int(new_end_time.timestamp())
    print("Reset timer to ({}). New end time is now: {} / unix: {}".format(time_to_add_dt, new_end_time, new_end_time_unix))
    write_end_time(timer_filepath, new_end_time_unix, log_file_path_abs)


"""Shortcut Functions to add time"""

def add_one_hour(timer_filepath, log_file_path_abs):
    add_time(timer_filepath, log_file_path_abs, hours = 1)


def add_fifteen_minutes(timer_filepath, log_file_path_abs):
    add_time(timer_filepath, log_file_path_abs, minutes = 15)


"""Functions to retrieve information about the time interval"""

def get_end_time_unix(timer_filepath, log_file_path_abs):
    """Get end time as unix timestamp"""
    end_time_unix = read_end_time(timer_filepath, log_file_path_abs)
    return end_time_unix


def get_end_time_textual_full(timer_filepath, log_file_path_abs):
    """Get end time in full textual representation"""
    end_time_unix = read_end_time(timer_filepath, log_file_path_abs)
    end_time_dt = datetime.fromtimestamp(end_time_unix)
    result = "{}".format(end_time_dt.strftime("%A, %d %B %Y, %H:%M:%S"))
    return result


def get_end_time_textual_simplified(timer_filepath, log_file_path_abs):
    """Get end time in simplified textual representation"""
    end_time_unix = read_end_time(timer_filepath, log_file_path_abs)
    end_time_dt = datetime.fromtimestamp(end_time_unix)
    time_left = get_time_left(timer_filepath, log_file_path_abs)
    result = "Timer "
    if time_left >= timedelta(days = 1):
        result += "expires in {} days".format(time_left.days)
    elif time_left.total_seconds() > 0:
        result += "expires today"
    else:
        result += "expired"
    result += " at {} UTC".format(end_time_dt.strftime("%H:%M:%S"))
    # result += " at {}".format(end_time_dt.astimezone(get_localzone()).strftime("%H:%M:%S")) # Not working yet
    return result


def get_time_left(timer_filepath, log_file_path_abs):
    """Time left on the timer as a timedelta object"""
    end_time_unix = read_end_time(timer_filepath, log_file_path_abs)
    end_time_dt = datetime.fromtimestamp(end_time_unix)
    # print("End Time datetime object: {}".format(end_time_dt))
    # print("Now datetime object: {}".format(datetime.now()))
    time_left = end_time_dt - datetime.now()
    # print("Time left: {} seconds".format(time_left))
    return time_left


def get_time_left_seconds(timer_filepath, log_file_path_abs):
    """Time left on the timer in seconds"""
    time_left = get_time_left(timer_filepath, log_file_path_abs)
    # print("Time left: {} seconds".format(time_left))
    return time_left.total_seconds()


def get_time_left_textual(timer_filepath, log_file_path_abs):
    """Get a full textual message on the time left on the timer"""
    time_left = get_time_left(timer_filepath, log_file_path_abs)
    result = ""
    if (time_left.total_seconds() > 0):
        result += "Time left: {}".format(str(time_left).split(".")[0])
    else:
        result += "Time expired {} ago".format(str(abs(time_left)).split(".")[0])

    return result


"""Pumping functions"""

def is_pump_desired(timer_filepath, log_file_path_abs):
    """Check if time is over or not, return True or False"""
    time_left_seconds = get_time_left_seconds(timer_filepath, log_file_path_abs)
    return time_left_seconds > 0


"""File I/O Functions"""

def read_end_time(timer_filepath, log_file_path_abs):
    """Read end time from file, return unix timestamp as int"""
    try:
        timer_file = open(timer_filepath, "r")
        timer_endtime = int(timer_file.readline())
        timer_file.close()
        print("Successfully read timer end time from file. End time: {}, file: {}".format(timer_endtime, timer_filepath), log_file_path_abs)
    except IOError as timer_err:
        print("IOError occurred: timer end time file ({}) could not be read. "
                      "Using default value of {}. Error:\n{}"
                      .format(timer_filepath, 0, timer_err), log_file_path_abs)
        return 0
    except ValueError as timer_err:
        print("Value Error occurred: timer end time could not be recognized as an integer."
                      "Using default value of {}. Error:\n{}"
                      .format(0, timer_err), log_file_path_abs)
        return 0

    return timer_endtime


def write_end_time(timer_filepath, end_time_unix, log_file_path_abs):
    """Write end time to file as a unix timestamp"""
    try:
        timer_file = open(timer_filepath, "w")
        timer_file.write(str(end_time_unix))
        timer_file.close()
        print("Successfully wrote new timer end time to file: {}".format(timer_filepath), log_file_path_abs)
    except IOError as timer_err:
        print("IOError occurred: timer end time file ({}) could not be written. Error:\n{}"
                      .format(timer_filepath, timer_err), log_file_path_abs)
        return 0
    except ValueError as timer_err:
        print("Value Error occurred: timer end time file could not be written. Error:\n{}"
                      .format(timer_err), log_file_path_abs)
        return 0


def main():
    """For testing purposes"""
    print("Now: " + str(datetime.now()))
    
    timer_filepath = "cfg/timer.cfg"
    log_file_path_abs = "testlog_timer.log"


    # end_time = read_end_time(timer_filepath, log_file_path_abs)
    # print("Read end time: {}\n".format(end_time))

    # end_time = get_end_time_textual_full(timer_filepath, log_file_path_abs)
    # print("Get end time: {}\n".format(end_time))

    # time_left_seconds = get_time_left_seconds(timer_filepath, log_file_path_abs)
    # print("Time left: {} seconds\n".format(time_left_seconds))

    # pump_desired = is_pump_desired(timer_filepath, log_file_path_abs)
    # print("Pump desired: {}\n".format(pump_desired))

    # write_end_time(timer_filepath, 1590230557, log_file_path_abs)

    # time_left_seconds = get_time_left_seconds(timer_filepath, log_file_path_abs)
    # print("Time left: {} seconds\n".format(time_left_seconds))

    # pump_desired = is_pump_desired(timer_filepath, log_file_path_abs)
    # print("Pump desired: {}\n".format(pump_desired))

    # add_one_hour(timer_filepath, log_file_path_abs)
    # add_fifteen_minutes(timer_filepath, log_file_path_abs)

    # time_left_seconds = get_time_left_seconds(timer_filepath, log_file_path_abs)
    # print("Time left: {} seconds\n".format(time_left_seconds))

    # pump_desired = is_pump_desired(timer_filepath, log_file_path_abs)
    # print("Pump desired: {}\n".format(pump_desired))

    # add_one_hour(timer_filepath, log_file_path_abs)

    print("End time (unix): {}, full: {}\n".format(get_end_time_unix(timer_filepath, log_file_path_abs), get_end_time_textual_full(timer_filepath, log_file_path_abs)))
    
    time_left_seconds = get_time_left_seconds(timer_filepath, log_file_path_abs)
    print("Time left: {} seconds\n".format(time_left_seconds))

    add_fifteen_minutes(timer_filepath, log_file_path_abs)

    set_timer_time_left(timer_filepath, log_file_path_abs, seconds = 3)

    time_left_seconds = get_time_left_seconds(timer_filepath, log_file_path_abs)
    print("Time left: {} seconds\n".format(time_left_seconds))

    pump_desired = is_pump_desired(timer_filepath, log_file_path_abs)
    print("Pump desired: {}\n".format(pump_desired))

    print(get_end_time_textual_simplified(timer_filepath, log_file_path_abs))

    set_timer_time_left(timer_filepath, 0, seconds = 0)

    time_left_seconds = get_time_left_seconds(timer_filepath, log_file_path_abs)
    print("Time left: {} seconds\n".format(time_left_seconds))

    print(get_end_time_textual_simplified(timer_filepath, log_file_path_abs))









if __name__ == "__main__":
    """For testing purposes"""
    logging.basicConfig()
    # logging.basicConfig(level=logging.DEBUG, filename='myapp.log', format='%(asctime)s %(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)
    try:
        main()
    except Exception as e:
        logger.exception("Main crashed: %s\n%s", e, traceback.format_exc())



#     """For testing purposes"""
#     print("Now: " + str(datetime.now()))
#     new_timer = Timer(timedelta(hours = 3))
#     print("Pump desired? " + str(new_timer.is_pump_desired()))
#     print("End time: " + str(new_timer.get_end_time_textual_full()))
#     print("Time left: " + str(new_timer.time_left()))

#     new_timer.add_time(hours = 0.5)
#     print("Pump desired? " + str(new_timer.is_pump_desired()))
#     print("End time: " + str(new_timer.get_end_time_textual_full()))
#     print("Time left: " + str(new_timer.time_left()))

#     new_timer.subtract_time(hours = 4)
#     print("Pump desired? " + str(new_timer.is_pump_desired()))
#     print("End time: " + str(new_timer.get_end_time_textual_full()))
#     print("Time left: " + str(new_timer.time_left()))

#     new_timer.reset_time_interval(minutes = 4)
#     print("Pump desired? " + str(new_timer.is_pump_desired()))
#     print("End time: " + str(new_timer.get_end_time_textual_full()))
#     print("Time left: " + str(new_timer.time_left()))
#     print("***Sleeping for 2 seconds***")
#     sleep(2)
#     print("Time left: " + str(new_timer.time_left()))

#     new_timer.subtract_time(minutes = 3, seconds = 50)
#     print("Pump desired? " + str(new_timer.is_pump_desired()))
#     print("End time: " + str(new_timer.get_end_time_textual_full()))
#     print("Time left: " + str(new_timer.time_left()))
#     print("***Sleeping for 10 seconds***")
#     sleep(10)
#     print("Pump desired? " + str(new_timer.is_pump_desired()))
#     print("End time: " + str(new_timer.get_end_time_textual_full()))
#     print("Time left: " + str(new_timer.time_left()))