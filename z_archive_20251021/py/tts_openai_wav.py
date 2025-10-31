# -*- coding: utf-8 -*-
"""
OpenAI TTS → WAV → воспроизведение через PowerShell SoundPlayer.
Использует OPENAI_API_KEY из .env. Голос задаётся параметром voice (alloy, verse, shimmer, coral, sage, soft).
"""

import os
import base64
import subprocess
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from openai import OpenAI

ROOT = Path(__file__).resolve().parent
TEMP = ROOT / "temp"; TEMP.mkdir(parents=True, exist_ok=True)
LOGS = ROOT / "logs"; LOGS.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS / "tts_openai.log"

MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")  # быстрый и качественный
DEFAULT_VOICE = os.getenv("OPENAI_TTS_VOICE", "alloy")    # варианты: alloy, verse, shimmer, coral, sage, soft

def _log(line: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with (LOGS / "tts_openai.log").open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {line}\n")

def _ensure_client() -> OpenAI:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY пуст. Заполните .env")
    return OpenAI(api_key=api_key)

def synth_to_wav(text: str, voice: str = None) -> Path:
    """
    Синтезирует text → WAV-файл в temp и возвращает путь.
    """
    voice = voice or DEFAULT_VOICE
    client = _ensure_client()
    out = TEMP / f"openai_tts_{voice}.wav"

    try:
        # Генерация WAV байтов
        resp = client.audio.speech.create(
            model=MODEL,
            voice=voice,
            input=text,
            format="wav",
        )
        audio_bytes = resp.read() if hasattr(resp, "read") else resp  # SDK может вернуть bytes
        with out.open("wb") as f:
            f.write(audio_bytes)
        _log(f"TTS OK: {voice} -> {out}")
        return out
    except Exception as e:
        _log(f"TTS ERROR: {e}")
        raise

def play_wav(path: Path):
    """
    Воспроизводит WAV синхронно через PowerShell (без внешних библиотек).
    """
    subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         f"[System.Media.SoundPlayer]::new('{str(path)}').PlaySync()"],
        check=False
    )

def say(text: str, voice: str = None):
    """
    Главная функция: синтез + проигрывание.
    """
    if not text:
        return
    wav = synth_to_wav(text, voice=voice)
    if wav.exists() and wav.stat().st_size > 0:
        play_wav(wav)
