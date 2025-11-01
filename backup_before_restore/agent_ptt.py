# agent_ptt.py — push-to-talk тест STT+TTS
import sounddevice as sd, soundfile as sf, numpy as np
from pathlib import Path
from dotenv import load_dotenv
import os, time

from stt_openai import transcribe
from tts_openai import say

load_dotenv()
BASE = Path(__file__).resolve().parent
TEMP = BASE/"temp"; TEMP.mkdir(exist_ok=True)

DEVICE = int(os.getenv("INPUT_DEVICE_INDEX", "-1"))
SR     = 44100

def record(seconds=2.0):
    print("Говори...")
    data = sd.rec(int(seconds*SR), samplerate=SR, channels=1, dtype="int16",
                  device=(None if DEVICE<0 else DEVICE))
    sd.wait()
    amp = float(np.abs(data).mean()); peak = int(np.abs(data).max())
    path = TEMP/f"ptt_{int(time.time())}.wav"
    sf.write(str(path), data, SR, subtype="PCM_16")
    print(f"[rec] {path.name} | mean_amp={amp:.1f} | peak={peak}")
    return path, amp

while True:
    input("\nНажми Enter и скажи фразу (2 сек). Ctrl+C — выход.")
    wav, amp = record(2.2)
    if amp < 500:
        print("Слишком тихо. Проверь устройство/уровень микрофона.")
        continue
    txt = (transcribe(str(wav), language="ru") or "").strip()
    print(f"[STT] {txt!r}")
    if not txt:
        say("Я не расслышал. Повтори, пожалуйста."); continue
    # простая логика: 8 плюс 8 -> 16
    reply = ""
    if "плюс" in txt and any(ch.isdigit() for ch in txt):
        try:
            expr = (txt.replace(" умножить на ", " * ")
                     .replace(" минус ", " - ")
                     .replace(" плюс ", " + ")
                     .replace("=", " "))
            reply = str(eval(expr))
        except Exception:
            reply = txt
    else:
        reply = txt
    print(f"[TTS] → {reply}")
    say(reply)
