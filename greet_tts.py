import openai, os
openai.api_key = os.getenv("OPENAI_API_KEY")
resp = openai.audio.speech.create(model="gpt-4o-mini-tts", voice="alloy", input="Привет, я запущен, жду активацию.")
resp.stream_to_file("greet.mp3")
