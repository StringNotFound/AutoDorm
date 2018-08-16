"""PyAudio Example: Play a wave file (callback version)."""

import pyaudio
import wave
import time
import sys
import numpy as np
import thread
import led_control as led
from neopixel import *

music = 0
current_data = 0
playing = False
start_time = 0
strip = led.getStrip()

# this method is called when the audio stream needs more data
def callback(in_data, frame_count, time_info, status):
    global music
    global current_data
    data = music.readframes(frame_count)
    current_data = data
    return (data, pyaudio.paContinue)

def sick_beats():
    global playing
    global start_time
    global current_data

    offset = 0.00

    # these were created in a preprocessing step
    beats = np.load("beats.npy")
    print(beats.shape)

    # wait for the song to start
    while not playing:
        pass

    assert(start_time != 0)

    num_beats = beats.shape[1]
    current_beat = 0

    while playing:
        if current_beat < num_beats and time.time() - start_time >= beats[0, current_beat] - offset:
            print("beat! ", beats[1, current_beat])
            #print('beat')
            current_beat += 1
            #print(beats[0, current_beat])
            #led.flash(strip, 0.1, Color(0, 0, 255))
            led.setBass(strip, beats[1, current_beat])
        # do the other averaging stuff
        time.sleep(0.001)
    print("stopped playing; exiting secondary thread")


def main():
    global music
    global playing
    global start_time

    if len(sys.argv) < 2:
        print("Plays a wave file.\n\nUsage: %s filename.wav" % sys.argv[0])
        sys.exit(-1)

    music = wave.open(sys.argv[1], 'rb')

    # instantiate PyAudio
    p = pyaudio.PyAudio()

    # open stream using callback
    stream = p.open(format=p.get_format_from_width(music.getsampwidth()),
                    channels=music.getnchannels(),
                    rate=music.getframerate(),
                    output=True,
                    stream_callback=callback)

    thread.start_new_thread(sick_beats, ())

    # start the stream
    stream.start_stream()
    playing = True
    start_time = time.time()

    # wait for stream to finish
    while stream.is_active():
        time.sleep(0.1)

    # stop stream
    stream.stop_stream()
    stream.close()
    music.close()
    playing = False


    # close PyAudio
    p.terminate()

main()
