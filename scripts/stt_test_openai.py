# C:\JarvisBridge\scripts\stt_test_openai.py
import os
from dotenv import load_dotenv
from openai import OpenAI
import sounddevice as sd
import soundfile as sf
import numpy as np

def record_wav(path: str, seconds: int = 5, samplerate: int = 16000):
    """Записывает моно WAV с микрофона."""
    print(f"🎙 Запись {seconds} сек… Говори что-нибудь.")
    audio = sd.rec(int(seconds * samplerate), samplerate=samplerate, channels=1, dtype="float32")
    sd.wait()
    # Конвертируем в int16 для стабильности
    audio_int16 = (audio * np.iinfo(np.int16).max).astype(np.int16)
    sf.write(path, audio_int16, samplerate, subtype="PCM_16")
    print(f"✅ Сохранено: {path}")

def speak(text: str, out_path: str = "stt_tts.wav"):
    """Озвучивает текст через OpenAI TTS и проигрывает через sounddevice."""
    client = OpenAI()
    tts_model = os.getenv("OPENAI_TTS_MODEL", "tts-1")
    tts_voice = os.getenv("OPENAI_TTS_VOICE", "alloy")

    print(f"🔊 Озвучиваю: {text!r}")
    speech = client.audio.speech.create(
        model=tts_model,
        voice=tts_voice,
        input=text,
        response_format="wav",
    )
    with open(out_path, "wb") as f:
        f.write(speech.content)

    data, sr = sf.read(out_path, dtype="float32")
    sd.play(data, sr)
    sd.wait()
    print("Готово ✅")

def main():
    load_dotenv()

    # 1) Запись
    wav_path = os.path.abspath("stt_test.wav")
    seconds = int(os.getenv("RECORD_SECONDS", "5"))
    record_wav(wav_path, seconds=seconds, samplerate=16000)

    # 2) Транскрибируем
    client = OpenAI()
    stt_model = os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-transcribe")
    print(f"🧠 Распознаю речь: модель={stt_model} …")
    with open(wav_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model=stt_model,
            file=f,
        )
    text = getattr(result, "text", "").strip()
    print("📝 Распознано:", text or "(пусто)")

    # 3) Озвучиваем ответ
    reply = f"Ты сказал: {text}" if text else "Я не расслышал. Давай ещё раз?"
    speak(reply)

if __name__ == "__main__":
    main()
