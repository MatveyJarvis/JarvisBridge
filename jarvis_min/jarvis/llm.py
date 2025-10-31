
from openai import OpenAI
from .config import settings

_client = None

def client() -> OpenAI:
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY пуст. Заполните .env")
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client

def chat(system: str, user: str) -> str:
    c = client()
    resp = c.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role":"system", "content": system},
            {"role":"user", "content": user},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content or ""
