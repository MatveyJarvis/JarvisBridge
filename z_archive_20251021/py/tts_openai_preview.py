# tts_openai_preview.py
# -*- coding: utf-8 -*-
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Проигрывание: сперва простой WAV-плеер, затем pydub как запасной вариант
try:
    import simpleaudio as sa
except Exception:
    sa = None

from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio


TEXT  = "Привет! Это тест. Если ты слышишь этот голос — воспроизведение работает."
VOICE = "alloy"
MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")


def main():
    print("=== OpenAI TTS — Предпрослушка ===")

    # 1) Загружаем ключ из .env
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("❌ В .env не найден OPENAI_API_KEY")

    # 2) Клиент
    client = OpenAI(api_key=api_key)

    # 3) Куда сохраняем
    out_dir = Path(__file__).parent / "_out"
    out_dir.mkdir(exist_ok=True)
    wav_path = out_dir / "tts_preview_alloy.wav"  # сохраняем как WAV

    # 4) Генерация (важно: без параметра формата — так требует твоя версия SDK)
    print(f"— Генерирую голос {VOICE}...")
    with client.audio.speech.with_streaming_response.create(
        model=MODEL,
        voice=VOICE,
        input=TEXT,
    ) as resp:
        resp.stream_to_file(str(wav_path))

    size = wav_path.stat().st_size
    print(f"OK ({size} байт). Файл: {wav_path}")

    # 5) Проигрывание
    # Сначала пробуем простой WAV-плеер (не требует ffmpeg)
    try:
        if sa is None:
            raise RuntimeError("simpleaudio не установлен")
        print("— Воспроизвожу (simpleaudio WAV)...")
        wave_obj = sa.WaveObject.from_wave_file(str(wav_path))
        play_obj = wave_obj.play()
        play_obj.wait_done()
        print("Готово.")
        return
    except Exception as e:
        print(f"⚠️ simpleaudio не удалось: {e}")

    # Если не вышло — пробуем через pydub (для MP3/WAV; mp3 требует ffmpeg)
    try:
        print("— Воспроизвожу (pydub)...")
        audio = AudioSegment.from_file(str(wav_path))  # авто-детект формата по заголовку
        play_obj = _play_with_simpleaudio(audio)
        play_obj.wait_done()
        print("Готово (pydub).")
        return
    except Exception as e2:
        print(f"⚠️ pydub не удалось: {e2}")

    # Последний шанс — открыть системным плеером
    print("— Открою системным проигрывателем...")
    if os.name == "nt":
        os.startfile(str(wav_path))
    else:
        print(f"Открой вручную: {wav_path}")


if __name__ == "__main__":
    main()
