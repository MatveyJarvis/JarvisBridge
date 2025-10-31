import os
from dotenv import load_dotenv
from recorder import record_wav
from stt_openai import transcribe
from agent import run_agent

def ensure_env():
    load_dotenv()
    missing = []
    for k in ["OPENAI_API_KEY", "OPENAI_MODEL"]:
        if not os.getenv(k):
            missing.append(k)
    if missing:
        raise RuntimeError(f"Отсутствуют переменные окружения: {', '.join(missing)}. Заполни .env")

    try:
        sec = int(os.getenv("RECORD_SECONDS", "5"))
    except Exception:
        sec = 5
    return sec

def _pick_say():
    """
    Выбирает TTS-движок по .env:
      TTS_ENGINE=openai  -> tts_openai.say
      TTS_ENGINE=local   -> tts_pyttsx3.say
    """
    engine = os.getenv("TTS_ENGINE", "openai").strip().lower()
    if engine == "local":
        from tts_pyttsx3 import say
    else:
        from tts_openai import say
    return say

def one_turn(seconds: int, say):
    wav_path = "input.wav"
    print(f"\n▶ Начинаю запись на {seconds} сек...")
    record_wav(wav_path, seconds=seconds)
    print("⏹️  Запись завершена.")
    text = transcribe(wav_path)
    if not text:
        print("⛔ Не удалось распознать речь. Увеличь RECORD_SECONDS в .env и попробуй снова.")
        return
    print(f"🗣️ Вы сказали: {text}")

    result = run_agent(text)
    if result.get("tool_logs"):
        for log in result["tool_logs"]:
            print(f"🔧 {log['tool']}({log['args']}) → {log['result']}")

    answer = (result.get("answer") or "Готово.").strip()
    print(f"🤖 Jarvis: {answer}")
    try:
        say(answer)
    except Exception as e:
        print(f"⚠️ Ошибка TTS: {e}")

def main():
    print("🧠 Jarvis: запись → распознавание → ответ → действия → озвучка")
    seconds = ensure_env()
    say = _pick_say()
    print("Нажмите Enter, затем говорите... (фиксированная длина записи)")

    while True:
        try:
            input("▶ Готов к записи. Нажмите Enter и говорите...")
            one_turn(seconds, say)
        except KeyboardInterrupt:
            print("\n👋 Выход.")
            break
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
