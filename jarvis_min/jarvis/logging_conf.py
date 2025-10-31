
from loguru import logger
from pathlib import Path
from .config import settings

def setup_logging():
    Path(settings.LOG_DIR).mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), level=settings.LOG_LEVEL)
    logger.add(Path(settings.LOG_DIR) / "jarvis.log", rotation="5 MB", retention=5, level=settings.LOG_LEVEL)
    return logger
