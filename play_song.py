import pyaudio
import wave
import time
import sys
import numpy as np
import thread
import led_control as led
from neopixel import *
import math
import random
import colorsys
import audioop
from multiprocessing import Process, Array, Value
import os

strip_arr = np.zeros((led.LED_COUNT, 3))
strip = None

# a dummy class to store state
class State:
    color = 0
    isOn = False

    beatLevel = 0
    fadeTime = 0

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
    for blob in blobs:
        blob.velocity += blob.acceleration * deltaTime
        blob.start += blob.velocity * deltaTime
        blob.end += blob.velocity * deltaTime
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


################### song visualizers ##########################

# call as quickly as possible
#
# delta_time - the time since this function was last called
# blobs - the set of all blobs
# state - the state returned by the last call to FairyUpdateHandler (or FairyBeatHandler)
def FairyUpdateHandler(delta_time, avg_vol, blobs, state):
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
        #color = colors[random.randint(0, len(colors)-1)]
        color = (1, 0, 0)
        blob = Blob(color, posn, posn)
        blob.opacity = random.uniform(0.7, 1)
        blob.opacity_decay_time = beat_duration * random.uniform(0.7, 1.1)
        blobs.append(blob)
    return blobs, state

def StrobeUpdateHandler(delta_time, avg_vol, blobs, state):
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
    return blobs, state

def StrobeBeatHandler(beat_duration, beat_intensity, blobs, state):
    state.color = getNextColor(state.color)
    return (blobs, state)

def LevelsUpdateHandler(delta_time, avg_vol, blobs, state):
    global strip

    if state is None:
        state = State()
        state.beatLevel = 0
        state.fadeTime = 5.0
    state.beatLevel = state.beatLevel - (delta_time / state.fadeTime)
    state.beatLevel = max(0, state.beatLevel)
    # set (top, bot)
    led.setLevels(strip, avg_vol, state.beatLevel)
    return blobs, state

def LevelsBeatHandler(beat_duration, beat_intensity, blobs, state):
    state.beatLevel = beat_intensity
    state.fadeTime = beat_duration
    return (blobs, state)

def PulseUpdateHandler(delta_time, avg_vol, blobs, state):
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

# NOTE: These variables are only accurate in the playAudio child process
# the last time the callback was called
last_update = 0
# the number of frames that we've read
num_frames = 0
# the wav music file
music = None
# the pipe
pipe = None

# callback is used in playAudio
def callback(in_data, frame_count, time_info, status):
    global last_update
    global num_frames
    global music
    global pipe

    num_frames = num_frames + frame_count
    last_update = time.time()
    pipe.value = num_frames / 1024

    data = music.readframes(frame_count)
    return (data, pyaudio.paContinue)

def playAudio(wave_stream, pya, cur_vol_idx):
    global last_update
    global num_frames
    global music
    global pipe
    # set the thread priority quite high
    os.nice(-19)

    music = wave_stream
    pipe = cur_vol_idx

    # open stream
    stream = pya.open(format=pya.get_format_from_width(music.getsampwidth()),
                    channels=music.getnchannels(),
                    rate=music.getframerate(),
                    output=True,
                    stream_callback=callback)
    stream.start_stream()

    # the number of frames that we've read
    while stream.is_active():
        time.sleep(0.05)
        #cur_vol_idx.value = num_frames / 1024
        # the stream sometimes hangs. We need to restart it
        if time.time() - last_update > 0.1:
            print("restarting stream!")
            stream.close()
            stream = pya.open(format=pya.get_format_from_width(music.getsampwidth()),
                            channels=music.getnchannels(),
                            rate=music.getframerate(),
                            output=True,
                            stream_callback=callback)
            stream.start_stream()


    # stop stream
    stream.stop_stream()
    stream.close()

# given a music file, returns the volume at every 1024 frames
def getAllVols(music):
    vols = []
    num_frames = 1024
    data = music.readframes(num_frames)
    while len(data) > 0:
        vols.append(audioop.rms(data, 2))
        data = music.readframes(num_frames)
    return vols

def getHandler(intensity):
    #low_intensity = [(PulseBeatHandler, PulseUpdateHandler), (FairyBeatHandler, FairyUpdateHandler)]
    low_intensity = [(FairyBeatHandler, FairyUpdateHandler)]
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
def play_song(strip, song_name, pya):

    music = wave.open('music/' + song_file + '.wav', 'rb')
    vols = np.array(getAllVols(music))
    # normalize
    vols = vols / float(np.max(vols))
    # getAllVols uses up music, so we need to reopen the file
    music = wave.open('music/' + song_file + '.wav', 'rb')
    framerate = music.getframerate()

    beat_file = open('music/' + song_file + '.txt')
    beats = [float(x.strip()) for x in beat_file]

    start_time = time.time()
    last_update = start_time

    memory_size = 5
    cur_beat_idx = 0
    offset = 0

    beatHandler = None
    updateHandler = None
    blobs = []
    state = None

    cur_vol_idx = Value('i', 0)
    audioProc = Process(target=playAudio, args=(music, pya, cur_vol_idx))
    audioProc.start()

    # wait for stream to finish
    while cur_beat_idx < len(beats) and cur_vol_idx.value + 1 < vols.shape[0]:
        delta_time = time.time() - last_update
        last_update += delta_time

        if beatHandler is None or updateHandler is None:
            (beatHandler, updateHandler) = getHandler(0)

        (blobs, state) = updateHandler(delta_time, vols[cur_vol_idx.value], blobs, state)

        music_time = cur_vol_idx.value * 1024.0 / framerate
        if music_time >= beats[cur_beat_idx] + offset:
            #print("beat")
            cur_beat_idx += 1
            # if this isn't the last beat
            if cur_beat_idx + 1 < len(beats):
                (blobs, state) = beatHandler(beats[cur_beat_idx + 1] - beats[cur_beat_idx],
                                             np.max(vols[max(cur_vol_idx.value - 5, 0):cur_vol_idx.value+1]), blobs, state)
            else:
                (blobs, state) = beatHandler(1, np.max(vols[max(cur_vol_idx.value - 5, 0):cur_vol_idx.value]), blobs, state)

        time.sleep(0.01)

    audioProc.join()

def main():
    global strip

    if len(sys.argv) < 2:
        print("Plays a wave file.\n\nUsage: %s song_name" % sys.argv[0])
        sys.exit(-1)

    # instantiate a strip
    strip = led.getStrip()

    # instantiate pyaudio
    p = pyaudio.PyAudio()

    play_song(strip, sys.argv[1], p)

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
