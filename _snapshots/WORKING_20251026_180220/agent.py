# -*- coding: utf-8 -*-
"""
agent.py вЂ” РјРёРЅРёРјР°Р»СЊРЅС‹Р№ Р°РіРµРЅС‚ СЃ СЂСѓСЃСЃРєРѕР№ Р»РѕРєР°Р»СЊСЋ
- Р’СЃРµРіРґР° РѕС‚РІРµС‡Р°РµС‚ РїРѕ-СЂСѓСЃСЃРєРё (system prompt)
- Р•СЃР»Рё РѕС‚РІРµС‚ вЂ” С‡РёСЃР»Рѕ, РїСЂРѕРёР·РЅРѕСЃРёС‚ РµРіРѕ РЎР›РћР’РћРњ РїРѕ-СЂСѓСЃСЃРєРё (С‡С‚РѕР±С‹ TTS РЅРµ С‡РёС‚Р°Р» "four")
"""

import os
import re
from dotenv import load_dotenv

# OpenAI client (РЅРѕРІС‹Р№ SDK)
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
        raise RuntimeError("OPENAI_API_KEY РїСѓСЃС‚ РІ .env")

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


# РѕС‡РµРЅСЊ РєРѕСЂРѕС‚РєРёР№ РјР°РїРїРµСЂ С‡РёСЃРµР» в†’ СЂСѓСЃСЃРєРёРµ СЃР»РѕРІР° (С…РІР°С‚Р°РµС‚ РґР»СЏ Р±Р°Р·РѕРІС‹С… РїСЂРѕРІРµСЂРѕРє)
_NUMS = {
    0: "РЅРѕР»СЊ", 1: "РѕРґРёРЅ", 2: "РґРІР°", 3: "С‚СЂРё", 4: "С‡РµС‚С‹СЂРµ", 5: "РїСЏС‚СЊ",
    6: "С€РµСЃС‚СЊ", 7: "СЃРµРјСЊ", 8: "РІРѕСЃРµРјСЊ", 9: "РґРµРІСЏС‚СЊ", 10: "РґРµСЃСЏС‚СЊ",
    11: "РѕРґРёРЅРЅР°РґС†Р°С‚СЊ", 12: "РґРІРµРЅР°РґС†Р°С‚СЊ", 13: "С‚СЂРёРЅР°РґС†Р°С‚СЊ", 14: "С‡РµС‚С‹СЂРЅР°РґС†Р°С‚СЊ",
    15: "РїСЏС‚РЅР°РґС†Р°С‚СЊ", 16: "С€РµСЃС‚РЅР°РґС†Р°С‚СЊ", 17: "СЃРµРјРЅР°РґС†Р°С‚СЊ", 18: "РІРѕСЃРµРјРЅР°РґС†Р°С‚СЊ",
    19: "РґРµРІСЏС‚РЅР°РґС†Р°С‚СЊ", 20: "РґРІР°РґС†Р°С‚СЊ", 30: "С‚СЂРёРґС†Р°С‚СЊ", 40: "СЃРѕСЂРѕРє",
    50: "РїСЏС‚СЊРґРµСЃСЏС‚", 60: "С€РµСЃС‚СЊРґРµСЃСЏС‚", 70: "СЃРµРјСЊРґРµСЃСЏС‚", 80: "РІРѕСЃРµРјСЊРґРµСЃСЏС‚",
    90: "РґРµРІСЏРЅРѕСЃС‚Рѕ", 100: "СЃС‚Рѕ"
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
    # РµСЃР»Рё РѕС‚РІРµС‚ вЂ” С‚РѕР»СЊРєРѕ С‡РёСЃР»Рѕ (СЃ С‚РѕС‡РєРѕР№/РїСЂРѕР±РµР»Р°РјРё) в†’ РѕР·РІСѓС‡РёРј СЃР»РѕРІРѕРј
    m = re.fullmatch(r"[\s\(]*([-+]?\d{1,4})[\s\.\)]*", s)
    if m:
        try:
            val = int(m.group(1))
            return _num_to_ru(val)
        except Exception:
            return s
    # РёРЅР°С‡Рµ вЂ” РіР°СЂР°РЅС‚РёСЏ СЂСѓСЃСЃРєРѕР№ С‚РѕС‡РєРё/С„РѕСЂРјР°С‚Р°
    return s


def run_agent(user_text: str) -> str:
    load_dotenv()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
    response_lang = os.getenv("RESPONSE_LANG", "ru").strip().lower()

    client, kind = _client()

    system_msg = (
        "РўС‹ РіРѕР»РѕСЃРѕРІРѕР№ Р°СЃСЃРёСЃС‚РµРЅС‚. РћС‚РІРµС‡Р°Р№ РљР РђРўРљРћ Рё РўРћР›Р¬РљРћ РїРѕ-СЂСѓСЃСЃРєРё. "
        "Р•СЃР»Рё РІРѕРїСЂРѕСЃ вЂ” РїСЂРѕСЃС‚Р°СЏ Р°СЂРёС„РјРµС‚РёРєР°, РѕС‚РІРµС‚ РґР°Р№ РѕРґРЅРёРј СЃР»РѕРІРѕРј РЅР° СЂСѓСЃСЃРєРѕРј "
        "(РЅР°РїСЂРёРјРµСЂ: В«С‡РµС‚С‹СЂРµВ», В«С€РµСЃС‚РЅР°РґС†Р°С‚СЊВ»)."
    )

    # --- Р’С‹Р·РѕРІ РјРѕРґРµР»Рё
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

    # РџРѕСЃС‚РѕР±СЂР°Р±РѕС‚РєР° РґР»СЏ СЂСѓСЃСЃРєРѕР№ РѕР·РІСѓС‡РєРё С‡РёСЃРµР»
    text_ru = _postprocess_ru(text)

    # РћР·РІСѓС‡РёРІР°РµРј
# [disabled] tts_say(text_ru)

    return text_ru
