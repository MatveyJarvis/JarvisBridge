# C:\JarvisBridge\scripts\tts_test_openai.py
import os
from dotenv import load_dotenv
from openai import OpenAI
import soundfile as sf
import sounddevice as sd

def main():
    load_dotenv()

    tts_model = os.getenv("OPENAI_TTS_MODEL", "tts-1")
    tts_voice = os.getenv("OPENAI_TTS_VOICE", "alloy")
    text = "Привет! Тест связи. Я — Джарвис. Готов к работе."

    client = OpenAI()

    print(f"Генерирую речь: модель={tts_model}, голос={tts_voice} …")
    speech = client.audio.speech.create(
        model=tts_model,
        voice=tts_voice,
        input=text,
        response_format="wav",   # актуальный параметр
    )

    out_path = os.path.abspath("tts_test.wav")
    with open(out_path, "wb") as f:
        f.write(speech.content)
    print("Файл сохранён:", out_path)

    # Проигрываем БЕЗ pydub, чтобы не трогать Temp
    data, samplerate = sf.read(out_path, dtype="float32")
    print("Проигрываю…")
    sd.play(data, samplerate)
    sd.wait()
    print("Готово ✅")

if __name__ == "__main__":
    main()
