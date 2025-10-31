# -*- coding: utf-8 -*-
"""
Jarvis Voice + OS-Bridge — B.1 (v2, явная TTS-отладка)
- Печатаем баннер V2 и строку [TTS] перед озвучкой.
- Ловим ошибку TTS и пишем её в logs/voice_bridge_tts.err.txt
"""

import os, sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
TEMP = ROOT / "temp"; TEMP.mkdir(parents=True, exist_ok=True)
LOGS = ROOT / "logs"; LOGS.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS / "voice_bridge.log"
TTS_ERR = LOGS / "voice_bridge_tts.err.txt"

def log(line: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a", encoding="utf-8") as f: f.write(f"[{ts}] {line}\n")

# добросим пути с вашими модулями
for extra in [ROOT, ROOT/"src", ROOT/"scripts", ROOT/"jarvis_min"]:
    p = str(extra)
    if p not in sys.path: sys.path.append(p)

# OS-bridge
from os_bridge import bridge_execute

# Recorder / STT
from recorder import record_wav
from stt_openai import transcribe

# TTS openai (принудительно)
from tts_openai import say as tts_say
TTS_ENGINE_NAME = "openai"

# Агент (опционально)
try:
    from agent import run_agent as _run_agent
except Exception:
    _run_agent = None

def ensure_env() -> int:
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise RuntimeError("OPENAI_API_KEY пуст. Заполните .env")
    try: return int(os.getenv("RECORD_SECONDS", "5"))
    except: return 5

def speak(text: str):
    msg = text or ""
    print(f"[TTS:{TTS_ENGINE_NAME}] {msg}")
    try:
        tts_say(msg)
        log(f"TTS OK")
    except Exception as e:
        with TTS_ERR.open("a", encoding="utf-8") as f:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} | {e}\n")
        print(f"[TTS ERROR] {e}")
        log(f"TTS ERROR: {e}")

def main():
    print("=== Jarvis Voice + OS-Bridge V2 ===")
    print(f"TTS активен: {TTS_ENGINE_NAME}")
    log("=== START Voice+Bridge V2 ===")
    sec = ensure_env()
    wav_path = str(TEMP / "voice_in.wav")

    while True:
        try:
            cmd = input("\nНажмите ENTER и говорите (или 'q' для выхода): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nВыход."); break
        if cmd == "q": print("Выход."); break

        print(f"[REC] Запись ~{sec} сек...")
        record_wav(wav_path, seconds=sec)
        print(f"[Recorder] Сохранено: {wav_path}")

        text = (transcribe(wav_path) or "").strip()
        if not text:
            print("[STT] Пусто."); speak("Не расслышал. Повтори, пожалуйста."); continue

        print(f"[STT] {text}"); log(f"STT: {text}")

        res = bridge_execute(text)
        if res.get("ok"):
            print(f"[BRIDGE] matched: {res.get('matched_id')}")
            speak(res.get("message", "Готово."))
            log(f"BRIDGE OK: {res.get('matched_id')}")
            continue

        print("[BRIDGE] нет совпадений")
        reply = None
        if _run_agent:
            try: reply = _run_agent(text)
            except Exception as e: print(f"[AGENT] Ошибка: {e}")
        if not reply: reply = f"Ты сказал: {text}"
        print(f"[REPLY] {reply}")
        speak(reply); log(f"REPLY: {reply}")

if __name__ == "__main__":
    main()
