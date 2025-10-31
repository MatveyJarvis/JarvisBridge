
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from ..config import settings
from ..skills.sample_skill import summarize_text

async def run():
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN пуст. Заполните .env")
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    @dp.message(F.text)
    async def handle_text(msg: types.Message):
        text = msg.text.strip()
        if text.startswith("/start"):
            await msg.answer("Привет! Я Jarvis Core. Пришли текст — я его суммирую.")
            return
        try:
            summary = summarize_text(text)
        except Exception as e:
            summary = f"Ошибка: {e}"
        await msg.answer(summary or "пусто")

    print("Telegram bot started.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(run())
