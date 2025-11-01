import os
from openai import OpenAI
from pydub import AudioSegment
from pydub.playback import play
from dotenv import load_dotenv

# === Настройка окружения ===
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY", "").strip()
if not api_key:
    raise RuntimeError("❌ Не найден OPENAI_API_KEY в .env")

client = OpenAI(api_key=api_key)

# === Доступные голоса (OpenAI tts-1) ===
voices = ["alloy", "verse", "coral", "sage", "nova", "amber"]

print("=== Проверка голосов Джарвиса ===")
print("Вы можете выбрать любой из доступных вариантов:\n")
for v in voices:
    print(f"  • {v}")

# === Фраза для теста ===
text = "Привет, Кирилл! Это тест голоса Джарвиса. Всё работает отлично."

# === Генерация аудио-файлов ===
os.makedirs("tests/audio", exist_ok=True)

for v in voices:
    print(f"\n🎙 Генерирую голос: {v} ...")
    out_path = f"tests/audio/test_{v}.mp3"
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice=v,
        input=text
    ) as response:
        response.stream_to_file(out_path)
    print(f"✅ Сохранено: {out_path}")

print("\nВсе варианты готовы! Вы можете прослушать их вручную в tests/audio/")
