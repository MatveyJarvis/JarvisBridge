# -*- coding: utf-8 -*-
import time, wave, sys
import pyaudio

REC_SECONDS = 4
RATE = 16000
CH = 1

pa = pyaudio.PyAudio()

print("=== INPUT DEVICES ===")
default_in = pa.get_default_input_device_info() if pa.get_device_count() else None
for i in range(pa.get_device_count()):
    info = pa.get_device_info_by_index(i)
    if int(info.get('maxInputChannels', 0)) > 0:
        mark = " (DEFAULT)" if default_in and info["index"] == default_in["index"] else ""
        print(f"[{info['index']}] {info['name']} | sr={int(info.get('defaultSampleRate',0))} | ch={int(info.get('maxInputChannels',0))}{mark}")

print("\n=== QUICK RECORD @16000 Hz mono from chosen device ===")
# авто-выбор: если есть устройство с именем, содержащим 'Microphone'/'Микрофон' — возьми его, иначе default
chosen_idx = default_in["index"] if default_in else None
for i in range(pa.get_device_count()):
    info = pa.get_device_info_by_index(i)
    name = (info.get("name") or "").lower()
    if int(info.get('maxInputChannels',0))>0 and ("microphone" in name or "микрофон" in name):
        chosen_idx = info["index"]; break

if chosen_idx is None:
    print("Нет входных устройств. Прервусь.")
    pa.terminate(); sys.exit(1)

print(f"Буду писать с устройства index={chosen_idx}")
stream = pa.open(format=pyaudio.paInt16, channels=CH, rate=RATE, input=True,
                 input_device_index=chosen_idx, frames_per_buffer=1024)

frames = []
print("Говори обычным голосом 4 сек…")
t0=time.time()
while time.time()-t0 < REC_SECONDS:
    frames.append(stream.read(1024, exception_on_overflow=False))

stream.stop_stream(); stream.close(); pa.terminate()

out = r"C:\JarvisBridge\temp\probe.wav"
wf = wave.open(out, 'wb'); wf.setnchannels(CH); wf.setsampwidth(2); wf.setframerate(RATE); wf.writeframes(b"".join(frames)); wf.close()
print(f"Сохранено: {out}")
print("Готово. Пришли скрин вывода и напиши, слышно ли твой голос при воспроизведении файла.")
