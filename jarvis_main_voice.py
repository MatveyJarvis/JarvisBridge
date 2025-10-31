# jarvis_main_voice.py
# Главный запуск Jarvis с персональным приветствием

import os
from dotenv import load_dotenv

from recorder import record_wav
from stt_openai import transcribe
from tts_openai import say
from agent import run_agent, jarvis_greeting


def main():
    # Загружаем переменные окружения
    load_dotenv()
    owner = os.getenv("OWNER_NAME", "друг")

    # Приветствие голосом
    greeting = jarvis_greeting()
    print(f"[Jarvis] {greeting}")
    say(greeting)

    # Основной цикл (одна итерация для примера)
    while True:
        print("\n[Jarvis] Слушаю вас...")
        wav_path = record_wav()
        if not wav_path:
            print("[Jarvis] Ошибка записи.")
            continue

        # Расшифровка (STT)
        user_text = transcribe(wav_path)
        if not user_text:
            print("[Jarvis] Не разобрал речь.")
            continue

        print(f"[Вы] {user_text}")

        # Ответ Jarvis
        response = run_agent(user_text)
        print(f"[Jarvis] {response}")
        say(response)

        # Условие выхода
        if user_text.strip().lower() in ["стоп", "выход", "пока"]:
            bye = f"До свидания, {owner}."
            print(f"[Jarvis] {bye}")
            say(bye)
            break


if __name__ == "__main__":
    main()
