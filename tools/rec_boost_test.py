import sounddevice as sd, soundfile as sf, numpy as np
from pathlib import Path
sr = 44100
sec = 3
print("Говори...")
data = sd.rec(int(sec*sr), samplerate=sr, channels=1, dtype="float32")
sd.wait()
# Усиление (3–8 раз)
data *= 6
data = np.clip(data, -1.0, 1.0)
out = Path("temp") / "boost_test.wav"
sf.write(str(out), data, sr)
print("Сохранено:", out)
