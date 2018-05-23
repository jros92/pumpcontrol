from django.shortcuts import render
from django.http import HttpResponse
from django import forms

import os

def read_mode_from_file():
    try:
        filepath = os.path.join("/home/pi/pumpcontrol", "cfg", "mode_selection.cfg")
        mode_file = open(filepath, "r")
        mode = int(mode_file.readline())
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


def index(request):
    # if this is a POST request we need to process the form data
    new_mode = ''
    if request.method == 'POST':
        form = forms.Form(request.POST)
        if request.POST.get('Manual'):
            new_mode = "Manual"
            pass  # do something
        elif request.POST.get('Scheduled'):
            new_mode = "Scheduled"
            pass  # do something else
        else:
            pass  # unknown

    # if a GET (or any other method) we'll create a blank form
    # else:
    active_mode = read_mode_from_file()
    # active_mode = "MANUAL"
    context = {'active_mode': active_mode, 'new_mode': new_mode}

    return render(request, 'frontend/index.html', context)


def settings(request):
    return HttpResponse("Settings here")
