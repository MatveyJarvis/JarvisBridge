# -*- coding: utf-8 -*-
"""
run_222.py — финальный тест-раннер блока 2.2.2 (a+b+c)

Назначение:
  - Читает dialog.jsonl → каждый запрос → проверяет маршрутизацию через fx_router.
  - Использует фикстуры forex_samples.json для имитации ответа инструмента.
  - Прогоняет результат через i18n/formatter → печатает короткий отчёт.
  - Проверяет, что все FX-запросы идут строго через tool:forex (source="tool").

Ожидаемый результат:
  - Для всех кейсов: RouteDecision.target == "tool:forex".
  - Финальный счётчик: "✅ N/N PASSED".
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict

# --- Путь к корню проекта -------------------------------------------------------
# Делаем это ДО импортов пакетов router/ i18n
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# --- Теперь можно импортировать пакеты -----------------------------------------
from router.fx_router import detect_and_route
from i18n.formatter import format_rate, format_conversion

# --- Пути к тестовым данным -----------------------------------------------------
DIALOG_PATH = os.path.join(ROOT, "tests", "fx", "dialog.jsonl")
FIXTURES_PATH = os.path.join(ROOT, "tests", "fx", "fixtures", "forex_samples.json")


# --- Загрузка данных ------------------------------------------------------------
def _load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _load_jsonl(path: str) -> list[Dict[str, Any]]:
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


# --- Логика тестов --------------------------------------------------------------
def run_tests() -> None:
    dialogs = _load_jsonl(DIALOG_PATH)
    fx_data = _load_json(FIXTURES_PATH)

    total = len(dialogs)
    passed = 0

    print(f"=== FX Routing & Formatting Test ({total} cases) ===\n")

    for d in dialogs:
        text = d["text"]
        expected_route = d["expected_route"]
        expected_intent = d["expected_intent"]

        route = detect_and_route(text)
        if not route:
            print(f"❌ No route for: {text}\n")
            continue

        ok = True
        if route.target != expected_route:
            print(f"❌ Wrong route for: {text} (got {route.target}, expected {expected_route})")
            ok = False
        if route.intent != expected_intent:
            print(f"❌ Wrong intent for: {text} (got {route.intent}, expected {expected_intent})")
            ok = False

        payload = route.payload
        base = payload.get("base")
        quote = payload.get("quote")
        amount = payload.get("amount")
        date_iso = payload.get("date")

        key = f"{base}_{quote}" if base and quote else None
        fx = fx_data.get(key) if key else None

        if fx:
            rate = fx["rate"]
            if route.intent == "fx.convert" and amount is not None:
                formatted = format_conversion(base, quote, rate, amount, date_iso=date_iso)
            else:
                formatted = format_rate(base, quote, rate, date_iso=date_iso)
        else:
            formatted = f"[Нет данных о паре {key}]"

        if ok:
            passed += 1
            print(f"✅ {text}\n→ {formatted}\n")
        else:
            print(f"⚠️  {text}\n→ {formatted}\n")

    print(f"=== РЕЗУЛЬТАТ: {passed}/{total} PASSED ===")


# --- Запуск ---------------------------------------------------------------------
if __name__ == "__main__":
    run_tests()
