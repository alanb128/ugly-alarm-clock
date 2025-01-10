import RPi.GPIO as GPIO
import time
import socketio
import requests
import pygame
import board
import busio
import adafruit_tpa2016
from adafruit_seesaw import seesaw, rotaryio, digitalio
import tinkeringtech_rda5807m
from adafruit_bus_device.i2c_device import I2CDevice

MODE = "slot"

sio = socketio.SimpleClient()
volume = -14
station = 9090

DEBOUNCE = 500
GPIO_TOP_SWITCH = 4
GPIO_MID_SWITCH = 17
GPIO_RIGHT_SWITCH = 27
GPIO_LEFT_SWITCH = 22
GPIO_ANALOG_SWITCH = 5
GPIO_ENC_INT = 23

GPIO.setmode(GPIO.BCM)

GPIO.setup(GPIO_TOP_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GPIO_LEFT_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GPIO_MID_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GPIO_RIGHT_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GPIO_ENC_INT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(GPIO_ANALOG_SWITCH, GPIO.OUT)

# Setup rotary
i2c = board.I2C()  # uses board.SCL and board.SDA
seesaw = seesaw.Seesaw(i2c, 0x37)
seesaw_product = (seesaw.get_version() >> 16) & 0xFFFF
print("Found product {}".format(seesaw_product))
if seesaw_product != 4991:
    print("Wrong firmware loaded?  Expected 4991")

# Configure seesaw pin used to read knob button presses
# The internal pull up is enabled to prevent floating input
seesaw.pin_mode(24, seesaw.INPUT_PULLUP)
button = digitalio.DigitalIO(seesaw, 24)

button_held = False

encoder = rotaryio.IncrementalEncoder(seesaw)
last_position = None

# set up the audio amp
i2c = busio.I2C(board.SCL, board.SDA)
tpa = adafruit_tpa2016.TPA2016(i2c)
tpa.max_gain = 28
tpa.fixed_gain = volume # starts at -14

# set up FM radio
# Preset stations. 8930 means 89.3 MHz, etc.
presets = [8850, 9010, 9090, 9810, 10100, 10210, 10290]
i_sidx = 2  # Starting at station with index 3

rds = tinkeringtech_rda5807m.RDSParser()
rdstext = "No rds data"

# Initialize the radio classes for use.
radio_i2c = I2CDevice(i2c, 0x11)
radio = tinkeringtech_rda5807m.Radio(radio_i2c, rds, station, 3)
radio.set_band("FM")  # Minimum frequency - 87 Mhz, max - 108 Mhz

def button_press(channel):

    global MODE

    print("Press: {}".format(channel))
    if channel == GPIO_LEFT_SWITCH:
        if MODE != "slot":
            MODE = "slot"
            slot_setup()

    elif channel == GPIO_MID_SWITCH:
        if MODE != "radio":
            MODE = "radio"
            radio_setup()


    elif channel == GPIO_RIGHT_SWITCH:
        if MODE != "clock":
            MODE = "clock"
            clock_setup()

    print("Switch to mode: {}".format(MODE))

def top_press(channel):

    global MODE

    if MODE == "slot":
        print("SPIN!")
        sio.emit('spinme', {'message': 'bar'})
        pygame.init()
        pygame.mixer.init()

        pygame.mixer.music.load('/usr/src/app/slot.wav')
        pygame.mixer.music.play()
    else:
        MODE = "slot"
        slot_setup()

def encoder_update(channel):
    print("encoder update")

def rotary_change(dir):
    global volume
    global station

    if MODE == "radio":
        # tuning
        if dir == "down":
            if station > 8810:
                station = station - 20
        else:
            if station < 10890:
                station = station + 20
        print("tuning change: {}".format(station))
        radio_tune(station)
    else:
        # volume
        if dir == "down":
            if volume > -28:
                volume = volume - 2
        else:
            if volume < 15:
                volume = volume + 2
        print("vol change: {}".format(volume))
        volume_set(volume)
    
def slot_setup():
    display_page("slot")
    sio.disconnect()
    sio.connect('http://slot')
    print("Connected to slot as {}".format(sio.sid))
    switch_audio("pi")

def clock_setup():
    display_page("slot/clock")
    sio.disconnect()
    sio.connect('http://slot')
    print("Connected to slot as {}".format(sio.sid))
    switch_audio("radio")

def radio_setup():
    display_page("slot/radio")
    sio.disconnect()
    sio.connect('http://slot')
    print("Connected to slot as {}".format(sio.sid))
    switch_audio("radio")
    time.sleep(2.5)
    radio_tune(station)

def display_page(page):
    # load page via API
    print("Requesting page {}".format(page))
    payload = {'url': page}
    r = requests.post('http://browser:5011/url', data=payload)
    print("Page request status: {}".format(r))
    print(r.content)

def switch_audio(source):
   if source == "pi":
       GPIO.output(GPIO_ANALOG_SWITCH, GPIO.LOW)
   elif source == "radio":
       GPIO.output(GPIO_ANALOG_SWITCH, GPIO.HIGH)
   else:
       print("Audio source not recognized.")

def volume_set(volume):
    tpa.fixed_gain = volume

def radio_tune(station):
    print("radio_tune")
    freq = round(station / 100, 2)
    radio.set_freq(station)
    
    sio.emit('tune', {'freq': str(freq) + " FM"})
    sio.emit('info', {'station': "No station info."})
# RDS text handle
def textHandle(rdsText):
    global rdstext
    rdstext = rdsText
    print("RDS: {}".format(rdsText))
    sio.emit('info', {'station': rdsText})

# %%%%%%%%%%%%%%%%%%%%%% START %%%%%%%%%%%%%%%%%%%%%%%%%%

print("Controller starting up.")

GPIO.add_event_detect(GPIO_TOP_SWITCH, GPIO.RISING, callback=top_press, bouncetime=DEBOUNCE)
GPIO.add_event_detect(GPIO_LEFT_SWITCH, GPIO.RISING, callback=button_press, bouncetime=DEBOUNCE)
GPIO.add_event_detect(GPIO_MID_SWITCH, GPIO.RISING, callback=button_press, bouncetime=DEBOUNCE)
GPIO.add_event_detect(GPIO_RIGHT_SWITCH, GPIO.RISING, callback=button_press, bouncetime=DEBOUNCE)
GPIO.add_event_detect(GPIO_ENC_INT, GPIO.RISING, callback=encoder_update, bouncetime=DEBOUNCE)

slot_setup()
rds.attach_text_callback(textHandle)
#time.sleep(2)
#print("switching audio hi")
#GPIO.output(GPIO_ANALOG_SWITCH, GPIO.HIGH)
#time.sleep(2)
#print("switching audio lo")
#GPIO.output(GPIO_ANALOG_SWITCH, GPIO.LOW)
#if GPIO.input(12) == 0:

last_position = 0

while True:
    #GPIO.output(5, GPIO.LOW)
    time.sleep(1)
    position = -encoder.position

    if position != last_position:
        if position < last_position:
            #print("UP ONE")
            rotary_change("up")
        else:
            #print("DOWN ONE")
            rotary_change("down")
        last_position = position
        #print("Position: {}".format(position))
    #print("pos: {}".format(encoder.position))
    #GPIO.output(5, GPIO.HIGH)
    #time.sleep(1.5)
    # check RDS
    radio.check_rds()
