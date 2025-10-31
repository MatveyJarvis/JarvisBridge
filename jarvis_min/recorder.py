# recorder.py — запись аудио с микрофона (wav)
import sounddevice as sd
import wave

def record_wav(filename: str = "input.wav", seconds: int = 5, samplerate: int = 44100):
    """
    Записывает голос с микрофона и сохраняет в WAV.
    """
    print(f"[Recorder] Запись {seconds} сек...")
    data = sd.rec(int(seconds * samplerate), samplerate=samplerate, channels=1, dtype="int16")
    sd.wait()
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(data.tobytes())
    print(f"[Recorder] Сохранено: {filename}")
    return filename

if __name__ == "__main__":
    record_wav("test.wav", 3)
