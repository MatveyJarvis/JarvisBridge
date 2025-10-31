# -*- coding: utf-8 -*-
import io, time, wave
import sounddevice as sd
import numpy as np
import os
from pathlib import Path

RATE = 16000
CH = 1
DUR = 3
DEV = int(os.getenv("INPUT_DEVICE_INDEX", "1"))

print(f"[STT-PING] device={DEV}, rate={RATE}, ch={CH}, dur={DUR}s")

# 1) Запись 3 сек
sd.default.device = (DEV, None)
print("[STT-PING] Говори фразу: 'Привет, Джарвис'...")
rec = sd.rec(int(DUR*RATE), samplerate=RATE, channels=CH, dtype='int16')
sd.wait()

# Сохраним на всякий
out = r"C:\JarvisBridge\temp\stt_ping.wav"
Path(out).parent.mkdir(parents=True, exist_ok=True)
with wave.open(out, 'wb') as wf:
    wf.setnchannels(CH); wf.setsampwidth(2); wf.setframerate(RATE)
    wf.writeframes(rec.tobytes())
print(f"[STT-PING] Сохранено: {out}")

# 2) Отправка в OpenAI Whisper
# Требуется переменная окружения OPENAI_API_KEY в .env или в системе
import openai
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("[STT-PING][ERR] Нет OPENAI_API_KEY. Проверь .env")
    raise SystemExit(1)
openai.api_key = api_key

print("[STT-PING] Отправляю в OpenAI Whisper...")
with open(out, "rb") as f:
    transcript = openai.audio.transcriptions.create(
        model="whisper-1",
        file=f,
        language="ru"
    )

text = transcript.text if hasattr(transcript, "text") else str(transcript)
print("[STT-PING] Результат распознавания:")
print(text)
