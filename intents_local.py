import random
import math

def handle_local_intent(text: str) -> str | None:
    """
    Обрабатывает простые локальные команды без интернета.
    Возвращает текст ответа или None, если фраза не распознана.
    """

    if not text:
        return None

    t = text.lower().strip()

    # --- Приветствие и small-talk ---
    if any(p in t for p in ["привет", "здравствуй", "добрый день", "hi", "hello", "hey"]):
        return random.choice([
            "Привет!", "Слушаю.", "Р rad видеть!", "Здравствуйте!"
        ])
    if "как дела" in t or "как ты" in t:
        return random.choice([
            "Отлично! Готов к работе.", "Все хорошо, спасибо.", "Работаю стабильно!"
        ])
    if "спасибо" in t:
        return random.choice(["Всегда пожалуйста!", "Не за что!", "Обращайся!"])
    if "пока" in t or "до свидания" in t:
        return random.choice(["До встречи!", "Пока!", "До связи!"])

    # --- Арифметика ---
    # Простое вычисление вроде "2 плюс 2", "3*7", "5 делить на 2"
    try:
        expr = (
            t.replace("плюс", "+")
             .replace("минус", "-")
             .replace("умножить на", "*")
             .replace("разделить на", "/")
             .replace(",", ".")
        )
        # Оставляем только допустимые символы
        if all(ch.isdigit() or ch in "+-*/. ()" for ch in expr):
            result = eval(expr)
            return f"{expr} равно {result}"
    except Exception:
        pass

    # --- Повтори за мной ---
    if t.startswith("повтори за мной"):
        phrase = t.replace("повтори за мной", "").strip()
        if phrase:
            return phrase

    return None
