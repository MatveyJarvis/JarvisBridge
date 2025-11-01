import os, json
from dotenv import load_dotenv

print("=== Проверка WHITELIST_PATH ===")
load_dotenv()
path = os.getenv("WHITELIST_PATH")
print(f"Переменная окружения: {path}")

if not path or not os.path.exists(path):
    print("❌ whitelist.json не найден или переменная не загружена")
else:
    # поддержка файлов с BOM
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    print("✅ Найден файл, разрешённые пути:")
    for p in data["allowed_paths"]:
        print(" →", p)
