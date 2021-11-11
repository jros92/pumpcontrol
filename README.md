# pumpcontrol
A custom IoT device to control a water pump over the internet and read and display the water tank level. Implements emergency shutoff for low tank levels.<br>
Uses python 3 and django hosted on nginx.<br>
Runs on a Raspberry Pi Zero W, utilizing GPIO and WiFi, reading sensor information from a custom tank level sensor and controlling a 230V relais to regulate pump operation.
