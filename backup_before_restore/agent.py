# -*- coding: utf-8 -*-
"""
agent.py — минимальный агент с русской локалью
- Всегда отвечает по-русски (system prompt)
- Если ответ — число, произносит его СЛОВОМ по-русски (чтобы TTS не читал "four")
"""

import os
import re
from dotenv import load_dotenv

# OpenAI client (новый SDK)
try:
    from openai import OpenAI
except Exception:
    OpenAI = None
    import openai as openai_legacy

from tts_openai import say as tts_say


def _client():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    project_id = os.getenv("OPENAI_PROJECT_ID", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY пуст в .env")

    if OpenAI is not None:
        kwargs = {"api_key": api_key}
        if project_id:
            kwargs["project"] = project_id
        return OpenAI(**kwargs), "new"
    else:
        openai_legacy.api_key = api_key
        if project_id:
            try:
                openai_legacy.organization = project_id
            except Exception:
                pass
        return openai_legacy, "legacy"


# очень короткий маппер чисел → русские слова (хватает для базовых проверок)
_NUMS = {
    0: "ноль", 1: "один", 2: "два", 3: "три", 4: "четыре", 5: "пять",
    6: "шесть", 7: "семь", 8: "восемь", 9: "девять", 10: "десять",
    11: "одиннадцать", 12: "двенадцать", 13: "тринадцать", 14: "четырнадцать",
    15: "пятнадцать", 16: "шестнадцать", 17: "семнадцать", 18: "восемнадцать",
    19: "девятнадцать", 20: "двадцать", 30: "тридцать", 40: "сорок",
    50: "пятьдесят", 60: "шестьдесят", 70: "семьдесят", 80: "восемьдесят",
    90: "девяносто", 100: "сто"
}
def _num_to_ru(n: int) -> str:
    if n in _NUMS:
        return _NUMS[n]
    if 21 <= n < 100:
        d, r = divmod(n, 10)
        tens = _NUMS[d*10]
        return tens if r == 0 else f"{tens} {_NUMS[r]}"
    return str(n)  # fallback

def _postprocess_ru(text: str) -> str:
    s = (text or "").strip()
    # если ответ — только число (с точкой/пробелами) → озвучим словом
    m = re.fullmatch(r"[\s\(]*([-+]?\d{1,4})[\s\.\)]*", s)
    if m:
        try:
            val = int(m.group(1))
            return _num_to_ru(val)
        except Exception:
            return s
    # иначе — гарантия русской точки/формата
    return s


def run_agent(user_text: str) -> str:
    load_dotenv()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
    response_lang = os.getenv("RESPONSE_LANG", "ru").strip().lower()

    client, kind = _client()

    system_msg = (
        "Ты голосовой ассистент. Отвечай КРАТКО и ТОЛЬКО по-русски. "
        "Если вопрос — простая арифметика, ответ дай одним словом на русском "
        "(например: «четыре», «шестнадцать»)."
    )

    # --- Вызов модели
    if kind == "new":
        resp = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_text},
            ],
        )
        text = (resp.choices[0].message.content or "").strip()
    else:
        resp = client.ChatCompletion.create(
            model=model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_text},
            ],
        )
        text = (resp["choices"][0]["message"]["content"] or "").strip()

    # Постобработка для русской озвучки чисел
    text_ru = _postprocess_ru(text)

    # Озвучиваем
    tts_say(text_ru)

    return text_ru
