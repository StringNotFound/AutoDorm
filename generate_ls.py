import numpy as np
from essentia.standard import *
import sys

# Loading audio file
audio = MonoLoader(filename=sys.argv[1])()

# Compute beat positions and BPM
rhythm_extractor = RhythmExtractor2013(method="multifeature")
bpm, beats, beats_confidence, _, beats_intervals = rhythm_extractor(audio)

print("BPM:", bpm)
print("Beat positions (sec.):", beats)
print("Beat estimation confidence:", beats_confidence)

loudness_extractor = BeatsLoudness(beats=beats, frequencyBands=[20, 150, 400, 3200, 7000, 22000])
loudness, lbr = loudness_extractor(audio)

# only take the loudness of the lower-frequency channels
loudness = np.mean(lbr[:, 0:3], axis=1)

# normalize
loudness -= np.min(loudness)
loudness /= np.max(loudness)

beats_out = np.vstack((beats, loudness))
np.save('beats.npy', beats_out)

#equalizer = EqualLoudness()
#pitch_estimator = PredominantPitchMelodia()
#pitches, pitches_confidence = pitch_estimator(equalizer(audio))
#pitch_times = np.linspace(0.0, len(audio) / 44100.0, len(pitches))

#print("Pitches:", pitches)
#print("Pitch estimation confidence:", pitches_confidence)

#np.save('pitches.npy', pitches)
#np.save('pitch_times.npy', pitch_times)
