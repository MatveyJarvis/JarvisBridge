import typer
from rich import print
from .logging_conf import setup_logging
from .config import settings
from .whitelist import Whitelist
from .connectors.fs import SafeFS
from .llm import chat
from .memory import append_event, tail

app = typer.Typer(help="Jarvis 1.0 Core CLI")

# ---------- БАЗА ----------
@app.command()
def run():
    logger = setup_logging()
    logger.info("Jarvis Core запущен.")
    print(f"[bold green]Model:[/bold green] {settings.OPENAI_MODEL}")

# ---------- FS ----------
@app.command("fs-scan")
def fs_scan():
    """Печатает все разрешённые файлы из whitelist."""
    logger = setup_logging()
    wl = Whitelist(settings.WHITELIST_FILE)
    fs = SafeFS(wl)
    count = 0
    for p in fs.iter_files():
        print(p)
        count += 1
    logger.info(f"Найдено файлов: {count}")

@app.command("fs-export")
def fs_export(out: str = typer.Argument("inventory.csv")):
    """Экспортирует список файлов в CSV (по умолчанию inventory.csv)."""
    logger = setup_logging()
    wl = Whitelist(settings.WHITELIST_FILE)
    fs = SafeFS(wl)
    from pathlib import Path
    from .tools.inventory import build_inventory, write_csv
    rows = list(build_inventory(fs))
    path = write_csv(rows, Path(out))
    logger.info(f"Экспортировано строк: {len(rows)} → {path}")
    print(path)

@app.command("fs-find")
def fs_find(
    pattern: str = typer.Argument(..., help="Подстрока в имени (без учёта регистра)"),
    exts: str = typer.Option("", "--exts", help="Фильтр расширений через запятую, напр.: .xlsx,.csv"),
):
    """Поиск по имени файла среди разрешённых путей."""
    logger = setup_logging()
    wl = Whitelist(settings.WHITELIST_FILE)
    fs = SafeFS(wl)

    want_exts = {e.strip().lower() for e in exts.split(",") if e.strip()} if exts else None
    q = pattern.lower()
    count = 0
    for p in fs.iter_files():
        if q in p.name.lower():
            if want_exts and p.suffix.lower() not in want_exts:
                continue
            print(p)
            count += 1
    logger.info(f"Найдено файлов по '{pattern}': {count}")

# ---------- БОТ (заготовка) ----------
@app.command("bot")
def bot_group(which: str = typer.Argument(..., help="telegram")):
    if which == "telegram":
        import asyncio
        from .bot.telegram_bot import run as run_bot
        asyncio.run(run_bot())
    else:
        raise typer.BadParameter("Неизвестный бот")

# ---------- МИНИ-JARVIS ----------
@app.command()
def ask(prompt: str = typer.Argument(..., help="Вопрос Jarvis'у")):
    logger = setup_logging()
    system = "Ты локальный помощник Jarvis. Отвечай кратко и по делу."
    answer = chat(system, prompt)
    print(answer)
    append_event({"type": "qa", "prompt": prompt, "answer": answer})
    logger.info("Сессия сохранена в память.")

@app.command("mem")
def mem(n: int = typer.Argument(10, help="Сколько последних записей показать")):
    """Показать последние записи памяти."""
    for item in tail(n):
        kind = item.get("type", "?")
        text = item.get("prompt") or item.get("note") or ""
        print(f"[{item.get('ts')}] {kind}: {text}")

if __name__ == "__main__":
    app()
