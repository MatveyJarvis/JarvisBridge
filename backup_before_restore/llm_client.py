# -*- coding: utf-8 -*-
"""
llm_client.py вЂ” РѕР±С‘СЂС‚РєР° РЅР°Рґ OpenAI Chat API.
.env:
  OPENAI_API_KEY
  OPENAI_MODEL      (РЅР°РїСЂ. gpt-4o, gpt-4.1, gpt-4o-mini)
  OPENAI_PROJECT_ID (РµСЃР»Рё РєР»СЋС‡ РїСЂРѕРµРєС‚РЅС‹Р№ sk-proj-...)
  OPENAI_TIMEOUT    (СЃРµРє, РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ 30)
"""
import os
from dotenv import load_dotenv
from intents.intents_offline import detect_intent
from typing import List, Dict, Optional
from openai import OpenAI
from openai._exceptions import OpenAIError

_client: Optional[OpenAI] = None
_model = "gpt-4o"
_timeout = 30

def _build_client() -> OpenAI:
    global _client, _model, _timeout
    if _client is not None:
        return _client
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY РїСѓСЃС‚. Р—Р°РїРѕР»РЅРё .env")
    _model = (os.getenv("OPENAI_MODEL", _model) or _model).strip()
    try:
        _timeout = int(os.getenv("OPENAI_TIMEOUT", _timeout))
    except Exception:
        _timeout = 30
    kwargs = {"api_key": api_key}
    if api_key.startswith("sk-proj-"):
        project_id = os.getenv("OPENAI_PROJECT_ID", "").strip()
        if project_id:
            kwargs["project"] = project_id
    _client = OpenAI(**kwargs)
    return _client

def ask_llm(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.6,
    max_output_tokens: int = 500,
) -> str:
        # --- offline intents precheck ---
    try:
        last_user = ""
        try:
            for m in reversed(messages or []):
                role = (m.get("role") or "").strip().lower()
                if role == "user":
                    last_user = (m.get("content") or "").strip()
                    break
        except Exception:
            pass
        if last_user:
            try:
                _i, _a = detect_intent(last_user)
                if _i and _a:
                    return _a
            except Exception:
                pass
    except Exception:
            client = _build_client()
    use_model = (model or os.getenv("OPENAI_MODEL") or _model).strip()
    try:
        resp = client.chat.completions.create(
            model=use_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_output_tokens,
            timeout=_timeout,
        )
        return (resp.choices[0].message.content or "").strip()
    except OpenAIError as e:
        return f"[LLM error] {e}"
    except Exception as e:
        return f"[LLM exception] {e}"



