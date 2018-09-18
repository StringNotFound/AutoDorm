<<<<<<< HEAD
# External module imports
import RPi.GPIO as GPIO
import time
import led_control as ledc

"""
Pin list:

    GND - black wire) - 6
    LED Control - green - GPIO18 - 12
    Computer - purple - GPIO17 - 11
    Motor 1 - yellow - GPIO23 - 16
    Motor 2 - orange - GPIO24 - 18
    Power Strip - blue - GPIO22 - 15
"""

# define wire locations
w_led = 18
w_comp = 17
w_motor_1 = 23
w_motor_2 = 24
w_power_strip = 22

# other parameters
light_delay = 0.1

def initialize():
    global w_comp
    global w_motor_1
    global w_motor_2
    global w_power_strip

    GPIO.setmode(GPIO.BCM)
    GPIO.setup([w_comp, w_motor_1, w_motor_2, w_power_strip], GPIO.OUT)
    GPIO.output([w_comp, w_motor_1, w_motor_2, w_power_strip], GPIO.LOW)

def cleanup():
    GPIO.cleanup()

def turn_on_lights():
    global w_motor_1
    global w_motor_2
    global light_delay

    GPIO.output(w_motor_1, GPIO.LOW)
    GPIO.output(w_motor_2, GPIO.HIGH)
    time.sleep(light_delay)
    GPIO.output(w_motor_1, GPIO.HIGH)
    GPIO.output(w_motor_2, GPIO.LOW)
    time.sleep(light_delay)
    GPIO.output(w_motor_1, GPIO.LOW)

def turn_off_lights():
    global w_motor_1
    global w_motor_2
    global light_delay

    GPIO.output(w_motor_2, GPIO.LOW)
    GPIO.output(w_motor_1, GPIO.HIGH)
    time.sleep(light_delay)
    GPIO.output(w_motor_2, GPIO.HIGH)
    GPIO.output(w_motor_1, GPIO.LOW)
    time.sleep(light_delay)
    GPIO.output(w_motor_2, GPIO.LOW)

def set_power_strip(state):
    global w_power_strip

    if state == True:
        GPIO.output(w_power_strip, GPIO.HIGH)
    else:
        GPIO.output(w_power_strip, GPIO.LOW)

def toggle_computer():
    global w_comp

    GPIO.output(w_comp, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(w_comp, GPIO.LOW)

"""
Given an (object, action) pair, attempts to execute the command. May throw an
error if the pairing is invalid or the command is not successfully executed
"""
def execute_command(cmd, strip):
    print(cmd)
    obj = cmd[0]
    act = cmd[1]

    if obj in {'light', 'lights'}:
        if act == 'off':
            turn_off_lights()
            return True
        if act == 'on':
            turn_on_lights()
            return True
        return False

    if obj in {'computer'}:
        if act in {'off', 'on'}:
            toggle_computer()
            return True
        return False

    if obj in {'fan'}:
        if act == 'off':
            set_power_strip(False)
            return True
        if act == 'on':
            set_power_strip(True)
            return True
        return False

    if obj in {'leds', 'led'}:
        if act == 'off':
            ledc.clear(strip)
            return True

    if obj in {'leds', 'led', 'color'}:
        if act == 'red':
            ledc.setRGBColor(strip, (1, 0, 0))
            return True
        if act == 'orange':
            ledc.setRGBColor(strip, (1, 0.5, 0))
            return True
        if act == 'yellow':
            ledc.setRGBColor(strip, (1, 1, 0))
            return True
        if act == 'green':
            ledc.setRGBColor(strip, (0, 1, 0))
            return True
        if act == 'blue':
            ledc.setRGBColor(strip, (0, 0, 1))
            return True
        if act == 'indigo':
            ledc.setRGBColor(strip, (0, 0, 0.5))
            return True
        if act == 'purple':
            ledc.setRGBColor(strip, (1, 0, 1))
            return True
        if act == 'pink':
            ledc.setRGBColor(strip, (1, 0, 0.5))
            return True
        if act == 'white':
            ledc.setRGBColor(strip, (1, 1, 1))
            return True
        return False
