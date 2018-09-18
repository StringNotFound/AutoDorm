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

# LED strip configuration:
LED_COUNT      = 243      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

L = 100
R = 143
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
        print(percentage_done)
        on_left = int(mid - lenl * percentage_done)
        on_right = int(mid + lenl * percentage_done)
        for i in range(on_left, on_right):
            dist = min(i - on_left, abs(i - mid), on_right - i);
            strip.setPixelColor(i, Color(0, 0, 255))
        # make the strip softer
        for i in range(on_left, 30):
            strip.setPixelColor(i, Color(0, 0, i / 6 * 255))
        strip.show()
        current_time = time.time()
    for i in range(L, R):
        strip.setPixelColor(i, Color(0, 0, 255))
    strip.show()

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
def getBassColor(amt):
    sat = 1
    if amt > .9:
        sat = 1 - (amt - 0.9) / 0.1
    c = colorsys.hsv_to_rgb(getHue(amt, 2/3.0, 1/6.0), sat, 1)
    return getLEDColor(c)


# amt \in [0 1]
def setBass(strip, amt):
    amt = min(1, amt)
    print(amt)
    lenr = LED_COUNT - R

    left = int(amt * L)
    right = LED_COUNT - int(amt * lenr)

    color = getBassColor(amt)

    for i in range(0, left):
        #color = getBassColor(amt * float(i) / left)
        strip.setPixelColor(i, color)
    for i in range(left, right):
        strip.setPixelColor(i, Color(0, 0, 0))
    for i in range(right, LED_COUNT):
        #color = getBassColor(amt * float(LED_COUNT - i) / lenr)
        strip.setPixelColor(i, color)
    strip.show()


def testBassColors(strip):
    clear(strip)
    for i in range(0, L):
        color = getBassColor(float(i) / L)
        strip.setPixelColor(i, color)
    strip.show()





# Define functions which animate LEDs in various ways.
def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)

def theaterChase(strip, color, wait_ms=50, iterations=10):
    """Movie theater light style chaser animation."""
    for j in range(iterations):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, color)
            strip.show()
            time.sleep(wait_ms/1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, 0)

def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)

def rainbow(strip, wait_ms=20, iterations=1):
    """Draw rainbow that fades across all pixels at once."""
    for j in range(256*iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((i+j) & 255))
        strip.show()
        time.sleep(wait_ms/1000.0)

def rainbowCycle(strip, wait_ms=20, iterations=5):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for j in range(256*iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((int(i * 256 / strip.numPixels()) + j) & 255))
        strip.show()
        time.sleep(wait_ms/1000.0)

def theaterChaseRainbow(strip, wait_ms=50):
    """Rainbow movie theater light style chaser animation."""
    for j in range(256):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, wheel((i+j) % 255))
            strip.show()
            time.sleep(wait_ms/1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, 0)

def setColor(strip, color, end=LED_COUNT):
    for i in range(end):
        strip.setPixelColor(i, color)
    strip.show()

def setRGBColor(strip, color, end=LED_COUNT):
    color = getLEDColor(color)
    setColor(strip, color, end)

def flash(strip, duration, color, old_color=Color(0,0,0)):
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


# Main program logic follows:
if __name__ == '__main__':

    strip = getStrip()

    jarvis_wake(strip, 0.5)
    #graphSin(strip)
    #pulse(strip, 5, 2.5, (0, 149, 255), (0, 0, 255))
    theaterChaseRainbow(strip)

    #setColor(strip, Color(0, 0, 0))
    #flash(strip, .25, Color(0, 255, 0))
    #setColor(strip, Color(0, 0, 0))
    #for i in range(255):
        #setBass(strip, i / 255.0)
        #time.sleep(0.01)
    #setBass(strip, 1)
   # setColor(strip, Color(255, 0, 0))
    #theaterChaseRainbow(strip)
    clear(strip)

    #colorWipe(strip, Color(0, 255, 0))
    #testBassColors(strip)
