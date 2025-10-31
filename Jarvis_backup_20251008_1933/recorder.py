import sounddevice as sd
import soundfile as sf
import numpy as np

def record_wav(path: str, seconds: int = 5, samplerate: int = 16000, channels: int = 1) -> str:
    """
    Запись аудио фиксированной длины в WAV (моно, 16 кГц).
    """
    print(f"▶ Начинаю запись на {seconds} сек...")
    audio = sd.rec(int(seconds * samplerate), samplerate=samplerate, channels=channels, dtype="float32")
    sd.wait()
    audio = np.clip(audio, -1.0, 1.0)
    sf.write(path, audio, samplerate, subtype="PCM_16")
    print("⏹️ Запись завершена.")
    return path
