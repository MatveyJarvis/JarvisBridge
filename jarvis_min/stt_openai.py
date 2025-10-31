from __future__ import annotations
import os, pathlib
from openai import OpenAI

def transcribe(path: str) -> str:
    # Берём ключ из .env (venv уже активен, .env лежит тут же)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY пуст. Заполни .env")

    client = OpenAI(api_key=api_key)
    audio_path = pathlib.Path(path)

    with audio_path.open("rb") as f:
        # Если у тебя в проекте используется другая модель — напишем её в .env и подставим тут
        model = os.getenv("OPENAI_STT_MODEL", "gpt-4o-transcribe")
        resp = client.audio.transcriptions.create(model=model, file=f)

    return resp.text
