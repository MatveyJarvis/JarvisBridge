# === Greeting TTS ===
$py = @"
import openai, os
openai.api_key = os.getenv("OPENAI_API_KEY")
resp = openai.audio.speech.create(model="gpt-4o-mini-tts", voice="alloy", input="Привет, я запущен, жду активацию.")
resp.stream_to_file("greet.mp3")
"@
$py | Out-File -Encoding utf8 greet_tts.py
.\.venv\Scripts\python.exe .\greet_tts.py
Start-Process -WindowStyle Minimized -FilePath "wmplayer.exe" -ArgumentList '/play','/close',"$PWD\greet.mp3"
Start-Sleep -Seconds 2
# === Start Jarvis ===
.\run_hotword_plus_main_ru_fast.bak_stepB.ps1
