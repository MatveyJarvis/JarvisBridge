# -*- coding: utf-8 -*-
"""
Jarvis Main (VOICE) + OS-Bridge — B.1 интеграция (фикс TTS)
- Принудительно используем TTS через tts_openai.say (игнорируем TTS_ENGINE)
- Явно печатаем, что TTS активирован, и отлавливаем ошибки озвучки
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# === ПАПКИ/ЛОГИ ==============================================================
ROOT = Path(__file__).resolve().parent
TEMP_DIR = ROOT / "temp"
LOGS_DIR = ROOT / "logs"
TEMP_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / "voice_bridge.log"

def log(line: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {line}\n")

# Добавим возможные каталоги с модулями
for extra in [ROOT, ROOT / "src", ROOT / "scripts", ROOT / "jarvis_min"]:
    p = str(extra)
    if p not in sys.path:
        sys.path.append(p)

# === ОС-МОСТ ================================================================
try:
    from os_bridge import bridge_execute
except Exception as e:
    raise RuntimeError(f"Не найден os_bridge.py рядом с проектом: {e}")

# === STT / TTS / RECORDER ===================================================
# recorder
try:
    from recorder import record_wav  # ваш модуль
except Exception as e:
    raise RuntimeError(f"Не найден recorder.record_wav: {e}")

# STT
try:
    from stt_openai import transcribe  # ваш модуль
except Exception as e:
    raise RuntimeError(f"Не найден stt_openai.transcribe: {e}")

# TTS — принудительно openai
try:
    from tts_openai import say as tts_say
    TTS_ENGINE_NAME = "openai"
except Exception as e:
    raise RuntimeError(f"TTS (tts_openai.say) недоступен: {e}")

# Опциональный агент
_run_agent = None
try:
    from agent import run_agent as _run_agent
except Exception:
    pass

def ensure_env() -> int:
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise RuntimeError("OPENAI_API_KEY пуст. Заполните .env")
    try:
        sec = int(os.getenv("RECORD_SECONDS", "5"))
    except Exception:
        sec = 5
    return sec

def speak(text: str):
    """Озвучка с явным логом и перехватом ошибок."""
    msg = text or ""
    print(f"[TTS:{TTS_ENGINE_NAME}] {msg}")
    try:
        tts_say(msg)
        log(f"TTS OK: {msg}")
    except Exception as e:
        err = f"TTS ERROR: {e}"
        print(err)
        log(err)

def main():
    print("Jarvis Voice + OS-Bridge (B.1) — готов.")
    print(f"TTS активен: {TTS_ENGINE_NAME}")
    log("=== START Voice+Bridge ===")
    sec = ensure_env()
    wav_path = str(TEMP_DIR / "voice_in.wav")

    while True:
        try:
            cmd = input("\nНажмите ENTER и говорите (или 'q' для выхода): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nВыход.")
            break
        if cmd == "q":
            print("Выход.")
            break

        print(f"[REC] Запись ~{sec} сек...")
        try:
            record_wav(wav_path, seconds=sec)
            print(f"[Recorder] Сохранено: {wav_path}")
        except Exception as e:
            msg = f"Ошибка записи микрофона: {e}"
            print(msg); log(msg)
            continue

        try:
            text = (transcribe(wav_path) or "").strip()
        except Exception as e:
            msg = f"Ошибка STT: {e}"
            print(msg); log(msg)
            continue

        if not text:
            print("[STT] Пусто. Повторите.")
            speak("Не расслышал. Повтори, пожалуйста.")
            continue

        print(f"[STT] {text}")
        log(f"STT: {text}")

        # 1) Сначала ОС-мост
        res = bridge_execute(text)
        if res.get("ok"):
            print(f"[BRIDGE] matched: {res.get('matched_id')}")
            speak(res.get("message", "Готово."))
            log(f"BRIDGE OK: {res.get('matched_id')}")
            continue
        else:
            print("[BRIDGE] Команда не распознана мостом.")

        # 2) Агент (если есть) или эхо
        reply = None
        if _run_agent:
            try:
                reply = _run_agent(text)
            except Exception as e:
                print(f"[AGENT] Ошибка агента: {e}")
        if not reply:
            reply = f"Ты сказал: {text}"
        print(f"[REPLY] {reply}")
        speak(reply)
        log(f"REPLY: {reply}")

if __name__ == "__main__":
    main()
