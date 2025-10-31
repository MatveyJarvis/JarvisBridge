# -*- coding: utf-8 -*-
"""
hotword_probe_stt.py
Записывает ~3 сек с микрофона (INPUT_DEVICE_INDEX из .env), отправляет в Whisper (RU),
печатает распознанный текст и сохраняет файл для проверки (./_probe_hotword.wav).
Это чистая проверка STT-контура для hotword.
"""

import os, time, wave, uuid
import numpy as np
import sounddevice as sd

# === .env ===
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))
except Exception:
    pass

# === OpenAI ===
try:
    from openai import OpenAI
    _SDK = "new"
except Exception:
    import openai  # type: ignore
    _SDK = "old"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_STT = os.getenv("OPENAI_STT_MODEL", "whisper-1")
SAMPLE_RATE = 16000

_env_idx = os.getenv("INPUT_DEVICE_INDEX", "-1")
DEVICE_INDEX = None if _env_idx in ("-1", "", None) else int(_env_idx)

def save_wav(path: str, pcm16: bytes, sr=16000):
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(pcm16)

def record_fixed(seconds=3.0) -> bytes:
    blocksize = int(SAMPLE_RATE * 0.03)
    q = []

    def cb(indata, frames, t, status):
        q.append((indata[:,0] * 32767).astype(np.int16).tobytes())

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32",
                        blocksize=blocksize, device=DEVICE_INDEX, callback=cb):
        time.sleep(seconds)
    return b"".join(q)

def transcribe_ru(wav_path: str) -> str:
    if not OPENAI_API_KEY:
        return "[ERROR] OPENAI_API_KEY not set"
    if _SDK == "new":
        client = OpenAI(api_key=OPENAI_API_KEY)
        with open(wav_path, "rb") as f:
            res = client.audio.transcriptions.create(
                model=MODEL_STT, file=f, response_format="text", temperature=0.0, language="ru"
            )
        return (res or "").strip()
    else:
        openai.api_key = OPENAI_API_KEY  # type: ignore
        with open(wav_path, "rb") as f:
            res = openai.Audio.transcriptions.create(  # type: ignore
                model=MODEL_STT, file=f, response_format="text", temperature=0.0, language="ru"
            )
        return (res or "").strip()

def main():
    print(f"[probe] INPUT_DEVICE_INDEX={DEVICE_INDEX}")
    print(f"[probe] OPENAI_API_KEY set: {bool(OPENAI_API_KEY)}")
    print("[probe] Запись ~3 сек. Скажи чётко: «Привет, Джарвис».")
    pcm16 = record_fixed(3.0)
    path = os.path.join(os.getcwd(), "_probe_hotword.wav")
    save_wav(path, pcm16, SAMPLE_RATE)
    print(f"[probe] Файл сохранён: {path}")

    print("[probe] Отправляю в Whisper (RU)…")
    try:
        text = transcribe_ru(path)
    except Exception as e:
        text = f"[EXCEPTION] {type(e).__name__}: {e}"
    print(f"[probe] Whisper → {text!r}")

if __name__ == "__main__":
    main()
