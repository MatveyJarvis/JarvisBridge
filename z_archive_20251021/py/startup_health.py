# -*- coding: utf-8 -*-
"""
startup_health.py — быстрый health-check при старте:
- короткий системный Beep (динамики),
- пробуем озвучить «Готов к работе».
- пишем результат в logs\health_YYYY-MM-DD.log
"""

import os, sys, datetime

def _log(msg: str):
    d = datetime.datetime.now()
    logdir = os.path.join(os.getcwd(), "logs")
    os.makedirs(logdir, exist_ok=True)
    path = os.path.join(logdir, f"health_{d:%Y-%m-%d}.log")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{d:%H:%M:%S}] {msg}\n")

def _beep():
    try:
        import winsound
        winsound.Beep(880, 180)  # 0.18 c
        winsound.Beep(988, 180)
        _log("Beep OK")
    except Exception as e:
        _log(f"Beep FAIL: {e}")

def _say_ready():
    # 1) пробуем tts_openai.say
    try:
        from tts_openai import say as tts_say
        tts_say("Готов к работе.")
        _log("TTS OpenAI: OK")
        return
    except Exception as e:
        _log(f"TTS OpenAI: FAIL: {e}")

    # 2) пробуем локальный движок pyttsx3 (если есть)
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", 185)
        engine.say("Готов к работе.")
        engine.runAndWait()
        _log("TTS local (pyttsx3): OK")
        return
    except Exception as e:
        _log(f"TTS local: FAIL: {e}")

def run():
    _log("=== STARTUP HEALTH ===")
    _beep()
    _say_ready()
    _log("=== DONE ===")

if __name__ == "__main__":
    run()
