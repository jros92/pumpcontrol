from django.shortcuts import render
from django.http import HttpResponse
from django import forms

import os


mode_file_path = os.path.join("/home/pi/pumpcontrol", "cfg", "mode_selection.cfg")


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


def index(request):
    active_mode = read_mode_from_file()
    new_mode = ''

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        form = forms.Form(request.POST)
        if request.POST.get('Manual'):
            new_mode = "MANUAL"
        elif request.POST.get('Scheduled'):
            new_mode = "SCHEDULED"
        elif request.POST.get('Timed'):
            new_mode = "TIMED"
        else:
            pass  # unknown

        write_mode_to_file(new_mode)

    # if a GET (or any other method) we'll create a blank form
    # else:

    context = {'active_mode': active_mode, 'new_mode': new_mode}

    return render(request, 'frontend/index.html', context)


def settings(request):
    return HttpResponse("Settings here")
