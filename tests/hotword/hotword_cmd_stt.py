# -*- coding: utf-8 -*-
"""
hotword_cmd_stt.py — улучшенная версия A1.4
- три попытки распознавания фразы пробуждения
- вывод вероятности совпадения
- повтор, если не совпало
"""

import os, time, wave, difflib
from datetime import datetime
from pathlib import Path
import numpy as np
import sounddevice as sd
from openai import OpenAI
from dotenv import load_dotenv

ROOT = Path(r"C:\JarvisBridge")
TEMP = ROOT / "temp"
TEMP.mkdir(parents=True, exist_ok=True)
load_dotenv(ROOT / ".env", override=False)

def _pick_wake_phrase() -> str:
    phrases = []
    if os.getenv("WAKE_PHRASES"):
        phrases = [p.strip().lower() for p in os.getenv("WAKE_PHRASES").replace(",", ";").split(";") if p.strip()]
    elif os.getenv("WAKE_PHRASE"):
        phrases = [os.getenv("WAKE_PHRASE").strip().lower()]
    return phrases[0] if phrases else "привет джарвис"

WAKE_PHRASE = _pick_wake_phrase()
INPUT_DEVICE_INDEX = int(os.getenv("INPUT_DEVICE_INDEX", "1"))
SR = int(os.getenv("INPUT_SAMPLE_RATE", "16000"))
CH = 1
WAKE_DURATION = 3.0
CMD_DURATION = 6.0
STT_MODEL = os.getenv("OPENAI_STT_MODEL", "whisper-1")
client = OpenAI()

def _save_wav(path, data):
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(CH)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((data * 32767).astype(np.int16).tobytes())

def _record(sec):
    frames = int(sec * SR)
    print(f"[rec] device={INPUT_DEVICE_INDEX}, dur={sec}s")
    data = sd.rec(frames, samplerate=SR, channels=CH, dtype="float32", device=INPUT_DEVICE_INDEX)
    sd.wait()
    return data.reshape(-1)

def _stt(path):
    with open(path, "rb") as f:
        r = client.audio.transcriptions.create(model=STT_MODEL, file=f, language="ru")
    return (r.text or "").strip().lower()

def _sim(a,b): return difflib.SequenceMatcher(None,a,b).ratio()*100

def main():
    for attempt in range(1,4):
        print(f"[Hotword] Попытка {attempt}/3. Скажи фразу: «{WAKE_PHRASE}»")
        wav = TEMP / f"wake_try{attempt}_{int(time.time())}.wav"
        _save_wav(wav, _record(WAKE_DURATION))
        text = _stt(wav)
        score = _sim(text, WAKE_PHRASE)
        print(f"[STT] Распознал: {text} ({score:.1f}%)")
        if score >= 70:
            print("[Hotword] ✅ Совпадение, говори команду…")
            cmd = TEMP / f"cmd_{int(time.time())}.wav"
            _save_wav(cmd, _record(CMD_DURATION))
            print("[STT] Команда:", _stt(cmd))
            print("[Done]")
            return
        else:
            print("[Hotword] Не совпало, попробуем ещё раз.\n")
    print("[Hotword] ❌ Три неудачных попытки — выход.")

if __name__ == "__main__":
    sd.default.device = (None, INPUT_DEVICE_INDEX)
    main()
