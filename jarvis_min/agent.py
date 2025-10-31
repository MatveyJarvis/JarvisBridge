import os, json, importlib
from dotenv import load_dotenv
from openai import OpenAI

# ленивый импорт инструментов
sys_tools = None

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Открывает приложение в Windows. Примеры: notepad, calc, mspaint, проводник, cmd.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Имя приложения (например, 'notepad' или 'блокнот')."}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "Открывает сайт/URL в браузере.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Ссылка, например 'google.com' или 'https://chat.openai.com'."}
                },
                "required": ["url"]
            }
        }
    }
]

def _import_tools():
    global sys_tools
    if sys_tools is None:
        sys_tools = importlib.import_module("tools.system_tools")

def _call_tool(name: str, args: dict) -> str:
    if name == "open_app":
        return sys_tools.open_app(**args)
    if name == "open_url":
        return sys_tools.open_url(**args)
    return f"Неизвестный инструмент: {name}"

def run_agent(user_text: str) -> dict:
    """
    Отправляет запрос в OpenAI, вызывает инструменты при необходимости и возвращает ответ.
    """
    # Загружаем .env перед созданием клиента
    load_dotenv()
    client = OpenAI()

    _import_tools()

    system_prompt = "Ты — голосовой ассистент Jarvis на Windows. Отвечай по делу, выполняй команды через tool_calls."
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text},
    ]

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    tool_logs = []
    msg = resp.choices[0].message

    if msg.tool_calls:
        for tc in msg.tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments or "{}")
            result = _call_tool(name, args)
            tool_logs.append({"tool": name, "args": args, "result": result})

        messages.append({"role": "assistant", "content": None, "tool_calls": msg.tool_calls})
        for log in tool_logs:
            messages.append({"role": "tool", "name": log["tool"], "content": log["result"]})

        resp2 = client.chat.completions.create(model=model, messages=messages)
        answer = (resp2.choices[0].message.content or "").strip()
    else:
        answer = (msg.content or "").strip()

    return {"answer": answer, "tool_logs": tool_logs}
