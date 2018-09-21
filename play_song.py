import pyaudio
import wave
import time
import sys
import numpy as np
import thread
import led_control as led
from essentia.standard import Loudness
from neopixel import *
import math

music = 0
current_data = 0
strip_arr = np.zeros((led_control.LED_COUNT, 3))

class Blob:
    acceleration = 0
    velocity = 0
    color = (0, 0, 0)
    color_fun = None
    start = 0
    end = 0
    size_fun = None

    def __init__(self, color, start, end):
        self.position = posn
        self.color = color
        self.start = start
        self.end = end

def UpdateBlobs(blobs, deltaTime):
    for blob in blobs:
        blob.velocity += blob.acceleration * deltaTime
        blob.start += blob.velocity * deltaTime
        blob.end += blob.velocity * deltaTime
        if blob.color_fun is not None:
            blob.color = blob.color_fun(blob, deltaTime)
        if blob.size_fun is not None:
            blob.size = blob.size_fun(blob, deltaTime)

def DrawBlobs(blobs, strip, background_color=(0,0,0)):
    strip_arr[:, :] = background_color
    for blob in blobs:
        start_int = int(math.ceil(blob.start))
        end_int = int(blob.end)
        color = blob.color
        strip_arr[start_int:end_int, :] = color
        if start_int > 0:
            pct = start_int - start
            strip_arr[start_int-1, :] = (pct * color[0], pct * color[1], pct * color[2])
        if end_int < led_control.LED_COUNT - 1:
            pct = end - end_int
            strip_arr[end+1, :] = (pct * color[0], pct * color[1], pct * color[2])
    for i in range(led_control.LED_COUNT):
        strip.setPixelColor(i, led_control.getLEDColor(tuple(strip_arr[i, :])))

# this method is called when the audio stream needs more data
def callback(in_data, frame_count, time_info, status):
    global music
    global current_data
    data = music.readframes(frame_count)
    current_data = data
    return (data, pyaudio.paContinue)

# call this method to play a song
# strip: a reference to the strip object
# filename: the filepath of the song to play
# beat_file: the filepath containing the stored beats of the song
def play_song(strip, song_file, beat_file):
    global music
    global current_data

    music = wave.open(song_file, 'rb')
    beat_file = open(beat_file)
    beats = [float(x.strip()) for x in beat_file]

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

    # how quickly do the beat effects fade (in seconds)?
    fade_time = 1.0
    last_update = 0
    # between 0 and 1
    beat_level = 0

    loudness = Loudness()
    memory_size = 5
    prev_vols = [0 for _ in range(memory_size)]
    cur_idx = 0

    # wait for stream to finish
    while stream.is_active():
        cur_volume = loudness(current_data)
        prev_vols[cur_idx, 1] = cur_volume
        cur_idx = (cur_idx + 1) % memory_size

        if current_beat < num_beats and time.time() - start_time >= beats[current_beat] - offset:
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
