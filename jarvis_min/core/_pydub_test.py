from pydub.generators import Sine
from pydub.playback import play

print("▶ Тестовый тон 440 Гц, 1 сек...")
tone = Sine(440).to_audio_segment(duration=1000)
play(tone)
print("✅ Проверка завершена.")
