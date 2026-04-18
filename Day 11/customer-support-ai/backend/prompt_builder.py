from __future__ import annotations


SCENARIO_PARAMS = {
    "strict": {
        "temperature": 0.2,
        "max_tokens": 150,
        "label": "Scenario A: Strict Policy Mode",
    },
    "friendly": {
        "temperature": 0.7,
        "max_tokens": 200,
        "label": "Scenario B: Friendly Tone Mode",
    },
    "fallback": {
        "temperature": 0.1,
        "max_tokens": 150,
        "label": "Scenario C: Fallback Mode",
    },
}


def format_context(docs: list[dict]) -> str:
    if not docs:
        return "No relevant policy found."

    lines: list[str] = []
    for index, doc in enumerate(docs[:3], start=1):
        line = f"{index}. {doc.get('title', '')}: {doc.get('solution', '')}"
        alternate = doc.get("alternate_solution", "").strip()
        if alternate:
            line += f" | Alternate: {alternate}"
        lines.append(line)
    return "\n".join(lines)


def build_strict_prompt(query: str, docs: list[dict]) -> str:
    context = format_context(docs)
    return f"""You are a professional customer support assistant.
Use ONLY the provided policy context.
Do not add extra assumptions.

Context:
{context}

Customer Issue:
{query}

Give a clear and concise response."""


def build_friendly_prompt(query: str, docs: list[dict]) -> str:
    context = format_context(docs)
    return f"""You are a polite and empathetic support agent.
Use the policy context but respond in a friendly tone.

Context:
{context}

Customer Issue:
{query}
"""


def build_fallback_prompt(query: str) -> str:
    return f"""No relevant policy found.

Respond with:
"No relevant policy found.Please escalate this issue to a human support agent."

Customer Issue:
{query}
"""


def build_prompt(query: str, docs: list[dict], mode: str, is_fallback: bool) -> dict:
    if is_fallback:
        scenario_key = "fallback"
        prompt = build_fallback_prompt(query)
        retry_prompt = f"{query}\nNo relevant policy found. Please escalate this issue to a human support agent."
    elif mode == "friendly":
        scenario_key = "friendly"
        prompt = build_friendly_prompt(query, docs)
        retry_prompt = f"{format_context(docs)}\nCustomer Issue: {query}\nRespond warmly."
    else:
        scenario_key = "strict"
        prompt = build_strict_prompt(query, docs)
        retry_prompt = f"{format_context(docs)}\nCustomer Issue: {query}\nRespond clearly."

    params = SCENARIO_PARAMS[scenario_key]
    return {
        "prompt": prompt,
        "retry_prompt": retry_prompt,
        "system_prompt": "",
        "user_prompt": prompt,
        "scenario": params["label"],
        "temperature": params["temperature"],
        "max_tokens": params["max_tokens"],
        "context": format_context(docs) if not is_fallback else "No relevant policy found.",
    }
