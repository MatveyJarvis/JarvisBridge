import speech_recognition as sr
r = sr.Recognizer()
with sr.Microphone() as source:
    print("Говори что-нибудь...")
    audio = r.listen(source)
    print("Распознано:")
    print(r.recognize_google(audio, language="ru-RU"))
