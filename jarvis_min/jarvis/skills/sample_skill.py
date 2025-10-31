
from ..llm import chat

def summarize_text(text: str) -> str:
    system = "Ты помощник Jarvis. Кратко суммируй входной текст (3-5 пунктов)."
    return chat(system, text)
