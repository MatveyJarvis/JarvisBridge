import pyttsx3, time

engine = pyttsx3.init()
voices = engine.getProperty('voices')

print("🔊 Найденные голоса:\n")

for i, v in enumerate(voices, 1):
    print(f"{i}. ID: {v.id}")
    print(f"   Name: {v.name}")
    print(f"   Lang: {v.languages if hasattr(v, 'languages') else '—'}")
    print(f"   Gender: {getattr(v, 'gender', '—')}")
    print("   ▶ Озвучиваю пример...")
    engine.setProperty('voice', v.id)
    engine.say(f"Это пример речи голоса номер {i}")
    engine.runAndWait()
    time.sleep(0.5)

print("\n✅ Тест завершён. Выберите понравившийся голос и вставьте его имя или часть ID в .env, например:")
print("TTS_VOICE=Irina")
