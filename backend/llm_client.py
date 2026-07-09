"""
Thin LLM abstraction — Groq only (fast, generous free tier, OpenAI-compatible
API under the hood).

We deliberately do NOT hide provider failures behind a silent fallback to
"no answer" - if the API key is missing or the call fails, we raise, and the
backend surfaces a clear error to the UI. Silently swallowing LLM errors in a
system whose whole point is "don't hallucinate, and be honest about limits"
would be self-defeating: a failed call and "the docs don't cover this" must
never look the same to the end user.
"""
import json
import os

from dotenv import load_dotenv

load_dotenv()

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


class LLMError(RuntimeError):
    pass


def _groq_chat(system: str, user: str, temperature: float, json_mode: bool) -> str:
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise LLMError(
            "GROQ_API_KEY is not set. Get a free key at https://console.groq.com "
            "and put it in your .env file (see .env.example)."
        )
    client = Groq(api_key=api_key)
    kwargs = {}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        **kwargs,
    )
    return resp.choices[0].message.content


def chat(system: str, user: str, temperature: float = 0.0, json_mode: bool = False) -> str:
    return _groq_chat(system, user, temperature, json_mode)


def chat_json(system: str, user: str, temperature: float = 0.0) -> dict:
    """Call the LLM expecting a JSON object back; parse defensively."""
    raw = chat(system, user, temperature=temperature, json_mode=True)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Some models occasionally wrap JSON in markdown fences despite instructions.
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise LLMError(f"Model did not return valid JSON: {raw[:500]}") from e