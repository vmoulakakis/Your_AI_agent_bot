import os
from typing import List, Dict, Any

import requests

from . import repositories as repo
from .utils import utc_now_iso


OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


def _build_headers() -> Dict[str, str]:
    api_key = os.environ.get("OPENAI_API_KEY") or (repo.get_setting("openai_api_key") or "").strip()
    if not api_key:
        raise RuntimeError("OpenAI API key missing. Set OPENAI_API_KEY or save in Settings.")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def chat_with_memory(session_id: str, user_message: str) -> str:
    conv = repo.get_conversation_by_session_id(session_id)
    if not conv:
        conv_id = repo.create_conversation(session_id, summary="")
    else:
        conv_id = int(conv["id"])

    repo.add_message(conv_id, "user", user_message)

    memories = repo.list_memories(conv_id, top_n=5)
    memory_snippets = [m["content"] for m in memories]

    history_rows = repo.list_messages(conv_id, limit=12)
    messages: List[Dict[str, str]] = []
    if memory_snippets:
        messages.append({
            "role": "system",
            "content": "You are an AI shopping concierge for an affiliate eShop. Persist and use user preferences. Key memories: " + "; ".join(memory_snippets),
        })
    else:
        messages.append({
            "role": "system",
            "content": "You are an AI shopping concierge for an affiliate eShop. Be helpful, concise, and product-focused.",
        })
    for r in history_rows:
        messages.append({"role": r["role"], "content": r["content"]})
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": OPENAI_MODEL,
        "messages": messages,
        "temperature": 0.5,
    }
    try:
        resp = requests.post(f"{OPENAI_BASE_URL}/chat/completions", headers=_build_headers(), json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        reply = data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        reply = f"Sorry, the AI service is currently unavailable: {e}"

    repo.add_message(conv_id, "assistant", reply)

    try:
        # Simple heuristic memory extraction
        mem_prompt = {
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": "Extract up to 3 short facts about user preferences or constraints to remember. Return as bullet points."},
                {"role": "user", "content": "\n\n".join([m["content"] for m in history_rows[-6:]] + [user_message, reply])},
            ],
            "temperature": 0.2,
        }
        mresp = requests.post(f"{OPENAI_BASE_URL}/chat/completions", headers=_build_headers(), json=mem_prompt, timeout=30)
        mresp.raise_for_status()
        mdata = mresp.json()
        mem_text = mdata["choices"][0]["message"]["content"].strip()
        for line in mem_text.splitlines():
            text = line.strip("- ")
            if text:
                repo.add_memory(conv_id, text, score=1.0)
    except Exception:
        pass

    return reply