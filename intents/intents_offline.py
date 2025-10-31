# -*- coding: utf-8 -*-
"""
intents_offline.py — офлайн-интенты для Jarvis (микрошаг 3.1)
Функции:
  - время: "который час", "сколько времени", "время"
  - калькулятор: "9 плюс 3", "15 - 7", "6 умножить на 4", "8 разделить на 2"
  - погода из кеша: читает C:\JarvisBridge\temp\weather_cache.json (если есть)
Запуск теста:  python -X utf8 -u .\intents\intents_offline.py --test "9 плюс 3"
Никаких внешних библиотек не требуется.
"""
import argparse
import json
import math
import os
import re
import sys
from datetime import datetime

# ---------- Utils ----------
RUS_OPS = {
    "плюс": "+", "+": "+",
    "минус": "-", "-": "-",
    "умножить на": "*", "умножить":"*", "умножение":"*", "x":"*", "х":"*","*":"*",
    "разделить на": "/", "разделить":"/", "делить":"/", "/":"/", "÷":"/", ":":"/"
}

NUM_WORDS = {
    "ноль":0,"один":1,"два":2,"три":3,"четыре":4,"пять":5,"шесть":6,"семь":7,"восемь":8,"девять":9,
    "десять":10,"одиннадцать":11,"двенадцать":12,"тринадцать":13,"четырнадцать":14,"пятнадцать":15,
    "шестнадцать":16,"семнадцать":17,"восемнадцать":18,"девятнадцать":19,"двадцать":20,"тридцать":30,
    "сорок":40,"пятьдесят":50,"шестьдесят":60,"семьдесят":70,"восемьдесят":80,"девяносто":90,
    "сто":100,"двести":200,"триста":300,"четыреста":400,"пятьсот":500,"шестьсот":600,"семьсот":700,"восемьсот":800,"девятьсот":900,
}

def ruwords_to_int(token: str):
    token = token.strip().lower()
    if token in NUM_WORDS:
        return NUM_WORDS[token]
    # составные: "двадцать три"
    parts = token.split()
    total = 0
    ok = False
    for p in parts:
        if p in NUM_WORDS:
            total += NUM_WORDS[p]
            ok = True
        else:
            return None
    return total if ok else None

def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()

# ---------- Intents ----------
def intent_time(_text: str):
    now = datetime.now()
    return f"Сейчас {now.strftime('%H:%M')}."

def parse_calc_expression(text: str):
    """
    Пытаемся извлечь простое выражение: a op b
    Поддержка чисел: цифры или русские слова.
    """
    t = normalize_text(text)

    # Нормализуем "умножить на"/"разделить на" -> одно слово с пробелами, ищем приоритетом длинные ключи
    # Меняем многословные операторы на одиночные символы
    t = t.replace("умножить на", "*").replace("разделить на", "/")

    # Найдём оператор
    op = None
    for k, v in RUS_OPS.items():
        if k in ("умножить на", "разделить на"):  # уже заменены выше
            continue
        if f" {k} " in f" {t} ":
            op = v
            break
    if not op:
        return None

    # Разбить по оператору
    if op in ["+", "-"]:
        parts = re.split(rf"\s*\{re.escape(op)}\s*| плюс | минус ", t)
    elif op == "*":
        parts = re.split(r"\s*\*\s*| умножить | x | х ", t)
    else:  # "/"
        parts = re.split(r"\s*\/\s*| разделить | делить | : | ÷ ", t)

    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) < 2:
        return None

    a_raw, b_raw = parts[0], parts[1]

    def to_num(s: str):
        s = s.strip()
        # числа в цифрах (включая десятичные с запятой)
        s2 = s.replace(",", ".")
        if re.fullmatch(r"[+-]?\d+(\.\d+)?", s2):
            try:
                return float(s2)
            except ValueError:
                pass
        # числа словами
        val = ruwords_to_int(s)
        if val is not None:
            return float(val)
        # убрать лишние слова типа "сколько будет", "посчитай", "пожалуйста"
        s = re.sub(r"\b(сколько|будет|посчитай|пожалуйста|равно)\b", "", s).strip()
        val = ruwords_to_int(s)
        if val is not None:
            return float(val)
        return None

    a = to_num(a_raw)
    b = to_num(b_raw)
    if a is None or b is None:
        return None

    return (a, op, b)

def intent_calc(text: str):
    parsed = parse_calc_expression(text)
    if not parsed:
        return None
    a, op, b = parsed
    try:
        if op == "+":
            res = a + b
        elif op == "-":
            res = a - b
        elif op == "*":
            res = a * b
        elif op == "/":
            if b == 0:
                return "На ноль делить нельзя."
            res = a / b
        else:
            return None
        if float(res).is_integer():
            res_str = str(int(res))
        else:
            # округлим до 4 знаков
            res_str = f"{res:.4f}".rstrip("0").rstrip(".")
        return f"Ответ: {res_str}."
    except Exception:
        return None

def intent_weather(_text: str):
    cache_path = r"C:\JarvisBridge\temp\weather_cache.json"
    if not os.path.exists(cache_path):
        return "Кеш погоды не найден."
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # ожидаем простой формат:
        # {"city":"Minsk","today":{"tmin":3,"tmax":8,"desc":"Облачно, без осадков"}}
        city = data.get("city") or data.get("location") or "город"
        today = data.get("today") or {}
        tmin = today.get("tmin")
        tmax = today.get("tmax")
        desc = today.get("desc") or today.get("summary") or "Нет описания"
        parts = [f"Погода, {city}.", desc]
        if tmin is not None and tmax is not None:
            parts.append(f"Температура от {tmin} до {tmax} °C.")
        return " ".join(parts)
    except Exception as e:
        return f"Не удалось прочитать кеш погоды: {e}"

# ---------- Router ----------
def detect_intent(text: str):
    t = normalize_text(text)
    # время
    if any(k in t for k in ["который час", "сколько времени", "время сейчас", "время"]):
        return "time", intent_time(t)
    # калькулятор
    if any(k in t for k in ["плюс", "минус", "умножить", "умножение", "разделить", "делить", "+", "-", "*", "/", "х", "x", "сколько будет"]):
        ans = intent_calc(t)
        if ans:
            return "calc", ans
    # погода
    if any(k in t for k in ["погода", "какая погода", "прогноз"]):
        return "weather", intent_weather(t)
    return None, None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", type=str, help="Текст запроса для офлайн-интента")
    args = parser.parse_args()

    if not args.test:
        print("USAGE: python -X utf8 -u .\\intents\\intents_offline.py --test \"сколько будет 9 плюс 3\"")
        sys.exit(0)

    text = args.test
    intent, answer = detect_intent(text)
    if intent:
        print(f"INTENT={intent}")
        print(f"ANSWER={answer}")
        sys.exit(0)
    else:
        print("NO_INTENT")
        sys.exit(2)

if __name__ == "__main__":
    main()
