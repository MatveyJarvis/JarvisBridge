# tools.py
# v2.2.2 — инструменты: погода и курс валют (фикс парсера курсов)

import re
import requests
from typing import Optional, Tuple

# ----------- Weather -----------

def _norm_city(q: str) -> str:
    return re.sub(r"\s+", " ", q or "").strip()

def _parse_weather_phrase(text: str) -> Optional[Tuple[str, Optional[str]]]:
    """
    Возвращает (city, when) где when ∈ {None, 'today','tomorrow'}
    Примеры: "погода в минске", "какая погода в москве завтра"
    """
    t = (text or "").lower()
    m = re.search(r"погода\s+в\s+([a-zа-яё .\-]+)", t, flags=re.IGNORECASE)
    if not m:
        return None
    city = _norm_city(m.group(1))
    when = None
    if "завтра" in t:
        when = "tomorrow"
    elif "сегодня" in t:
        when = "today"
    return (city, when)

def _weather(city: str, when: Optional[str], timeout: int = 8) -> Optional[str]:
    try:
        url = f"https://wttr.in/{city}?format=j1"
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "JarvisBridge/2.2.2"})
        r.raise_for_status()
        data = r.json()
        if "current_condition" not in data or "weather" not in data:
            return None

        if when == "tomorrow":
            day = data["weather"][1] if len(data.get("weather", [])) > 1 else data["weather"][0]
            avg = day.get("avgtempC")
            hourly = day.get("hourly", [])
            desc = ""
            if hourly:
                mid = hourly[min(4, len(hourly) - 1)]
                desc = (mid.get("weatherDesc") or [{"value": ""}])[0]["value"]
            return f"Завтра в {city}: около {avg}°C, {desc}."
        else:
            cur = data["current_condition"][0]
            temp = cur.get("temp_C")
            feels = cur.get("FeelsLikeC")
            desc = (cur.get("weatherDesc") or [{"value": ""}])[0]["value"]
            return f"Сейчас в {city}: {temp}°C, ощущается как {feels}°C, {desc}."
    except Exception:
        return None

# ----------- Currency -----------

_RU2ISO = {
    "доллар": "USD", "доллара": "USD", "доллару": "USD", "доллары": "USD",
    "евро": "EUR",
    "рубль": "RUB", "рубля": "RUB", "рублю": "RUB", "рублей": "RUB", "руб": "RUB",
    "фунт": "GBP", "фунта": "GBP", "фунтов": "GBP",
    "йена": "JPY", "иена": "JPY", "йены": "JPY",
}

_ISO = ("USD", "EUR", "RUB", "GBP", "JPY")

def _to_code(token: str) -> str:
    if not token:
        return ""
    x = token.strip().upper()
    if x in _ISO:
        return x
    return _RU2ISO.get(token.strip().lower(), "")

def _parse_rate_phrase(text: str) -> Optional[Tuple[str, str]]:
    """
    Примеры:
      - 'курс доллара к рублю'
      - 'курс eur к usd'
      - 'курс евро к доллару'
    Возвращает (base, quote) как коды ISO.
    """
    t = (text or "").lower()
    # Именованные группы, без вложенных захватов
    pattern = (
        r"курс\s+(?P<base>(?:[a-z]{3}|[a-zа-яё]+))\s+к\s+(?P<quote>(?:[a-z]{3}|[a-zа-яё]+))"
    )
    m = re.search(pattern, t, flags=re.IGNORECASE)
    if not m:
        return None

    base_raw = m.group("base")
    quote_raw = m.group("quote")

    base = _to_code(base_raw)
    quote = _to_code(quote_raw)

    if base and quote and base != quote:
        return (base, quote)
    return None

def _rate(base: str, quote: str, timeout: int = 8) -> Optional[str]:
    try:
        url = f"https://api.exchangerate.host/latest?base={base}&symbols={quote}"
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        js = r.json()
        rate = (js.get("rates") or {}).get(quote)
        if not rate:
            return None
        dt = js.get("date")
        return f"Курс {base}/{quote}: {rate:.4f} (на {dt})."
    except Exception:
        return None

# ----------- Router -----------

def try_tool_answer(text: str, timeout: int = 8) -> Optional[str]:
    """Пытаемся ответить инструментами. Возвращает строку или None."""
    # Weather
    w = _parse_weather_phrase(text)
    if w:
        city, when = w
        ans = _weather(city, when, timeout=timeout)
        if ans:
            return ans

    # Currency
    r = _parse_rate_phrase(text)
    if r:
        base, quote = r
        ans = _rate(base, quote, timeout=timeout)
        if ans:
            return ans

    return None
