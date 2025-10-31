import os, sys
# добавить в PYTHONPATH корень проекта (на уровень выше папки scripts)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tts_openai import say

print("BEFORE")
say("Слушаю.")
print("AFTER")
