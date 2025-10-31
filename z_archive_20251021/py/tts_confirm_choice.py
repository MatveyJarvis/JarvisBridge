# tts_confirm_choice.py
# -*- coding: utf-8 -*-
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from pydub import AudioSegment
import simpleaudio as sa

ROOT = Path(__file__).parent
OUT = ROOT / "_out"
OUT.mkdir(exist_ok=True)

def play_wav(p):
    wave = sa.WaveObject.from_wave_file(str(p))
    play = wave.play()
    play.wait_done()

def main():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("В .env нет OPENAI_API_KEY")
    model = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
    voice = os.getenv("OPENAI_TTS_VOICE", "alloy")

    client = OpenAI(api_key=api_key)
    mp3p = OUT / "tts_confirm_choice.mp3"
    wavp = OUT / "tts_confirm_choice.wav"
    text = f"Голос {voice} установлен. Проверка связи."

    print(f"Модель: {model} | Голос: {voice}")
    with client.audio.speech.with_streaming_response.create(
        model=model, voice=voice, input=text
    ) as resp:
        resp.stream_to_file(str(mp3p))

    AudioSegment.from_file(str(mp3p)).export(str(wavp), format="wav")
    print("→ Воспроизвожу подтверждение…")
    play_wav(wavp)
    print("Готово.")

if __name__ == "__main__":
    main()
