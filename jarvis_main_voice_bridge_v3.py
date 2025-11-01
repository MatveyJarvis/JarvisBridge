# ===== Jarvis Voice Bridge v3 — стабильная версия после Этапа 3 =====
import os, datetime, time, openai, playsound, sounddevice as sd, wavio
from intents_offline import handle_offline_intent

openai.api_key = os.getenv("OPENAI_API_KEY")

def record_and_recognize():
    duration = 4
    fs = 16000
    print("[rec] Recording...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    filename = "C:\\JarvisBridge\\temp\\voice_in.wav"
    wavio.write(filename, audio, fs, sampwidth=2)
    with open(filename, "rb") as f:
        transcript = openai.Audio.transcriptions.create(model="whisper-1", file=f)
    return transcript.text.strip().lower()

def speak(text):`r`n    print("[tts]", text)`r`n    import requests, base64`r`n    url = "https://api.openai.com/v1/audio/speech"`r`n    headers = {"Authorization": f"Bearer {os.getenv(\"OPENAI_API_KEY\")}", "Content-Type": "application/json"}`r`n    payload = {"model": "gpt-4o-mini-tts", "voice": "alloy", "input": text}`r`n    response = requests.post(url, headers=headers, json=payload)`r`n    speech_file = "C:\\JarvisBridge\\temp\\tts_out.mp3"`r`n    with open(speech_file, "wb") as f: f.write(response.content)`r`n    playsound.playsound(speech_file)

def main():
    print("=== Jarvis Full (VAD=False) ===")
    speak("Готов к работе. Слушаю.")
    while True:
        text = record_and_recognize()
        print("[user]", text)
        if not text: continue
        if any(x in text for x in ["стоп", "спать", "пока"]):
            speak("До связи."); break
        offline = handle_offline_intent(text)
        if offline:
            speak(offline)
        else:
            resp = openai.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user","content":text}])
            speak(resp.choices[0].message.content)

if __name__ == "__main__":
    main()





