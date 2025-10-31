import os
from dotenv import load_dotenv
from openai import OpenAI

def transcribe(path: str, language: str = "ru") -> str:
    """
    Распознаёт речь из файла WAV через OpenAI Whisper.
    """
    # гарантируем загрузку .env на момент вызова
    load_dotenv()

    model = os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-transcribe")
    # создаём клиент только тут, когда .env уже загружен
    client = OpenAI()

    with open(path, "rb") as f:
        resp = client.audio.transcriptions.create(
            model=model,
            file=f,
            language=language
        )
    text = getattr(resp, "text", "") or ""
    return text.strip()
