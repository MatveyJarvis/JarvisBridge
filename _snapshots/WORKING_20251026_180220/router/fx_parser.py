# -*- coding: utf-8 -*-
"""
fx_parser.py — устойчивый парсер валютных запросов (RU/EN) для жёсткой маршрутизации.

Выдаёт нормализованную структуру:
  FxParseResult(base="USD", quote="BYN", amount=100.0, date_iso="2025-10-14")

Особенности:
  - Понимает пары: "USD/RUB", "usd rub", "eur к rub", "евро к рублю".
  - Понимает конверсию: "сколько будет 100 usd в byn", "convert 50 eur to rub".
  - Распознаёт суммы: целые и дробные ("," или ".") — числа из ДАТЫ не считаем суммой.
  - Даты: "сегодня", "на вчера", "вчера", "10.10.2025", "10.10.25".
  - Без внешних пакетов. Имеет встроенный словарь синонимов валют (fallback).
    Если будет файл router/currency_map.json — можно расширить маппинг там.

Публичная функция:
  parse_fx_query(text: str, locale="ru-RU", default_quote="BYN") -> FxParseResult | None
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

# --- Результат парсинга ---------------------------------------------------------

@dataclass
class FxParseResult:
    base: Optional[str] = None     # "USD"
    quote: Optional[str] = None    # "BYN"
    amount: Optional[float] = None # 100.0
    date_iso: Optional[str] = None # "YYYY-MM-DD"


# --- Встроенный fallback-словарь валют -----------------------------------------

_FALLBACK_CCY_MAP: Dict[str, str] = {
    # ISO
    "usd":"USD","eur":"EUR","rub":"RUB","byn":"BYN","kzt":"KZT","cny":"CNY","pln":"PLN",
    "chf":"CHF","try":"TRY","jpy":"JPY","gbp":"GBP","uah":"UAH","aed":"AED","hkd":"HKD",
    "sgd":"SGD","aud":"AUD","cad":"CAD","nzd":"NZD","kgs":"KGS","uzs":"UZS",
    # RU/варианты
    "доллар":"USD","доллара":"USD","долларов":"USD","бакс":"USD","баксов":"USD","баксы":"USD",
    "евро":"EUR",
    "рубль":"RUB","рубля":"RUB","рублей":"RUB","российский рубль":"RUB","рос рубль":"RUB",
    "бел рубль":"BYN","бел.рубль":"BYN","белруб":"BYN","бел.руб":"BYN","беларуский рубль":"BYN",
    "белорусский рубль":"BYN","белорусский":"BYN","белорусских":"BYN","руб byn":"BYN",
    "йена":"JPY","иена":"JPY",
    "юань":"CNY","злотый":"PLN","франк":"CHF","лира":"TRY","тенге":"KZT",
    # EN words
    "dollar":"USD","euro":"EUR","ruble":"RUB","russian ruble":"RUB","belarusian ruble":"BYN",
    "yuan":"CNY","yen":"JPY","lira":"TRY","franc":"CHF","zloty":"PLN","tenge":"KZT",
}

def _load_external_map() -> Dict[str, str]:
    path = os.path.join(os.path.dirname(__file__), "currency_map.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return {str(k).lower(): str(v).upper() for k, v in data.items()}
        except Exception:
            pass
    return {}

_EXT_MAP = _load_external_map()
_CCY_MAP: Dict[str, str] = {**_FALLBACK_CCY_MAP, **_EXT_MAP}

# --- Вспомогательные ------------------------------------------------------------

_DATE_PAT = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b")

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())

def _to_code(token: str) -> Optional[str]:
    t = token.strip().lower()
    if re.fullmatch(r"[a-z]{3}", t):
        return t.upper()
    return _CCY_MAP.get(t)

def _strip_dates(text: str) -> str:
    # вырезаем даты, чтобы числа внутри не считались суммой
    return _DATE_PAT.sub(" ", text)

def _find_amount(text: str) -> Optional[float]:
    # сначала убираем даты
    t_wo_dates = _strip_dates(text)
    # возможные конструкции "на 100", "за 50" — всё равно это сумма
    m = re.search(r"(\d+(?:[.,]\d+)?)", t_wo_dates)
    if not m:
        return None
    val = m.group(1).replace(",", ".")
    try:
        return float(val)
    except Exception:
        return None

def _parse_date_ru(text: str) -> Optional[str]:
    t = _norm(text)
    today = datetime.now().date()
    if "сегодня" in t:
        return today.isoformat()
    if "вчера" in t or "на вчера" in t:
        return (today - timedelta(days=1)).isoformat()
    m = _DATE_PAT.search(t)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100:
            y += 2000
        try:
            return datetime(y, mo, d).date().isoformat()
        except Exception:
            return None
    return None

def _extract_two_ccy_by_pair(text: str) -> Optional[Tuple[str, str]]:
    m = re.search(r"\b([A-Za-z]{3})\s*/\s*([A-Za-z]{3})\b", text, flags=re.IGNORECASE)
    if m:
        return m.group(1).upper(), m.group(2).upper()
    m2 = re.search(r"\b([A-Za-z]{3})\s+([A-Za-z]{3})\b", text, flags=re.IGNORECASE)
    if m2:
        return m2.group(1).upper(), m2.group(2).upper()
    return None

def _scan_currency_in_chunk(chunk: str) -> Optional[str]:
    m = re.search(r"\b([A-Za-z]{3})\b", chunk)
    if m:
        c = _to_code(m.group(1))
        if c:
            return c
    for n in (3, 2, 1):
        pat = r"(?:\b\w+\b\s*){" + str(n) + r"}"
        for m2 in re.finditer(pat, chunk):
            candidate = _norm(m2.group(0))
            if candidate in _CCY_MAP:
                return _CCY_MAP[candidate]
    chunk2 = chunk.replace(".", " ")
    if chunk2 != chunk:
        return _scan_currency_in_chunk(chunk2)
    return None

def _scan_all_currencies(text: str):
    found = []
    for m in re.finditer(r"\b([A-Za-z]{3})\b", text):
        c = _to_code(m.group(1))
        if c and c not in found:
            found.append(c)
    words = re.findall(r"\b[\w\.]+\b", text)
    for n in (3, 2, 1):
        for i in range(len(words) - n + 1):
            cand = _norm(" ".join(words[i:i+n]).replace(".", " "))
            code = _CCY_MAP.get(cand)
            if code and code not in found:
                found.append(code)
    return found

# --- Основной парсер ------------------------------------------------------------

def parse_fx_query(
    text: str,
    *,
    locale: str = "ru-RU",
    default_quote: str = "BYN",
) -> Optional[FxParseResult]:
    if not text or not text.strip():
        return None
    t = _norm(text)

    date_iso = _parse_date_ru(t) if locale.startswith("ru") else None
    amount = _find_amount(t)

    base = None
    quote = None

    pair = _extract_two_ccy_by_pair(t)
    if pair:
        base, quote = pair
    else:
        # свободная форма: «евро к рублю», «yen to usd», и т.д.
        m = re.search(r"(.+?)\s+(?:к|в|to|in)\s+(.+)$", t)
        if m:
            left, right = m.group(1), m.group(2)
            base = _scan_currency_in_chunk(left)
            quote = _scan_currency_in_chunk(right)
        else:
            codes = _scan_all_currencies(t)
            if len(codes) >= 2:
                base, quote = codes[0], codes[1]
            elif len(codes) == 1:
                base, quote = codes[0], default_quote

    # если указана только одна валюта
    if base and not quote:
        quote = default_quote
    elif quote and not base:
        base, quote = quote, base or default_quote

    return FxParseResult(base=base, quote=quote, amount=amount, date_iso=date_iso)

# --- Ручной запуск --------------------------------------------------------------

if __name__ == "__main__":
    samples = [
        "Курс доллара к рублю",
        "eur/rub на вчера",
        "сколько будет 100 usd в byn",
        "usd eur",
        "Convert 50 EUR to RUB",
        "курс евро 10.10.2025",
        "бакс к бел рублю",
        "сколько будет 250 баксов в бел.рублях сегодня",
        "GBP USD",
        "йена к доллару",
        "сколько будет 99,5 евро в рублях",
    ]
    for s in samples:
        r = parse_fx_query(s, locale="ru-RU", default_quote="BYN")
        print("---")
        print(s)
        print(r)
