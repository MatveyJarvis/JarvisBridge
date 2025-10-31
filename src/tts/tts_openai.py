# -*- coding: utf-8 -*-
"""
OpenAI TTS: генерируем MP3 и воспроизводим через ffplay (FFmpeg).
Переменные окружения:
  OPENAI_TTS_MODEL  (по умолчанию: tts-1)
  OPENAI_TTS_VOICE  (по умолчанию: alloy)
"""

import os
import shutil
import subprocess
import tempfile
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def tts_to_file(text: str, out_path: str | None = None) -> str:
    """
    Генерирует аудиофайл с озвучкой текста (MP3) и возвращает путь к файлу.
    """
    if not text or not text.strip():
        raise ValueError("TTS: пустой текст")

    model = os.getenv("OPENAI_TTS_MODEL", "tts-1").strip()
    voice = os.getenv("OPENAI_TTS_VOICE", "alloy").strip()

    if out_path is None:
        fd, path = tempfile.mkstemp(prefix="jarvis_tts_", suffix=".mp3")
        os.close(fd)
        out_path = path

    client = OpenAI()

    # Стриминг без параметра 'format' — совместимо с текущей версией SDK
    with client.audio.speech.with_streaming_response.create(
        model=model,
        voice=voice,
        input=text
    ) as response:
        response.stream_to_file(out_path)

    return out_path


def _play_with_ffplay(path: str) -> None:
    """
    Воспроизводит файл через ffplay, если он доступен в PATH.
    """
    ffplay = shutil.which("ffplay")
    if not ffplay:
        # как запасной вариант — открыть системным плеером
        try:
            os.startfile(path)  # Windows
            return
        except Exception:
            pass
        raise RuntimeError("ffplay не найден в PATH, и не удалось открыть системным плеером.")

    # -nodisp: без окна, -autoexit: автоматически завершить, -v quiet: без логов
    subprocess.run([ffplay, "-nodisp", "-autoexit", "-v", "quiet", path], check=False)


def say(text: str) -> str:
    """
    Синтезирует речь и сразу проигрывает её через ffplay.
    Возвращает путь к созданному MP3.
    """
    audio_path = tts_to_file(text)
    _play_with_ffplay(audio_path)
    return audio_path
