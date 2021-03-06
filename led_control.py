#!/usr/bin/env python3
# NeoPixel library strandtest example
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.

import time
from neopixel import *
import argparse
import math
import colorsys
import threading

# set this command and broadcast on this cond var to activate a led effect
"""
Valid commands:
    activate (arg0 = sec)
    flash (arg0 = (r, g, b))
"""
command = ""
arg0 = 0
arg1 = 0
condvar = 0

# LED strip configuration:
LED_COUNT      = 238      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

L = 89
R = 148
mid = (L + R) / 2

def jarvis_wake(strip, seconds):
    L = 0
    R = LED_COUNT
    lenl = mid - L
    lenr = mid - R
    start_time = time.time()
    current_time = start_time
    while current_time - start_time < seconds:
        percentage_done = (current_time - start_time) / float(seconds)
        on_left = int(mid - lenl * percentage_done)
        on_right = int(mid + lenl * percentage_done)
        for i in range(on_left, on_right):
            strip.setPixelColor(i, Color(0, 0, 255))
        # make the strip softer
        for i in range(on_left, 30):
            strip.setPixelColor(i, Color(0, 0, i / 6 * 255))
        strip.show()
        current_time = time.time()
    for i in range(L, R):
        strip.setPixelColor(i, Color(0, 0, 255))
    strip.show()

def jarvis_sleep(strip, seconds):
    L = 0
    R = LED_COUNT
    lenl = mid - L
    lenr = mid - R
    start_time = time.time()
    current_time = start_time
    while current_time - start_time < seconds:
        percentage_done = (current_time - start_time) / float(seconds)
        off_left = int(lenl * percentage_done)
        off_right = int(lenr * percentage_done)
        for i in range(L, off_left):
            strip.setPixelColor(i, Color(0, 0, 0))
        for i in range(R-off_left, R+1):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()
        current_time = time.time()
    clear(strip)

def blobs(strip, blob_speed, background_color, blob_color, num_blobs=3):
    pass

def pulse(strip, seconds, frequency, c1, c2):
    start_time = time.time()
    current_time = start_time
    prev_time = start_time
    percent = 0.0
    increase = True
    while current_time - start_time < seconds:
        i = (current_time - prev_time) / frequency

        if increase:
            percent += i
        else:
            percent -= i

        if percent >= 1:
            percent = 1
            increase = False
        if percent <= 0:
            percent = 0
            increase = True

        for i in range(0, LED_COUNT):
            strip.setPixelColor(i, Color(int(c1[0] * percent + c2[0] * (1 - percent)), int(c1[1] * percent + c2[1] * (1 - percent)), int(c1[2] * percent + c2[2] * (1 - percent))))
        strip.show()

        prev_time = current_time
        current_time = time.time()

# given an RGB tuple, converts it into a color object
def getLEDColor(c):
    return Color(int(c[1] * 255), int(c[0] * 255), int(c[2] * 255))

# all parameters should be in [0, 1]
# linearly interpolates between start and end hue, wrapping clockwise around the wheel
def getHue(amt, startHue, endHue):
    if startHue < endHue:
        return amt * (endHue - startHue) + startHue
    # otherwise, we need to wrap around
    endHue += 1
    # now startHue < endHue
    hue = amt * (endHue - startHue) + startHue
    if hue > 1:
        hue -= 1
    return hue

# amt \in [0, 1]
# returns an rgb tuple
def getBassColor(amt):
    sat = 1
    if amt > .9:
        sat = 1 - (amt - 0.9) / 0.1
    c = colorsys.hsv_to_rgb(getHue(amt, 2/3.0, 1/6.0), sat, 1)
    return c

# amt \in [0 1]
def setLevels(strip, top, bot):
    global L
    global R
    global mid

    top = min(1, top)
    bot = min(1, bot)

    lenr = LED_COUNT - R
    left = int(bot * L)
    right = LED_COUNT - int(bot * lenr)

    bassColor = getLEDColor(getBassColor(bot))
    off = Color(0, 0, 0)

    for i in range(0, left):
        #color = getBassColor(amt * float(i) / left)
        strip.setPixelColor(i, bassColor)
    for i in range(left, right):
        strip.setPixelColor(i, off)
    for i in range(right, LED_COUNT):
        #color = getBassColor(amt * float(LED_COUNT - i) / lenr)
        strip.setPixelColor(i, bassColor)

    lenmid = int(top * (R - L))
    topColor = getLEDColor(getBassColor(top))

    for i in range(int(mid - lenmid / 2), int(mid + lenmid / 2)):
        strip.setPixelColor(i, topColor)
    strip.show()

def setInvTop(strip, amt):
    global L
    global R
    global mid

    amt = min(1, amt)

    lenl = int(amt * (mid - L))
    lenr = int(amt * (R - mid))

    color = getLEDColor(getBassColor(amt))
    off = Color(0, 0, 0)

    for i in range(L, L + lenl):
        strip.setPixelColor(i, color)
    for i in range(L + lenl, R - lenr):
        strip.setPixelColor(i, off)
    for i in range(R - lenr, R):
        strip.setPixelColor(i, color)

    strip.show()

def setColor(strip, color, end=LED_COUNT):
    for i in range(end):
        strip.setPixelColor(i, color)
    strip.show()

def setRGBColor(strip, color, end=LED_COUNT):
    color = getLEDColor(color)
    setColor(strip, color, end)

def flash(strip, duration, color, old_color=(0,0,0)):
    color = getLEDColor(color)
    old_color = getLEDColor(old_color)
    setColor(strip, color)
    time.sleep(duration)
    setColor(strip, old_color)
    strip.show()

def clear(strip):
    setColor(strip, Color(0, 0, 0))

# call this once to get a strip object
def getStrip():
    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    # Intialize the library (must be called once before other functions).
    strip.begin()
    return strip

# this thread enables the concurrent led effects
# (currently unused)
def ledThread(cond, strip=None):
    global condvar
    global command
    global arg0
    global arg1

    command = ""
    condvar = cond
    if strip == None:
        strip = getStrip()

    condvar.acquire()
    while True:
        # now we wait for a command
        while command == "":
            print("LED_THREAD: Waiting for broadcast")
            condvar.wait()
            print("LED_THREAD: Woken up")
        print("LED_THREAD: Received command!")

        if command == "exit":
            print("LED_THREAD: exiting...")
            return

        active = True
        if command == "flash":
            print("LED_THREAD: Flash", str(arg0))
            flash(strip, 0.5, getLEDColor(arg0))
        if command == "activate":
            print("LED_THREAD: Activate")
            jarvis_wake(strip, arg0)
            #pulse(strip, 5, 2.5, (0, 149, 255), (0, 0, 255))
        if command == "clear":
            print("LED_THREAD: Clear")
            clear(strip)
        command = ""
        arg0 = 0
        arg1 = 0


# Main program logic follows:
if __name__ == '__main__':

    strip = getStrip()

    #jarvis_wake(strip, 0.5)
    #setBass(strip, 1)
    #setLevels(strip, 0.1, 0.1)
    #jarvis_sleep(strip, 0.5)
    #graphSin(strip)
    #pulse(strip, 5, 2.5, (0, 149, 255), (0, 0, 255))
    #theaterChaseRainbow(strip)

    #setColor(strip, Color(0, 0, 0))
    #flash(strip, .25, Color(0, 255, 0))
    #setColor(strip, Color(0, 0, 0))
    #for i in range(255):
        #setBass(strip, i / 255.0)
        #time.sleep(0.01)
   # setColor(strip, Color(255, 0, 0))
    #theaterChaseRainbow(strip)
    clear(strip)

    #colorWipe(strip, Color(0, 255, 0))
    #testBassColors(strip)
