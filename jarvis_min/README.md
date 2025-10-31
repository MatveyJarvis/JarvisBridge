
# Jarvis 1.0 Core (Starter)

Минимальный каркас проекта под Windows 11 (Python 3.10+). Включает:
- Конфиг + .env loader
- Логирование (rotating file + console)
- Белый список путей (локальные/сетевые) и безопасный файловый коннектор
- LLM-обёртку (OpenAI API)
- Пример навыка (`skills/sample_skill.py`)
- CLI (Typer): `jarvis run`, `jarvis fs scan`, `jarvis bot telegram`
- Заготовку Telegram-бота (aiogram 3.x)
- Плейсхолдеры под 1С-коннектор и самообучение (level 3)
- Тест дыма `pytest -q`

## Быстрый старт

```bash
# 1) Распаковать архив в папку проекта, затем:
python -m venv .venv && .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt

# 2) Скопировать .env.example -> .env и заполнить ключи
copy .env.example .env

# 3) Запустить smoke-тест
pytest -q

# 4) Пробный запуск
python -m jarvis.cli run

# 5) Скан по белому списку путей
python -m jarvis.cli fs scan

# 6) Telegram-бот (только скелет)
python -m jarvis.cli bot telegram
```

## Структура
```
jarvis/
  __init__.py
  config.py
  logging_conf.py
  whitelist.py
  llm.py
  permissions.py
  connectors/
    __init__.py
    fs.py
    onec.py
  skills/
    __init__.py
    sample_skill.py
  bot/
    __init__.py
    telegram_bot.py
scripts/
  check_openai_balance.py
tests/
  test_smoke.py
```

## Примечания
- Для Telegram бота заполните `TELEGRAM_BOT_TOKEN` в .env.
- `whitelist.yaml` — основной файл белых списков путей/масок.
- Под 1С оставлен коннектор-плейсхолдер (`connectors/onec.py`) и TODO.
- Самообучение Level 3: добавлен каркас `permissions.py` и места для метрик/логов.
