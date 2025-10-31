# -*- coding: utf-8 -*-
import os, sys, time, wave
import numpy as np
import sounddevice as sd

RATE = 16000
CH = 1
DUR = 4

print("=== SOUNDDEVICE DEVICES ===")
try:
    print("Default input index:", sd.default.device[0])
except Exception as e:
    print("Default input unknown:", e)

devices = sd.query_devices()
for i, d in enumerate(devices):
    if d.get("max_input_channels", 0) > 0:
        print(f"[{i}] {d['name']} | hostapi={d['hostapi']} | sr={int(d.get('default_samplerate',0))} | ch_in={d['max_input_channels']}")

# авто-выбор: берём первое устройство, в имени которого есть 'Mic input with SST' или 'Микрофон'
choose = None
for i, d in enumerate(devices):
    name = d["name"].lower()
    if d.get("max_input_channels",0) > 0 and ("mic input with sst" in name or "микрофон" in name or "microphone" in name):
        choose = i
        break

if choose is None:
    choose = sd.default.device[0]

print(f"\nБуду писать с устройства index={choose}")
sd.default.device = (choose, None)

print(f"Запись {DUR} сек @ {RATE} Hz, mono…")
rec = sd.rec(int(DUR*RATE), samplerate=RATE, channels=CH, dtype='int16')
sd.wait()

out = r"C:\JarvisBridge\temp\probe_sd.wav"
wf = wave.open(out, 'wb'); wf.setnchannels(CH); wf.setsampwidth(2); wf.setframerate(RATE)
wf.writeframes(rec.tobytes()); wf.close()

print("Сохранено:", out)
print("Готово. Открой файл и скажи, слышно ли голос. Пришли скрин списка устройств (этой программы).")
