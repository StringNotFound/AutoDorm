import numpy as np

# matplotlib for displaying the output
import matplotlib.pyplot as plt
import matplotlib.style as ms
ms.use('seaborn-muted')
#matplotlib inline

# and IPython.display for audio output
import IPython.display

# Librosa for audio
import librosa
# And the display module for visualization
import librosa.display
import sys

#audio_path = librosa.util.example_audio_file()

# or uncomment the line below and point it at your favorite song:
#

if len(sys.argv) < 2:
    print("Plays a wave file.\n\nUsage: %s filename.wav" % sys.argv[0])
    sys.exit(-1)

audio_path = sys.argv[1]

y, sr = librosa.load(audio_path)
#IPython.display.Audio(data=y, rate=sr)
y_harmonic, y_percussive = librosa.effects.hpss(y)

librosa.output.write_wav('/home/lkasser/AutoDorm/harmonic.wav', y_harmonic, sr)
librosa.output.write_wav('/home/lkasser/AutoDorm/bass.wav', y_percussive, sr)

tempo, beats = librosa.beat.beat_track(y=y_percussive, sr=sr)
beats = librosa.frames_to_time(beats, sr=sr)
np.save("beats", beats)
print(tempo)
print(beats)

pitches, magnitudes = librosa.piptrack(y=y_harmonic, sr=sr)
# something is wrong here
indices = np.argmax(magnitudes, axis=1)
pitches = pitches[:, indices]
print(pitches)

