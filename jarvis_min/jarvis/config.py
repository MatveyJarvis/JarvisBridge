
from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
    OPENAI_MODEL: str   = os.getenv("OPENAI_MODEL", "gpt-5.1-mini").strip()
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").strip()
    LOG_DIR: str   = os.getenv("LOG_DIR", "logs").strip()

    WHITELIST_FILE: str = os.getenv("WHITELIST_FILE", "whitelist.yaml").strip()

settings = Settings()
