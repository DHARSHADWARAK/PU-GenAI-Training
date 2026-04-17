from __future__ import annotations

from typing import Any

import requests

from config import settings


def build_local_response(query: str, docs: list[dict], is_fallback: bool, mode: str) -> str:
    if is_fallback or not docs:
        return (
            "Please escalate this issue to a human support agent. "
            "We could not find a reliable policy match for this complaint."
        )

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


def generate_response(
    prompt: str,
    temperature: float,
    max_tokens: int,
    *,
    query: str,
    docs: list[dict],
    is_fallback: bool,
    mode: str,
) -> dict[str, Any]:
    if not settings.sarvam_api_key:
        return {
            "text": build_local_response(query, docs, is_fallback, mode),
            "model": "local-fallback",
            "used_mock": True,
            "usage": None,
            "error": "SARVAM_API_KEY is missing. Returned a local fallback response.",
        }

    headers = {
        "Content-Type": "application/json",
        "api-subscription-key": settings.sarvam_api_key,
    }
    payload = {
        "model": settings.sarvam_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        response = requests.post(
            settings.sarvam_api_url,
            headers=headers,
            json=payload,
            timeout=settings.request_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        if not content:
            raise ValueError("Sarvam API returned an empty response.")
        return {
            "text": content,
            "model": data.get("model", settings.sarvam_model),
            "used_mock": False,
            "usage": data.get("usage"),
            "error": None,
        }
    except Exception as exc:
        return {
            "text": build_local_response(query, docs, is_fallback, mode),
            "model": "local-fallback",
            "used_mock": True,
            "usage": None,
            "error": f"Sarvam request failed: {exc}",
        }
