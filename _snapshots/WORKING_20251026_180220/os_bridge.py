# -*- coding: utf-8 -*-
"""
OS-Bridge B.2.1 — безопасный мост с нормализацией фраз и 'мягким' сопоставлением.
Замени этим файлом существующий os_bridge.py в C:\JarvisBridge\

Особенности:
- Нормализация (lower, удаление лишних символов).
- Словарь с синонимами/заменами (например: 'запусти' -> 'открой').
- Fuzzy matching (difflib.get_close_matches) поверх фраз из bridge_config.json.
- Поддержка безопасности: для "открой сайт X" — только по белому списку в конфиге.
- Логи: logs/os_bridge.log
"""

import json
import os
import re
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from difflib import get_close_matches

ROOT = Path(__file__).resolve().parent
LOGS_DIR = ROOT.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / "os_bridge.log"
CONFIG_PATH = ROOT / "bridge_config.json"

# Порог сходства (0..1). Чем ближе к 1 — строже.
FUZZY_THRESHOLD = 0.65

# Простые текстовые замены/синонимы (нормализация)
NORMALIZATION_MAP = {
    r"\bзапусти\b": "открой",
    r"\bзапустить\b": "открой",
    r"\bпоказ(ать|и)\b": "открой",
    r"\bбраузер\b": "хром",
    r"\bхром\b": "хром",
    r"\bгугл\b": "google",
    r"\bзагрузк[аи]\b": "загрузки",
    r"\bпараметр[ы]?\b": "настройки",
    r"\bнастройки windows\b": "настройки",
    # добавляй свои правила по мере надобности
}

# Регексп для "открой сайт <домен>"
SITE_OPEN_RE = re.compile(r"(?:открой|запусти)\s+(?:сайт\s+)?([A-Za-z0-9\.-]+\.[A-Za-z]{2,6})")

def log(line: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {line}\n")

def load_config():
    if not CONFIG_PATH.exists():
        raise RuntimeError(f"Не найден конфиг: {CONFIG_PATH}")
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        cfg = json.load(f)
    # Приведём элементы к удобному виду
    for key, item in cfg.items():
        item["id"] = key
        item["phrases"] = [p.strip().lower() for p in item.get("phrases", [])]
        # run может быть строкой или списком
        cmd = item.get("run", [])
        if isinstance(cmd, str):
            item["run"] = shlex.split(cmd)
        elif isinstance(cmd, list):
            item["run"] = [str(x) for x in cmd]
        else:
            raise ValueError(f"{key}: поле 'run' должно быть str или list[str]")
        item.setdefault("env_expand", True)
        item.setdefault("shell", False)
        item.setdefault("confirm_say", "Готово.")
        # опциональный whitelist для сайтов
        item.setdefault("allowed_domains", [])
    return cfg

def apply_normalization(text: str) -> str:
    t = text.lower()
    # убираем лишние символы (оставим буквы, цифры, пробелы, точку и дефис)
    t = re.sub(r"[^0-9a-zа-яё\.\-\s]", " ", t, flags=re.I)
    # применяем словарь замен
    for pattern, repl in NORMALIZATION_MAP.items():
        t = re.sub(pattern, repl, t, flags=re.I)
    # сократим пробелы
    t = re.sub(r"\s+", " ", t).strip()
    return t

def find_site(text: str):
    m = SITE_OPEN_RE.search(text)
    if not m:
        return None
    domain = m.group(1).lower()
    # убираем возможные слеши
    domain = domain.split('/')[0]
    return domain

def safe_run_allowed(cmd_item: dict) -> subprocess.Popen:
    cmd = cmd_item["run"]
    if cmd_item.get("env_expand", True):
        cmd = [os.path.expandvars(str(x)) for x in cmd]

    shell = bool(cmd_item.get("shell", False))
    log(f"EXEC: {cmd!r} shell={shell}")
    try:
        proc = subprocess.Popen(cmd, shell=shell)
        return proc
    except Exception as e:
        log(f"ERROR EXEC: {e}")
        raise

def match_command_by_phrase(norm_text: str, cfg: dict):
    """
    Сначала пробуем exact substring match: если какая-то фраза из конфига
    полностью встречается в нормализованном тексте — принимаем её гарантированно.
    """
    for key, item in cfg.items():
        for phrase in item["phrases"]:
            if phrase and phrase in norm_text:
                return item
    return None

def match_command_fuzzy(norm_text: str, cfg: dict):
    """
    Fuzzy match: построим список всех фраз и используем difflib.get_close_matches
    для norm_text (целевой текcт) и для каждой фразы — сравним.
    Вернём лучший match, если score >= FUZZY_THRESHOLD.
    """
    # собираем все фразы с привязкой к id
    pool = []
    id_map = {}
    for key, item in cfg.items():
        for phrase in item["phrases"]:
            pool.append(phrase)
            id_map[phrase] = key

    if not pool:
        return None

    # get_close_matches ищет похожие элементы в pool для norm_text
    # но удобнее — искать похожие фразы к norm_text и брать лучший
    candidates = get_close_matches(norm_text, pool, n=5, cutoff=FUZZY_THRESHOLD)
    if not candidates:
        # попробовать искать по словам: взять первое слово и смотреть
        words = norm_text.split()
        for w in words:
            c = get_close_matches(w, pool, n=1, cutoff=FUZZY_THRESHOLD)
            if c:
                return cfg[id_map[c[0]]]
        return None
    # возвращаем первый кандидат (самый похожий)
    best = candidates[0]
    return cfg[id_map[best]]

def bridge_execute(user_text: str) -> dict:
    """
    Основная точка входа: принимает оригинальный текст (из STT),
    нормализует, пробует прямой матч -> fuzzy -> специальные слоты (сайты).
    """
    try:
        cfg = load_config()
    except Exception as e:
        log(f"CONFIG LOAD ERROR: {e}")
        return {"ok": False, "message": f"Ошибка конфига: {e}", "matched_id": None}

    # 1) нормализация
    norm = apply_normalization(user_text)
    log(f"INPUT: {user_text!r} NORM: {norm!r}")

    # 2) специальный слот: открой сайт X (только из allowed_domains)
    domain = find_site(user_text.lower())
    if domain:
        # найдем в конфиге команду, у которой есть allowed_domains с этим доменом
        for key, item in cfg.items():
            allowed = [d.lower() for d in item.get("allowed_domains", [])]
            if domain in allowed:
                try:
                    safe_run_allowed(item)
                    return {"ok": True, "message": item.get("confirm_say", "Открываю сайт."), "matched_id": item["id"]}
                except Exception as e:
                    return {"ok": False, "message": f"Ошибка запуска сайта: {e}", "matched_id": item["id"]}
        log(f"SITE BLOCKED: {domain}")
        return {"ok": False, "message": "Открывать произвольные сайты запрещено.", "matched_id": None}

    # 3) exact substring match
    exact = match_command_by_phrase(norm, cfg)
    if exact:
        try:
            safe_run_allowed(exact)
            return {"ok": True, "message": exact.get("confirm_say", "Готово."), "matched_id": exact["id"]}
        except Exception as e:
            return {"ok": False, "message": f"Ошибка запуска: {e}", "matched_id": exact["id"]}

    # 4) fuzzy match
    fuzzy = match_command_fuzzy(norm, cfg)
    if fuzzy:
        try:
            safe_run_allowed(fuzzy)
            return {"ok": True, "message": fuzzy.get("confirm_say", "Готово."), "matched_id": fuzzy["id"]}
        except Exception as e:
            return {"ok": False, "message": f"Ошибка запуска: {e}", "matched_id": fuzzy["id"]}

    # 5) ничего не найдено
    log(f"MISS: {user_text!r} -> {norm!r}")
    return {"ok": False, "message": "Команда не распознана. Скажи: 'что ты умеешь'.", "matched_id": None}

def describe_capabilities() -> str:
    cfg = load_config()
    lines = []
    for key, item in cfg.items():
        ph = ", ".join(item["phrases"])
        lines.append(f"- {key}: {ph}")
    return "Доступные команды:\n" + "\n".join(lines)

# Простая CLI для тестирования
def _cli():
    print("OS-Bridge B.2.1 — тест. Введите фразу (или 'выход').")
    while True:
        try:
            line = input(">> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            continue
        if line.lower() in ("выход", "exit", "quit"):
            break
        if "что ты умеешь" in line.lower():
            print(describe_capabilities()); continue
        res = bridge_execute(line)
        print(f"[{ 'OK' if res['ok'] else 'ERR' }] {res['message']} (cmd: {res['matched_id']})")

if __name__ == "__main__":
    _cli()
