# -*- coding: utf-8 -*-
"""
hotword_cmd_stt_llm_tts.py — A3.4 (silent MP3 playback via winmm/MCI)
- Проигрываем TTS без открытия Яндекс.Музыки/плееров и без окон.
"""

import os, sys, time, ctypes
from ctypes import wintypes

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TMP_DIR = os.path.join(ROOT, "temp")
os.makedirs(TMP_DIR, exist_ok=True)
TTS_MP3_PATH = os.path.join(TMP_DIR, "tts_out.mp3")

def log(msg: str):
    sys.stdout.write(msg + "\n"); sys.stdout.flush()

# === Тихое воспроизведение MP3 через MCI (winmm) ===
_mciSendStringW = ctypes.windll.winmm.mciSendStringW
_mciSendStringW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.UINT, wintypes.HANDLE]
_mciSendStringW.restype = wintypes.UINT

def _mci(cmd: str) -> int:
    buf = ctypes.create_unicode_buffer(1024)
    return _mciSendStringW(cmd, buf, 1024, None)  # 0 = OK

def play_mp3_silent(path: str, wait: bool = True) -> None:
    alias = f"tts_{int(time.time()*1000)}"
    _mci(f"close {alias}")
    rc = _mci(f'open "{path}" type mpegvideo alias {alias}')
    if rc != 0:
        log(f"[WARN] MCI open failed: code={rc}")
        return
    if wait:
        _mci(f"play {alias} wait")
        _mci(f"close {alias}")
    else:
        _mci(f"play {alias}")

# === TTS: OpenAI → mp3, иначе безопасный fallback ===
def tts_synthesize_to_mp3(text: str, out_path: str):
    ok = False
    try:
        try:
            from openai import OpenAI
            client = OpenAI()
            with client.audio.speech.with_streaming_response.create(
                model="gpt-4o-mini-tts", voice="alloy", input=text
            ) as resp:
                resp.stream_to_file(out_path)
            ok = True
        except Exception as e:
            log(f"[TTS] OpenAI TTS fallback: {e}")
    except Exception as e:
        log(f"[TTS] import OpenAI error: {e}")

    if not ok:
        with open(out_path, "wb") as f:
            f.write(b"ID3")
        time.sleep(0.2)

def speak(text: str):
    log(f"[TTS] Озвучиваю: {text}")
    tts_synthesize_to_mp3(text, TTS_MP3_PATH)
    play_mp3_silent(TTS_MP3_PATH, wait=True)

# === Тестовый сценарий ===
def listen_hotword_once() -> bool:
    log("[Hotword] Попытка 1/3. Скажи фразу (варианты): привет джарвис, джарвис привет, привет jarvis ...")
    log("[rec] device=1, dur=3.0s")
    log("[STT] Распознал: привет джарвис  | best='keyword' (100.0%)")
    log("[Hotword] ✅ Совпадение, говори команду…")
    speak("Слушаю")
    return True

def record_command_and_transcribe() -> str:
    log("[rec] device=1, dur=6.0s")
    cmd = "какая сегодня погода"
    log(f"[STT] Команда: {cmd}")
    return cmd

def ask_llm_for_answer(text: str) -> str:
    ans = ("Извини, я не могу предоставить текущую информацию о погоде. "
           "Попробуй проверить в приложении или на сайте прогноза погоды.")
    log(f"[LLM] Ответ: {ans}")
    return ans

def main():
    if not listen_hotword_once():
        log("[Hotword] Не удалось распознать ключевую фразу."); return
    cmd = record_command_and_transcribe()
    reply = ask_llm_for_answer(cmd)
    speak(reply)
    log("[Done]")

if __name__ == "__main__":
    main()
