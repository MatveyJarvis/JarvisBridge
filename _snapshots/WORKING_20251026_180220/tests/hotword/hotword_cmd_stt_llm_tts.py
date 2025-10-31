# -*- coding: utf-8 -*-
"""
hotword_cmd_stt_llm_tts.py — A3.6 (Pause/Resume + interactive command)
- Тихий MP3 через winmm/MCI
- «Стоп/Пауза Джарвис» останавливает слушание до «Привет Джарвис»
- Команду вводим вручную в консоли (для точной проверки логики)
"""

import os, sys, time, ctypes, re
from ctypes import wintypes

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TMP_DIR = os.path.join(ROOT, "temp"); os.makedirs(TMP_DIR, exist_ok=True)
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
        log(f"[WARN] MCI open failed: code={rc}"); return
    if wait:
        _mci(f"play {alias} wait"); _mci(f"close {alias}")
    else:
        _mci(f"play {alias}")

# === TTS (OpenAI → mp3) с безопасным fallback ===
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
        with open(out_path, "wb") as f: f.write(b"ID3")
        time.sleep(0.2)

def speak(text: str):
    log(f"[TTS] Озвучиваю: {text}")
    tts_synthesize_to_mp3(text, TTS_MP3_PATH)
    play_mp3_silent(TTS_MP3_PATH, wait=True)

# === Ключевые фразы ===
HOTWORDS = [r"\bпривет\s+джарвис\b", r"\bджарвис\s+привет\b", r"\bпривет\s+jarvis\b"]
PAUSE_WORDS = [r"\bстоп\s+джарвис\b", r"\bджарвис\s+стоп\b", r"\bпауза\s+джарвис\b"]

def _matches_any(text: str, patterns):
    t = text.lower()
    return any(re.search(p, t) for p in patterns)

def listen_hotword_once() -> bool:
    log("[Hotword] Жду фразу пробуждения... (эмитация для теста)")
    log("[rec] device=1, dur=3.0s")
    heard = input("[YOU] Напишите/введите фразу пробуждения (например: Привет Джарвис): ").strip()
    if not heard:
        heard = "привет джарвис"
    log(f"[STT] Распознал: {heard}  | best='keyword' (100.0%)")
    return _matches_any(heard, HOTWORDS)

def record_command_and_transcribe() -> str:
    log("[rec] device=1, dur=6.0s")
    cmd = input("[YOU] Введите команду (например: Стоп Джарвис / Пауза Джарвис / Какая сегодня погода): ").strip()
    if not cmd:
        cmd = "какая сегодня погода"
    log(f"[STT] Команда: {cmd}")
    return cmd

def ask_llm_for_answer(text: str) -> str:
    ans = ("Извини, я не могу предоставить текущую информацию о погоде. "
           "Попробуй проверить в приложении или на сайте прогноза погоды.")
    log(f"[LLM] Ответ: {ans}")
    return ans

def main():
    PAUSED = False
    while True:
        if PAUSED:
            log("[State] Пауза активна — жду только «привет джарвис».")
        if not listen_hotword_once():
            log("[Hotword] Ключевая фраза не распознана."); break

        log("[Hotword] ✅ Совпадение, говори команду…")
        speak("Слушаю")
        cmd = record_command_and_transcribe()

        if _matches_any(cmd, PAUSE_WORDS):
            PAUSED = True
            speak("Пауза. Скажи «привет джарвис», чтобы продолжить.")
            continue

        if PAUSED:
            PAUSED = False
            speak("Продолжаем работу.")

        reply = ask_llm_for_answer(cmd)
        speak(reply)

        # Для удобства теста спросим, хотим ли ещё круг
        cont = input("[YOU] Ещё один круг? (y/N): ").strip().lower()
        if cont != "y":
            break

    log("[Done]")

if __name__ == "__main__":
    main()
