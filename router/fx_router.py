# -*- coding: utf-8 -*-
"""
fx_router.py — жёсткая маршрутизация валютных запросов строго в инструмент forex_tool.

Назначение:
  - Детектировать намерение FX (курс/конверсия) по RU/EN фразам и шаблонам пар.
  - Спарсить базовые поля через fx_parser (base, quote, amount?, date?).
  - Вернуть RouteDecision с target="tool:forex" и высокой уверенностью.
  - Если это не FX — вернуть None (пусть обработает общий роутер/LLM).

Файл самодостаточный, без внешних пакетов (stdlib). Зависит только от:
  - router/fx_parser.py
  - router/currency_map.json (используется внутри fx_parser)

Ручная проверка:
  1) Активируй venv и запусти файл напрямую:
     cd C:\JarvisBridge
     .\.venv\Scripts\activate
     python -X utf8 -u .\router\fx_router.py
  2) Ожидаемый признак успеха — для тестовых фраз печатаются dict-объекты с:
     target="tool:forex", intent="fx.rate" или "fx.convert", confidence≈0.88–0.92.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

# Импорт локального парсера
try:
    from .fx_parser import parse_fx_query, FxParseResult
except Exception:
    # Если модуль запускают напрямую
    from fx_parser import parse_fx_query, FxParseResult  # type: ignore


# --- Модель решения маршрутизации ------------------------------------------------

@dataclass
class RouteDecision:
    target: str              # "tool:forex"
    intent: str              # "fx.rate" | "fx.convert" | "fx.unknown"
    payload: Dict[str, Any]  # {base, quote, amount?, date?, raw?}
    reason: str              # короткое объяснение
    confidence: float        # 0..1

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# --- Ключевые паттерны для быстрого детекта намерения ---------------------------

# Базовые ключевые слова (RU/EN), указывающие на FX
_KEYWORDS = (
    r"курс|обмен|конверт(ируй|ировать|ация)|сколько\s+будет|во\s+что|в\s+чём|"
    r"доллар|бакс|евро|рубл|тенге|юань|злот|франк|лир[аы]|йена|иен[аы]|сомон|"
    r"usd|eur|rub|byn|kzt|cny|pln|chf|try|jpy|kgs|uzs|uah|gbp|aud|cad|nzd|aed|hkd|sgd|"
    r"exchange\s*rate|fx|convert|conversion|how\s+much\s+is"
)

# Паттерны вида пары: с косой чертой или через пробел
_PAIR_HINTS = (
    r"[A-Za-z]{3}\s*/\s*[A-Za-z]{3}",
    r"\b[A-Za-z]{3}\s+[A-Za-z]{3}\b",
)


def _looks_like_fx(text: str) -> bool:
    t = text.lower()
    if re.search(_KEYWORDS, t):
        return True
    for p in _PAIR_HINTS:
        if re.search(p, t, flags=re.IGNORECASE):
            return True
    # Евро/доллар/рубль в склонениях без явного «курс»
    if re.search(r"\b(евро|доллар(а|ов)?|рубл[ьяе]?)\b", t):
        return True
    return False


# --- Публичный API ---------------------------------------------------------------

def detect_and_route(
    text: str,
    *,
    locale: str = "ru-RU",
    default_quote: str = "BYN",
) -> Optional[RouteDecision]:
    """
    Возвращает:
      - RouteDecision(target="tool:forex", ...) — если обнаружен FX.
      - None — если это не FX.

    Аргументы:
      text          — пользовательская фраза
      locale        — "ru-RU" | "en-US"
      default_quote — если сказали «сколько будет 100 USD» без quote
    """
    if not text or not text.strip():
        return None

    # 1) Быстрый детект намерения
    if not _looks_like_fx(text):
        return None

    # 2) Полный парсинг
    parsed: Optional[FxParseResult] = parse_fx_query(
        text=text,
        locale=locale,
        default_quote=default_quote,
    )

    if not parsed or not parsed.base or not parsed.quote:
        # Детект есть, но парсер не уверен — всё равно шлём в tool с минимальным payload
        payload = {
            "text": text,
            "base": getattr(parsed, "base", None),
            "quote": getattr(parsed, "quote", None),
            "amount": getattr(parsed, "amount", None),
            "date": getattr(parsed, "date_iso", None),
        }
        return RouteDecision(
            target="tool:forex",
            intent="fx.unknown",
            payload=payload,
            reason="FX intent detected, but parser is uncertain",
            confidence=0.60,
        )

    # 3) Intent: конверсия (есть amount) или просто курс
    intent = "fx.convert" if parsed.amount is not None else "fx.rate"

    payload = {
        "base": parsed.base,          # напр., "USD"
        "quote": parsed.quote,        # напр., "BYN"
        "amount": parsed.amount,      # float | None
        "date": parsed.date_iso,      # "YYYY-MM-DD" | None
        "raw": text,
    }

    # 4) Возврат решения
    return RouteDecision(
        target="tool:forex",
        intent=intent,
        payload=payload,
        reason="Strict FX route via fx_router (keywords/pair detected and parsed)",
        confidence=0.92 if intent == "fx.convert" else 0.88,
    )


# --- Ручной смок-тест ------------------------------------------------------------

if __name__ == "__main__":
    tests = [
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
    ]
    for q in tests:
        rd = detect_and_route(q)
        print("---")
        print(q)
        if rd:
            print(rd.to_dict())
        else:
            print("No FX route")
