# tools/rec_one_sd.py
import sys, sounddevice as sd, soundfile as sf, numpy as np
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: python tools/rec_one_sd.py <device_index> [seconds]")
    sys.exit(1)

dev = int(sys.argv[1])
sec = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
sr  = int(sd.query_devices(dev)['default_samplerate'])
print(f"[rec] device={dev} @ {sr}Hz for {sec}s ... Скажи: 'привет джарвис'")

data = sd.rec(int(sec*sr), samplerate=sr, channels=1, dtype="int16", device=dev)
sd.wait()

amp = float(np.abs(data).mean())
peak = int(np.abs(data).max())
out  = Path("temp")/f"probe_dev{dev}_{sr}.wav"
out.parent.mkdir(parents=True, exist_ok=True)
sf.write(str(out), data, sr, subtype="PCM_16")
print(f"[rec] saved: {out} | mean_amp={amp:.1f} | peak={peak}")

if amp < 500:  # эмпирический порог тишины
    print("[warn] Слишком тихо: проверь громкость/усиление микрофона в Windows.")
else:
    print("[ok] Запись выглядит живой. Прослушай файл вручную.")
