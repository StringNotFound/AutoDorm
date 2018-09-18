def set_lights(on=False):
    if on:
        print("turning on lights")
    else:
        print("turning off lights")

def set_fan(on=False):
    if on:
        print("turning on fan")
    else:
        print("turning off fan")

def toggle_computer():
    print("'pressing' computer power button")

def set_blinds(lower=False):
    if lower:
        print("raising blinds")
    else:
        print("lowering blinds")


"""
Given an (object, action) pair, attempts to execute the command. May throw an
error if the pairing is invalid or the command is not successfully executed
"""
def execute_command(cmd):
    print(cmd)
