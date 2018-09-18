"""PyAudio Example: Play a wave file (callback version)."""

import pyaudio
import wave
import time
import sys
import numpy as np
import thread
import led_control as led
from essentia.standard import Loudness
from neopixel import *

music = 0
current_data = 0

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

    print("stopped playing; exiting secondary thread")


def play_song(strip, filename):
    global music
    global current_data

    music = wave.open(filename, 'rb')

    # instantiate PyAudio
    p = pyaudio.PyAudio()

    # open stream using callback
    stream = p.open(format=p.get_format_from_width(music.getsampwidth()),
                    channels=music.getnchannels(),
                    rate=music.getframerate(),
                    output=True,
                    stream_callback=callback)

    # start the stream
    stream.start_stream()
    start_time = time.time()

    # the offset of the beats (in seconds)
    offset = 0.00

    # these were created in a preprocessing step
    beats = np.load("beats.npy")
    num_beats = beats.shape[1]
    current_beat = 0

    # how quickly do the beat effects fade (in seconds)?
    fade_time = 1.0
    last_update = 0
    # between 0 and 1
    beat_level = 0

    loudness = Loudness()
    memory_size = 5
    prev_vols = np.zeros((memory_size, 1))
    cur_idx = 0

    # wait for stream to finish
    while stream.is_active():
        cur_volume = loudness(current_data)
        prev_vols[cur_idx, 1] = cur_volume
        cur_idx = (cur_idx + 1) % memory_size

        if current_beat < num_beats and time.time() - start_time >= beats[0, current_beat] - offset:
            #print("beat! ", beats[1, current_beat])
            beat_level = beats[1, current_beat]
            current_beat += 1
        #print("setting beat level to ", beat_level)
        led.setBass(strip, beat_level)
        beat_level -= fade_time * (time.time() - last_update)
        beat_level = max(beat_level, 0)
        last_update = time.time()

        # do the other averaging stuff
        time.sleep(0.001)

    # stop stream
    stream.stop_stream()
    stream.close()
    music.close()

    # close PyAudio
    p.terminate()

def main():
    if len(sys.argv) < 2:
        print("Plays a wave file.\n\nUsage: %s filename.wav" % sys.argv[0])
        sys.exit(-1)

    # instantiate a strip
    strip = led.getStrip()

    play_song(strip, sys.argv[1])

main()
