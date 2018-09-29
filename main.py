import snowboydecoder
import sys
import signal
import time
import io
import pyaudio
import wave
import threading
import thread

# import our custom natural language processing algorithm
import nlp
# allows us to execute commands
import commands
# controls leds
import led_control

# Imports the Google Cloud client library
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

interrupt = False
LEDStrip = 0

# Instantiates a google speech client
client = speech.SpeechClient()

# records a 5 second clip of the user speaking
def record():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    RECORD_SECONDS = 5
    WAVE_OUTPUT_FILENAME = "output.wav"

    # technically, this is the KeywordDetector's instance of PyAudio, but
    # we closed the steam before calling the handler
    global pya

    #pya = pyaudio.PyAudio()

    stream = pya.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("* recording")

    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("* done recording")

    stream.stop_stream()
    stream.close()
    # we definitely don't want to close this PyAudio instance, since we don't own it
    # (it's closed in detector.terminate())
    #pya.terminate()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(pya.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    return WAVE_OUTPUT_FILENAME

# converts the given wav file to text using google's speech API
def wav2text(file_name):
    global client

    # Loads the audio into memory
    with io.open(file_name, 'rb') as audio_file:
        content = audio_file.read()
        audio = types.RecognitionAudio(content=content)

    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code='en-US')

    # Detects speech in the audio file
    response = client.recognize(config, audio)

    #for result in response.results:
        #print('Transcript: {}'.format(result.alternatives[0].transcript))
    if len(response.results) == 0:
        return ""
    else:
        return response.results[0].alternatives[0].transcript;

def get_cmds():
    print('recording file')
    file_name = record()
    print('recorded file')
    # what the user said
    print('converting recorded file to text')
    spoken_text = wav2text(file_name)
    print(spoken_text)
    print('parsing text')
    cmds = nlp.parse_phrase(spoken_text)
    return cmds


###########################################################################

# called when CTRL-C is pressed
def signal_handler(signal, frame):
    global interrupt
    interrupt = True

# called when the keyword is spoken
def keyword_handler():
    global LEDStrip
    global pya

    # display the wakeup thing
    led_control.jarvis_wake(LEDStrip, 0.5)

    print("keyword handler called")

    try:
        cmds = get_cmds()
        led_control.jarvis_sleep(LEDStrip, 0.5)
        for cmd in cmds:
            commands.execute_command(cmd, LEDStrip, pya)
    except SyntaxError:
        # if there's a problem with the parsing, it's an automatic failure
        led_control.flash(LEDStrip, 0.5, (1, 0, 0))

# called to determine whether the detector should exit
def interrupt_callback():
    global interrupt
    # terminate if the keyword was spoken or if CTRL-C was pressed
    return interrupt

def main():
    global interrupt
    global pya
    global LEDStrip
    global led_cond

    if len(sys.argv) == 1:
        print("Error: need to specify model name")
        print("Usage: python demo.py your.model")
        sys.exit(-1)

    # initialize the GPIO pins
    commands.initialize()

    LEDStrip = led_control.getStrip()

    model = sys.argv[1]
    # capture SIGINT signal, e.g., Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # get the detector instance
    detector = snowboydecoder.HotwordDetector(model, sensitivity=0.5)
    # the detector instiantiates PyAudio(), but we need it for our record function
    pya = detector.audio

    print('Listening... Press Ctrl+C to exit')

    # listen for the keyword
    detector.start(detected_callback=keyword_handler,
            interrupt_check=interrupt_callback,
            sleep_time=0.03)

    print('\nCtrl+C received... exiting')
    detector.terminate()


main()
