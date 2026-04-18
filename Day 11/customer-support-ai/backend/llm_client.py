from __future__ import annotations

from typing import Any

from groq import Groq

from config import settings


FALLBACK_RESPONSE_TEXT = "No relevant policy found. Please escalate this issue to a human support agent."


def build_local_response(query: str, docs: list[dict], is_fallback: bool, mode: str) -> str:
    if is_fallback or not docs:
        return FALLBACK_RESPONSE_TEXT

    primary_doc = docs[0]
    base_response = primary_doc.get("company_response") or "We will review your case."
    alternate = primary_doc.get("alternate_solution", "an alternate resolution")

    if mode == "friendly":
        return (
            f"I'm sorry you're dealing with this. {base_response} "
            f"If needed, we can also consider {alternate}."
        )

    return (
        f"{base_response} Policy category: {primary_doc.get('category', 'General')}. "
        f"Alternate resolution: {alternate}."
    )


def _get_client() -> Groq:
    return Groq(api_key=settings.groq_api_key)


def _extract_text(response: Any) -> str:
    choices = getattr(response, "choices", None) or []
    if not choices:
        return ""

    message = getattr(choices[0], "message", None)
    content = getattr(message, "content", "") if message else ""
    return (content or "").strip()


def generate_response(
    prompt: str,
    temperature: float,
    max_tokens: int,
    *,
    system_prompt: str,
    query: str,
    docs: list[dict],
    retry_prompt: str,
    is_fallback: bool,
    mode: str,
) -> dict[str, Any]:
    if is_fallback:
        return {
            "text": FALLBACK_RESPONSE_TEXT,
            "model": "rule-based-fallback",
            "used_mock": False,
            "usage": None,
            "error": None,
        }

    if not settings.groq_api_key:
        return {
            "text": build_local_response(query, docs, is_fallback, mode),
            "model": "local-fallback",
            "used_mock": True,
            "usage": None,
            "error": "GROQ_API_KEY is missing. Returned a local fallback response.",
        }

    client = _get_client()
    messages = []
    if system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = _extract_text(response)
        if not content:
            retry_messages = []
            if system_prompt.strip():
                retry_messages.append({"role": "system", "content": system_prompt})
            retry_messages.append({"role": "user", "content": retry_prompt})
            response = client.chat.completions.create(
                model=settings.groq_model,
                messages=retry_messages,
                temperature=0.2,
                max_tokens=120,
            )
            content = _extract_text(response)

        if not content:
            raise ValueError("Groq returned an empty response.")

        return {
            "text": content,
            "model": getattr(response, "model", settings.groq_model),
            "used_mock": False,
            "usage": getattr(response, "usage", None),
            "error": None,
        }
    except Exception as exc:
        return {
            "text": build_local_response(query, docs, is_fallback, mode),
            "model": "local-fallback",
            "used_mock": True,
            "usage": None,
            "error": f"Groq request failed: {exc}",
        }
