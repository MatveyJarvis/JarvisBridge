import sounddevice as sd
import soundfile as sf

device_index = 1  # индекс твоего микрофона (Realtek)
samplerate = 48000
duration = 5  # секунд

print("🎙️ Запись... Говори обычным голосом (5 секунд)")
audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='float32', device=device_index)
sd.wait()
sf.write("mic_test.wav", audio, samplerate)
print("✅ Запись завершена. Файл mic_test.wav создан в папке C:\\JarvisBridge")
