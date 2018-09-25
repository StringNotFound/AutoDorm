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
import random
import colorsys

music = 0
current_data = 0
prev_vols = 0
strip_arr = np.zeros((led.LED_COUNT, 3))

# a dummy class to store state
class State:
    def __init__(self):
        pass

class Blob:
    acceleration = 0
    velocity = 0
    color = (0, 0, 0)
    color_fun = None
    start = 0
    end = 0

    opacity = 1
    opacity_decay_time = -1

    def __init__(self, color, start, end, velocity = 0, acceleration = 0):
        self.color = color
        self.start = start
        self.end = end
        self.velocity = velocity
        self.acceleration = acceleration

def UpdateBlobs(blobs, deltaTime):
    print("updating blobs")
    for blob in blobs:
        blob.velocity += blob.acceleration * deltaTime
        blob.start += blob.velocity * deltaTime
        print("new start:", blob.start)
        blob.end += blob.velocity * deltaTime
        print("new end:", blob.end)
        if blob.color_fun is not None:
            blob.color = blob.color_fun(blob, deltaTime)
        if blob.opacity_decay_time > 0:
            blob.opacity = max(0, blob.opacity - (deltaTime / blob.opacity_decay_time))

def DrawBlobs(blobs, strip, background_color=(0,0,0)):
    strip_arr[:, :] = background_color
    for blob in blobs:
        if blob.start < 0 or blob.end > led.LED_COUNT:
            continue
        start_int = int(math.ceil(blob.start))
        end_int = int(blob.end)
        color = (blob.color[0] * blob.opacity, blob.color[1] * blob.opacity, blob.color[2] * blob.opacity)

        # now we take the weighted average of the blob's color and the current color:
        strip_arr[start_int:end_int+1, :] *= 1 - blob.opacity
        strip_arr[start_int:end_int+1, :] += color

        # finally, we cover the case where the endpoints of the blob aren't evenly on a pixel
        if start_int > 0:
            # this is the percentage of the pixel before the first pixel that's covered
            pct = start_int - blob.start
            # we multiply it by the opacity of the blob
            pct *= blob.opacity
            # now we use the decay function to bring it into visually linear color space
            pct = decayFunction(pct)

            # now we use the percentage just like we would opacity
            strip_arr[start_int-1, :] *= 1 - pct
            strip_arr[start_int-1, :] += (pct * color[0], pct * color[1], pct * color[2])
        if end_int < led.LED_COUNT - 1:
            pct = blob.end - end_int
            pct *= blob.opacity
            pct = decayFunction(pct)

            strip_arr[end_int+1, :] *= 1 - pct
            strip_arr[end_int+1, :] += (pct * color[0], pct * color[1], pct * color[2])
    # display everthing
    for i in range(led.LED_COUNT):
        strip.setPixelColor(i, led.getLEDColor(tuple(strip_arr[i, :])))
    strip.show()

# given an intensity in the range [0, 1], uses weber-fechner's law to bring it into visually linear color space
def decayFunction(x):
    return 1 / (1 + math.exp(-((256 * x / 21) - 6)))

# this method is called when the audio stream needs more data
def callback(in_data, frame_count, time_info, status):
    global music
    global current_data
    data = music.readframes(frame_count)
    current_data = data
    return (data, pyaudio.paContinue)

################### song visualizers ##########################

# call as quickly as possible
#
# delta_time - the time since this function was last called
# blobs - the set of all blobs
# state - the state returned by the last call to FairyUpdateHandler (or FairyBeatHandler)
def FairyUpdateHandler(delta_time, blobs, state):
    global strip

    UpdateBlobs(blobs, delta_time)
    DrawBlobs(blobs, strip)
    return blobs, state

# handles a beat event for the fairy light
# 
# beat_duration - the time until the next beat
# beat_intensity - [0, 1], where 1 is higher intensity (controls number of lights)
# blobs - the set of all blobs
# state - the state returned by FairyUpdateHandler
def FairyBeatHandler(beat_duration, beat_intensity, blobs, state):
    global primary_color

    # first, we clean up the blobs by removing those who are dead
    blobs = [b for b in blobs if b.opacity != 0]

    # now we add more new blobs
    num_blobs = int(60 * beat_intensity)
    for _ in range(num_blobs):
        posn = random.randint(0, led.LED_COUNT)
        color = colors[random.randint(0, len(colors)-1)]
        blob = Blob(color, posn, posn)
        blob.opacity = random.uniform(0.7, 1)
        blob.opacity_decay_time = beat_duration * random.uniform(0.7, 1.1)
        blobs.append(blob)
    return blobs, state

def StrobeUpdateHandler(delta_time, blobs, state):
    global strip

    if state is None:
        state = State()
        state.color = (1, 0, 0)
        state.isOn = True

    if state.isOn:
        color = led.getLEDColor(state.color)
        state.isOn = False
    else:
        color = led.getLEDColor((0, 0, 0))
        state.isOn = True

    color = led.getLEDColor((0, 0, 0))
    for i in range(led.LED_COUNT):
        strip.setPixelColor(i, color)
    strip.show()

def StrobeBeatHandler(beat_duration, beat_intensity, blobs, state):
    state.color = getNextColor(state.color)
    return (blobs, state)

def LevelsUpdateHandler(delta_time, blobs, state):
    global strip

    if state is None:
        state = State()
        state.beatLevel = 0
        state.fadeTime = 1
    state.beatLevel -= delta_time / state.fadeTime
    state.beatLevel = max(0, state.beatLevel)
    led.setBass(strip, beat_level)
    led.setTop(strip, np.mean(prev_vols))

def LevelsBeatHandler(beat_duration, beat_intensity, blobs, state):
    state.beatLevel = beat_intensity
    state.fadeTime = beat_duration
    return (blobs, state)

def PulseUpdateHandler(delta_time, blobs, state):
    global strip

    if state is None:
        state = State()
        state.color = (0, 0, 1)
    UpdateBlobs(blobs, delta_time)
    DrawBlobs(blobs, strip)
    return blobs, state

def PulseBeatHandler(beat_duration, beat_intensity, blobs, state):
    blob = Blob(state.color, 0, led.LED_COUNT - 1)
    blob.opacity_decay_time = beat_duration * 0.7
    blobs.append(blob)
    return (blobs, state)

################### helper methods ############################

def getNextColor(c):
    hsv = colorsys.rgb_to_hsv(c[0], c[1], c[2])
    return colorsys.hsv_to_rgb(hsv[0] + 1/6, hsv[1], hsv[2])

#################### "main" methods ###########################

def getHandler(intensity):
    low_intensity = [(PulseBeatHandler, PulseUpdateHandler), (FairyBeatHandler, FairyUpdateHandler)]
    mid_intensity = [(LevelsBeatHandler, LevelsUpdateHandler)]
    high_intensity = [(StrobeBeatHandler, StrobeUpdateHandler)]

    if intensity == -1:
        return low_intensity[random.randint(0, len(low_intensity)-1)]
    if intensity == 0:
        return mid_intensity[random.randint(0, len(mid_intensity)-1)]
    if intensity == 1:
        return high_intensity[random.randint(0, len(high_intensity)-1)]

# call this method to play a song
# strip: a reference to the strip object
# filename: the filepath of the song to play
# beat_file: the filepath containing the stored beats of the song
def play_song(strip, song_file, beat_file):
    global music
    global current_data
    global prev_vols

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

    last_update = start_time

    loudness = Loudness()
    memory_size = 5
    prev_vols = [0 for _ in range(memory_size)]
    cur_idx = 0
    cur_beat_idx = 0

    beatHandler = None
    updateHandler = None
    blobs = []
    state = None

    # wait for stream to finish
    while stream.is_active():
        continue
        cur_volume = loudness(current_data)
        prev_vols[cur_idx, 1] = cur_volume
        cur_idx = (cur_idx + 1) % memory_size

        deltaTime = time.time() - last_update
        last_update += deltaTime

        if beatHandler is None or updateHandler is None:
            getHandler(0)

        updateHandler(delta_time, blobs, state)

        if cur_beat_idx < len(beats) and time.time() - start_time >= beats[cur_beat_idx] - offset:
            cur_beat_idx += 1
            # if this isn't the last beat
            if cur_beat_idx + 1 < len(beats):
                beatHandler(beats[cur_beat_idx + 1] - beats[cur_beat_idx], max(prev_vols), blobs, state)
            else:
                beatHandler(1, max(prev_vols), blobs, state)

        time.sleep(0.001)

    # stop stream
    stream.stop_stream()
    stream.close()
    music.close()

    # close PyAudio
    p.terminate()

def main():
    if len(sys.argv) < 2:
        print("Plays a wave file.\n\nUsage: %s filename.wav beat_file.txt" % sys.argv[0])
        sys.exit(-1)

    # instantiate a strip
    strip = led.getStrip()

    play_song(strip, sys.argv[1], sys.argv[2])

def test_blobs():
    print("testing blobs...")
    strip = led.getStrip()
    blob1 = Blob((1, 0, 0), 1, 1, 1)
    blob2 = Blob((0, 1, 0), 8, 8, -1)
    blobs = [blob1, blob2]
    print(blobs)

    last_update = time.time()
    while True:
        curtime = time.time()
        delta_time = curtime - last_update
        last_update = curtime
        UpdateBlobs(blobs, delta_time)
        DrawBlobs(blobs, strip)

main()
