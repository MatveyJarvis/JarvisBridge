# -*- coding: utf-8 -*-
from __future__ import annotations
import json, os
from typing import Optional

def _load_locales() -> dict:
    path = os.path.join(os.path.dirname(__file__), "locales.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {"symbols": {}, "phrases": {"on_date_ru": "на {DATE}", "approx": "≈"}}

_LOCALES = _load_locales()
_SYM = _LOCALES.get("symbols", {})
_PH = _LOCALES.get("phrases", {"on_date_ru": "на {DATE}", "approx": "≈"})

def format_number(value: float, *, locale: str = "ru-RU", max_frac: int = 4) -> str:
    if value is None: return ""
    neg = value < 0; v = abs(float(value))
    s = f"{v:.{max_frac}f}".rstrip("0").rstrip(".")
    int_part, frac_part = (s.split(".") + [""])[:2] if "." in s else (s, "")
    def grp(x: str, sep: str) -> str:
        r = x[::-1]; chunks = [r[i:i+3] for i in range(0, len(r), 3)]
        return sep.join(chunks)[::-1]
    if locale.startswith("ru"):
        int_fmt = grp(int_part, " "); out = f"{int_fmt},{frac_part}" if frac_part else int_fmt
    else:
        int_fmt = grp(int_part, ","); out = f"{int_fmt}.{frac_part}" if frac_part else int_fmt
    return f"-{out}" if neg else out

def _fmt_date_ru(date_iso: Optional[str]) -> str:
    if not date_iso: return ""
    try:
        y, m, d = date_iso.split("-"); return f"{d}.{m}.{y}"
    except Exception:
        return date_iso

def format_rate(base: str, quote: str, rate: float, *, date_iso: Optional[str]=None, locale: str="ru-RU") -> str:
    pair = f"{base.upper()}/{quote.upper()}"
    rate_s = format_number(rate, locale=locale, max_frac=6)
    if locale.startswith("ru"):
        date_part = f" {_PH.get('on_date_ru','на {DATE}').format(DATE=_fmt_date_ru(date_iso))}" if date_iso else ""
        return f"Курс {pair}{date_part}: {rate_s}"
    return f"{pair} rate: {rate_s}" + (f" on {date_iso}" if date_iso else "")

def format_conversion(base: str, quote: str, rate: float, amount: float, *, date_iso: Optional[str]=None, locale: str="ru-RU") -> str:
    amount_s = format_number(amount, locale=locale, max_frac=4)
    conv_s = format_number(amount * rate, locale=locale, max_frac=4)
    rate_s = format_number(rate, locale=locale, max_frac=6)
    if locale.startswith("ru"):
        date_part = f" {_PH.get('on_date_ru','на {DATE}').format(DATE=_fmt_date_ru(date_iso))}" if date_iso else ""
        return f"{amount_s} {base.upper()} {_PH.get('approx','≈')} {conv_s} {quote.upper()} по курсу {rate_s}{date_part}"
    else:
        date_part = f" on {date_iso}" if date_iso else ""
        return f"{amount_s} {base.upper()} ≈ {conv_s} {quote.upper()} at rate {rate_s}{date_part}"

if __name__ == "__main__":
    print(format_rate("USD","BYN",3.2567, locale="ru-RU"))
    print(format_conversion("USD","BYN",3.2567,100, date_iso="2025-10-20", locale="ru-RU"))
    print(format_rate("EUR","RUB",102.34567, date_iso="2025-10-19", locale="en-US"))
    print(format_conversion("EUR","RUB",102.34567,50, date_iso="2025-10-19", locale="en-US"))
