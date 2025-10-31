import sounddevice as sd
import soundfile as sf
import numpy as np
import os

# Настройки
fs = 44100           # частота дискретизации
seconds = 3          # длительность записи

# Если нужно указать устройства вручную — раскомментируй строку ниже:
# sd.default.device = (МИКРОФОН_ИНДЕКС, КОЛОНКИ_ИНДЕКС)

print("🎙 Запись 3 секунды... Говори что-нибудь:")
audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='float32')
sd.wait()

# Сохраняем WAV-файл
filename = os.path.abspath("test_record.wav")
sf.write(filename, audio, fs)
print(f"✅ Файл сохранён: {filename}")

print("🔊 Воспроизвожу запись...")
sd.play(audio, fs)
sd.wait()
print("Готово ✅")
