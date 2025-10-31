# probe_voices.py
from pathlib import Path
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = "gpt-4o-mini-tts"
voices = ["alloy", "verse", "shimmer", "coral", "sage", "soft"]
out = Path("_out"); out.mkdir(exist_ok=True)

print(f"Model: {model}")
for v in voices:
    try:
        fn = out / f"probe_{v}.mp3"
        with client.audio.speech.with_streaming_response.create(
            model=model, voice=v, input=f"Test voice {v}."
        ) as resp:
            resp.stream_to_file(str(fn))
        print(f"OK: {v}")
    except Exception as e:
        print(f"NO: {v} -> {e.__class__.__name__}: {e}")
