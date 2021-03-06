from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django import forms

import os
import subprocess
import csv
from datetime import datetime

# Load own modules ###################################
import importlib.util

# Pump Scheduler Module
spec = importlib.util.spec_from_file_location("module.name", "/home/pi/pumpcontrol/pump_scheduler.py")
pump_scheduler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pump_scheduler)

# Pump Timer Module
spec = importlib.util.spec_from_file_location("module.name", "/home/pi/pumpcontrol/pump_timer.py")
pump_timer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pump_timer)
######################################################

cfg_directory = os.path.join("/home/pi/pumpcontrol", "cfg")
mode_file_path = os.path.join(cfg_directory, "mode_selection.cfg")
manual_state_file_path = os.path.join(cfg_directory, "manual_pump_control.cfg")
schedule_file_path = os.path.join(cfg_directory, "schedule.csv")
timer_file_path = os.path.join(cfg_directory, "timer.cfg")

# def check_pumpcontrol_running():
#     #subprocess.check_output(['ls', '-l'])
#     stdout = subprocess.check_output(["ps", "-f", "-C", "python", "|", "grep", "pumpcontrol/level-gauge_v3.0b2.py", "|", "awk", "'{print $2}'"], shell=True)
#     #stdout = subprocess.check_output(["awk", "'{print $2}'"], input=subprocess.check_output(["grep", "pumpcontrol/level-gauge_v3.0b2.py"], input=subprocess.check_output(["ps", "-f", "-C", "python"])))
#     # try:
#     result = int(stdout)
#
#     return result >= 0


def read_schedule_simple():
    try:
        schedule_arr = []
        with open(schedule_file_path) as schedule_file:
            schedreader = csv.reader(schedule_file, delimiter=',')
            # next(schedreader)  # Skip header
            # print("Rows read:")
            for row in schedreader:
                # print(row)
                schedule_arr.append(row)
            print("Successfully read schedule from CSV.")
        return schedule_arrget_schedule_textual_vertically
    except IOError as err:
        print("IOError: could not read schedule.csv. {}".format(err))
        return "Unable to read schedule."


def read_mode_from_file():
    try:
        mode_file = open(mode_file_path, "r")
        mode = mode_file.readline()
        mode_file.close()
        print("Successfully read desired control mode from file: {}".format(mode))
    except IOError as mode_err:
        print("IOError occurred: control mode could not be read. "
                      "Using default value of {}. Error:\n{}"
                      .format(1, mode_err))
        return 1
    except ValueError as mode_err:
        print("Value Error occurred: control mode could not be recognized.  Has to be \"0\", \"1\", or \"2\"."
                      "Using default value of {}. Error:\n{}"
                      .format("OFF", mode_err))
        return 1
    return mode


def read_manual_state_from_file():
    try:
        state_file = open(manual_state_file_path, "r")
        state = state_file.readline()
        state_file.close()
        print("Successfully read manual pump state from file: {}".format(state))
    except IOError as state_err:
        print("IOError occurred: manual pump state could not be read. "
                      "Using default value of {}. Error:\n{}"
                      .format(0, state_err))
        return 0
    except ValueError as state_err:
        print("Value Error occurred: control mode could not be recognized.  Has to be \"0\", \"1\"."
                      "Using default value of {}. Error:\n{}"
                      .format(0, state_err))
        return 0
    return state


def write_mode_to_file(new_mode):
    try:
        mode_file = open(mode_file_path, "w")
        mode_file.write(new_mode)
        mode_file.close()
        print("Successfully wrote new control mode to file: {}".format(new_mode))
    except IOError as mode_err:
        print("IOError occurred: control mode could not be written. Error:\n{}".format(mode_err))
    except ValueError as mode_err:
        print("Value Error occurred: control mode could not be written. Error:\n{}".format(mode_err))


def write_manual_state_to_file(new_state):
    try:
        state_file = open(manual_state_file_path, "w")
        state_file.write(new_state)
        state_file.close()
        print("Successfully wrote new manual state to file: {}".format(new_state))
    except IOError as state_err:
        print("IOError occurred: manual state could not be written. Error:\n{}".format(state_err))
    except ValueError as state_err:
        print("Value Error occurred: manual state could not be written. Error:\n{}".format(state_err))


def index(request):
    # program_running = check_pumpcontrol_running()
    active_mode = read_mode_from_file()
    new_mode = ''

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        form = forms.Form(request.POST)

        # Look up the name attribute of the form that was submitted, 
        # then check for submit value and perform corresponding commands

        # Mode switch commanded
        if request.POST.get('Mode_Switch'):
            requested_mode = request.POST['Mode_Switch']
            if requested_mode == 'Manual':
                new_mode = "MANUAL"
            elif requested_mode == 'Scheduled':
                new_mode = "SCHEDULED"
            elif requested_mode == 'Timed':
                new_mode = "TIMED"

            write_mode_to_file(new_mode)

        # Pump switch on/off in Manual control mode commanded
        if request.POST.get('Manual_Control'):
            if (request.POST['Manual_Control'] == 'ON'):
                write_manual_state_to_file("1")
            else:
                write_manual_state_to_file("0")

        # Timer change in Timed mode commanded
        if request.POST.get('Timer_Control'):
            if request.POST['Timer_Control'] == 'AddFourHours':
                pump_timer.add_four_hours(timer_file_path, 0)
            elif request.POST['Timer_Control'] == 'AddOneHour':
                pump_timer.add_one_hour(timer_file_path, 0)
            elif request.POST['Timer_Control'] == 'AddFifteenMinutes':
                pump_timer.add_fifteen_minutes(timer_file_path, 0)
            elif request.POST['Timer_Control'] == 'Reset':
                pump_timer.set_timer_time_left(timer_file_path, 0, seconds = 0)
            else:
                pass  # unknown

        # return HttpResponseRedirect('') // not needed anymore because of AJAX page reload
        return HttpResponse('')

    # if a GET (or any other method) we'll create a blank form
    else:
        # Retrieve variables from pumpcontrol modules and text files
        today_textual = pump_scheduler.get_today_textual()
        manual_state = read_manual_state_from_file()
        if manual_state == "1":
            manual_state = "ON"
        elif manual_state == "0":
            manual_state = "OFF"

        schedule_simple = pump_scheduler.get_schedule_textual_vertically(schedule_file_path)
        schedule_today = pump_scheduler.get_todays_schedule_textual_vertically(schedule_file_path)
        schedule_tomorrow = pump_scheduler.get_tomorrows_schedule_textual_vertically(schedule_file_path)

        timer_expiration_textual = pump_timer.get_end_time_textual_simplified(timer_file_path, 0)
        time_left_textual = pump_timer.get_time_left_textual(timer_file_path, 0)

        # Export the variables to be used in HTML
        context = {
            'today_textual': today_textual,
            'active_mode': active_mode, 
            'new_mode': new_mode, 
            'manual_state': manual_state, 
            'schedule_simple': schedule_simple, 
            'schedule_today': schedule_today,
            'schedule_tomorrow': schedule_tomorrow,
            'timer_expiration_textual': timer_expiration_textual,
            'time_left_textual': time_left_textual
            }

        return render(request, 'frontend/index.html', context)


def settings(request):
    return HttpResponse("Settings here")
