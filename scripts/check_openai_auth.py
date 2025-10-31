# C:\JarvisBridge\scripts\check_openai_auth.py
import os, textwrap
from dotenv import load_dotenv
from openai import OpenAI
from httpx import HTTPStatusError

def mask(key: str) -> str:
    if not key:
        return "(пусто)"
    return f"{key[:6]}...{key[-4:]} (len={len(key)})"

def main():
    load_dotenv()
    key = os.getenv("OPENAI_API_KEY", "")
    print("OPENAI_API_KEY =", mask(key))

    if not key:
        print("❌ Ключ не найден в .env. Проверь файл .env и строку OPENAI_API_KEY=...")
        return

    try:
        client = OpenAI(api_key=key)
        # пробный запрос на список моделей — самый простой auth-check
        models = list(client.models.list())
        print(f"✅ Auth OK. Доступно моделей: {len(models)}")
    except HTTPStatusError as e:
        print("❌ HTTP error:", e.response.status_code, e.response.text)
    except Exception as e:
        print("❌ Error:", repr(e))

if __name__ == "__main__":
    main()
