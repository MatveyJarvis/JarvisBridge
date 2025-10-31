# -*- coding: utf-8 -*-
import sys, os

# добавляем корень проекта C:\JarvisBridge в путь импорта
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.voice_logger import log_turn

log_turn("тест логгера", "ответ логгера работает", {"stage": "manual_test"})
print("[✓] Проверка логгера завершена — строка должна появиться в voice_dialog.jsonl")
