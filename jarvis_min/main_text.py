# main_text.py — текстовый режим Jarvis (ввод с клавиатуры → голосовой ответ)
from __future__ import annotations
import os
import dotenv
from openai import OpenAI
from tts_openai import say

dotenv.load_dotenv()

def ensure_env() -> str:
    api = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    if not api:
        raise RuntimeError("OPENAI_API_KEY пуст. Заполни .env")
    return model

def chat(model: str, user_text: str) -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Ты — Jarvis. Отвечай кратко и по делу."},
            {"role": "user", "content": user_text},
        ],
    )
    return resp.choices[0].message.content.strip()

def main():
    model = ensure_env()
    print("Текстовый режим Jarvis. Введи запрос (пустая строка или 'exit' — выход).")
    while True:
        q = input("> ").strip()
        if q.lower() in {"", "exit", "quit"}:
            break
        reply = chat(model, q)
        print(f"[LLM] {reply}")
        try:
            say(reply)
        except Exception as e:
            print(f"[TTS] ошибка воспроизведения: {e}")

if __name__ == "__main__":
    main()
