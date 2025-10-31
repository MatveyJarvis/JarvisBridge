# tools/probe_mics_sd.py — записывает по 1с с каждого входа, чтобы увидеть, что реально пишет
import sounddevice as sd
import soundfile as sf
import numpy as np
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "temp" / "probe"
OUT.mkdir(parents=True, exist_ok=True)

devs = sd.query_devices()
print("=== INPUT DEVICES (sounddevice) ===")
for i, info in enumerate(devs):
    if info["max_input_channels"] <= 0:
        continue
    name = info["name"]
    sr = int(info["default_samplerate"])
    print(f"[{i}] {name} | SR={sr}")
    try:
        sd.check_input_settings(device=i, samplerate=sr, channels=1)
        data = sd.rec(int(1.0 * sr), samplerate=sr, channels=1, dtype="int16", device=i)
        sd.wait()
        amp = int(np.abs(data).mean())
        out = OUT / f"mic_{i}_{sr}.wav"
        sf.write(str(out), data, sr, subtype="PCM_16")
        print(f"  -> OK, amp≈{amp} → файл: {out.name}")
    except Exception as e:
        print(f"  -> FAIL: {e}")
