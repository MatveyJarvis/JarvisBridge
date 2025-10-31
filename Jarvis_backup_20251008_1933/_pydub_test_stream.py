import io, subprocess
from pydub.generators import Sine

print("▶ Тестовый тон 440 Гц, 1 сек...")

# Генерируем звук
tone = Sine(440).to_audio_segment(duration=1000)

# Экспортируем в память как WAV
buf = io.BytesIO()
tone.export(buf, format="wav")
data = buf.getvalue()

# Проигрываем через ffplay из stdin (без записи на диск)
subprocess.run(
    ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", "-"],
    input=data
)

print("✅ Проверка завершена.")
