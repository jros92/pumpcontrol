#!/usr/bin/python
# Use Python 3

import csv
from time import sleep
from datetime import datetime, date, time, timedelta


class Timer():
    """A timer to turn on pump operation for a set period of time, then turn it off.

    Attributes:
        end_time: The time at which the time on the timer is up.
    """


    def __init__(self, time_interval):
        self.end_time = datetime.now() + time_interval


    """Methods to manipulate the time interval"""

    def add_time(self, days = 0, hours = 0, minutes = 0, seconds = 0):
        """Add time to the timer's time interval"""
        self.end_time += timedelta(days = days, hours = hours, minutes = minutes, seconds = seconds)


    def subtract_time(self, days = 0, hours = 0, minutes = 0, seconds = 0):
        """Subtract time from the timer's time interval"""
        self.end_time -= timedelta(days = days, hours = hours, minutes = minutes, seconds = seconds)


    def reset_time_interval(self, days = 0, hours = 0, minutes = 0, seconds = 0):
        """Reset timer to specified time interval"""
        self.end_time = datetime.now() + timedelta(days = days, hours = hours, minutes = minutes, seconds = seconds)


    """Methods to retrieve information about the time interval"""

    def is_pump_desired(self):
        """Check if time is over or not, return True or False"""
        return datetime.now() < self.end_time


    def get_end_time(self):
        return self.end_time


    def time_left(self):
        """Time left on the timer in seconds"""
        return (self.end_time - datetime.now())


    # def main():
    #     """For testing purposes"""
    #     pump_desired = is_pump_desired()
    #     print(pump_desired)
    #     return pump_desired


if __name__ == "__main__":
    """For testing purposes"""
    print("Now: " + str(datetime.now()))
    new_timer = Timer(timedelta(hours = 3))
    print("Pump desired? " + str(new_timer.is_pump_desired()))
    print("End time: " + str(new_timer.get_end_time()))
    print("Time left: " + str(new_timer.time_left()))
    
    new_timer.add_time(hours = 0.5)
    print("Pump desired? " + str(new_timer.is_pump_desired()))
    print("End time: " + str(new_timer.get_end_time()))
    print("Time left: " + str(new_timer.time_left()))

    new_timer.subtract_time(hours = 4)
    print("Pump desired? " + str(new_timer.is_pump_desired()))
    print("End time: " + str(new_timer.get_end_time()))
    print("Time left: " + str(new_timer.time_left()))

    new_timer.reset_time_interval(minutes = 4)
    print("Pump desired? " + str(new_timer.is_pump_desired()))
    print("End time: " + str(new_timer.get_end_time()))
    print("Time left: " + str(new_timer.time_left()))
    print("***Sleeping for 2 seconds***")
    sleep(2)
    print("Time left: " + str(new_timer.time_left()))

    new_timer.subtract_time(minutes = 3, seconds = 50)
    print("Pump desired? " + str(new_timer.is_pump_desired()))
    print("End time: " + str(new_timer.get_end_time()))
    print("Time left: " + str(new_timer.time_left()))
    print("***Sleeping for 10 seconds***")
    sleep(10)
    print("Pump desired? " + str(new_timer.is_pump_desired()))
    print("End time: " + str(new_timer.get_end_time()))
    print("Time left: " + str(new_timer.time_left()))