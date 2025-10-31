import os
import sys
from dotenv import load_dotenv

# Добавляем путь к src в sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from audio.recorder import record_wav

def main():
    load_dotenv()
    print("🎤 Готов. Скажи фразу и замолчи...")
    path = record_wav()
    print("✅ Saved:", path)

if __name__ == "__main__":
    main()
