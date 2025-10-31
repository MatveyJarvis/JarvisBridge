# tts_openai.py
from __future__ import annotations
import os
import pathlib
from openai import OpenAI
from pydub import AudioSegment
from pydub.playback import play
import dotenv

# автоподгрузка .env (лежит рядом с файлом)
dotenv.load_dotenv()

DEFAULT_TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
DEFAULT_VOICE = os.getenv("OPENAI_TTS_VOICE", "alloy")
OUTPUT_DIR = pathlib.Path(os.getenv("TTS_OUTPUT_DIR", "."))


def say(text: str, voice: str = DEFAULT_VOICE, model: str = DEFAULT_TTS_MODEL, filename: str | None = None) -> str:
    """
    Синтез речи через OpenAI и (по возможности) воспроизведение.
    Возвращает путь к mp3-файлу.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY пуст. Заполни .env")

    client = OpenAI(api_key=api_key)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / (filename or "tts_out.mp3")

    # Генерация аудио
    with client.audio.speech.with_streaming_response.create(
        model=model,
        voice=voice,
        input=text,
    ) as response:
        response.stream_to_file(out_path)

    # Пытаемся воспроизвести (если нет ffmpeg — просто вернём файл)
    try:
        audio = AudioSegment.from_file(out_path)
        play(audio)
    except Exception:
        pass

    return str(out_path)


if __name__ == "__main__":
    # быстрый запуск из консоли:
    # python tts_openai.py "Привет, это тест голоса."
    import sys
    phrase = "Проверка TTS. Всё работает." if len(sys.argv) < 2 else " ".join(sys.argv[1:])
    print(say(phrase))
