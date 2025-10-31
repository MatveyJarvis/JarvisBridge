# jarvis_test_direct.py
# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv
from recorder import record_wav
from stt_openai import transcribe
from agent import run_agent
from tts_openai import say as tts_say

def main():
    load_dotenv()
    print("[Test] Режим прямого теста: запись → STT → агент → TTS")

    # Параметры теста
    in_rate = 16000
    device_index = int(os.getenv("INPUT_DEVICE_INDEX", "1"))
    tmp_dir = os.path.join(os.getcwd(), "temp")
    os.makedirs(tmp_dir, exist_ok=True)
    wav_path = os.path.join(tmp_dir, "test_direct.wav")

    # Записываем короткий запрос
    record_wav(wav_path, in_rate, 1, device_index, 2, 30, 8.0, "[recorder]")

    print(f"[Test] Сохранено: {wav_path}")
    print("[Test] Расшифровка (STT)...")
    text = transcribe(wav_path).strip()
    print(f"[STT] → {text!r}")

    if not text:
        print("[Test] Пустая расшифровка. Завершено.")
        return

    print("[Test] Ответ агента...")
    reply = run_agent(text).strip()
    print(f"[Agent] ← {reply!r}")

    print("[Test] Озвучка ответа...")
    tts_say(reply)
    print("[Test] Завершено.")

if __name__ == "__main__":
    main()
