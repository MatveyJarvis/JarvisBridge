# -*- coding: utf-8 -*-
"""
scripts/greet_play.py — генерирует TTS-"привет" и проигрывает его тихо (winmm/MCI)
"""
import os, time, ctypes
from ctypes import wintypes

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TMP = os.path.join(ROOT, "temp")
os.makedirs(TMP, exist_ok=True)
MP3 = os.path.join(TMP, "greet.mp3")

# --- TTS через OpenAI (fallback, если нет сети/ключа) ---
def tts_to_mp3(text: str, out_path: str):
    ok = False
    try:
        from openai import OpenAI
        client = OpenAI()
        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts", voice="alloy", input=text
        ) as r:
            r.stream_to_file(out_path)
        ok = True
    except Exception as e:
        # Фоллбек — короткий "псевдо"-mp3, чтобы плеер отработал
        with open(out_path, "wb") as f:
            f.write(b"ID3")
        time.sleep(0.15)
    return ok

# --- Тихий проигрыватель MP3 (winmm/MCI) ---
_mci = ctypes.windll.winmm.mciSendStringW
_mci.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.UINT, wintypes.HANDLE]
_mci.restype = wintypes.UINT

def mci(cmd: str) -> int:
    buf = ctypes.create_unicode_buffer(1024)
    return _mci(cmd, buf, 1024, None)

def play_mp3_silent(path: str):
    alias = f"tts_{int(time.time()*1000)}"
    mci(f"close {alias}")
    rc = mci(f'open "{path}" type mpegvideo alias {alias}')
    if rc != 0:
        return
    mci(f"play {alias} wait")
    mci(f"close {alias}")

if __name__ == "__main__":
    txt = "Привет, я запущен и готов к работе. Жду активацию."
    tts_to_mp3(txt, MP3)
    play_mp3_silent(MP3)
