# -*- coding: utf-8 -*-
"""
probe_mic_level.py — быстрый тест входа микрофона.
Печатает уровень (RMS) каждые ~200 мс. Если всегда 0.0000 — устройство не то / не слышно.
Берёт индекс из .env (INPUT_DEVICE_INDEX). Частота 16 кГц, моно.
"""

import os, time, numpy as np, sounddevice as sd

SAMPLE_RATE = 16000
BLOCK_MS = 200
BLOCK = int(SAMPLE_RATE * (BLOCK_MS/1000.0))

env_idx = os.getenv("INPUT_DEVICE_INDEX", "-1")
DEVICE_INDEX = None if env_idx in ("-1", "", None) else int(env_idx)

def main():
    print(f"[probe] device index = {DEVICE_INDEX}")
    print("[probe] Говорите в микрофон. Идёт замер ~6 секунд:")
    rms_vals = []
    def cb(indata, frames, time_info, status):
        x = (indata[:,0] * 32767).astype(np.int16)
        rms = float(np.sqrt(np.mean((x.astype(np.float32))**2)) / 32767.0)
        rms_vals.append(rms)
        print(f"RMS={rms:.4f}")

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32",
                        blocksize=BLOCK, device=DEVICE_INDEX, callback=cb):
        t0 = time.time()
        while time.time() - t0 < 6.0:
            time.sleep(0.05)

    hi = max(rms_vals) if rms_vals else 0.0
    print(f"[probe] MAX_RMS={hi:.4f}")
    print("[probe] Если MAX_RMS ≈ 0.0000 — этот вход молчит/не тот.")

if __name__ == "__main__":
    main()
