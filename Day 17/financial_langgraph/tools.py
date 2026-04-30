"""Tools used by the LangGraph financial assistant."""

from __future__ import annotations

import ast
import json
import math
import os
import re
import statistics
import urllib.error
import urllib.request
from pathlib import Path


def web_search(query: str, ticker: str) -> str:
    """Search latest market news with Serper when SERPER_API_KEY is available."""

    api_key = os.getenv("SERPER_API_KEY", "")
    search_query = f"{ticker} latest market news earnings sentiment {query}"
    if not api_key:
        return (
            "Serper API key not configured. Offline placeholder: check latest earnings, analyst revisions, "
            "regulatory news, sector trend, and market sentiment before making an investment recommendation."
        )

    payload = json.dumps({"q": search_query, "num": 5}).encode("utf-8")
    request = urllib.request.Request(
        "https://google.serper.dev/search",
        data=payload,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return f"Serper search failed: {exc}"

    organic = data.get("organic", [])[:5]
    if not organic:
        return "Serper returned no market news results."

    snippets = []
    for item in organic:
        title = item.get("title", "Untitled result")
        snippet = item.get("snippet", "No snippet available")
        link = item.get("link", "")
        snippets.append(f"{title}: {snippet} ({link})")
    return "\n".join(snippets)


def calculator(question: str) -> str:
    """Compute financial formulas or arithmetic expressions from the question."""

    text = question.lower()

    roi_match = re.search(r"(?:buy|cost|invest(?:ment)?)\D+([0-9,.]+)\D+(?:sell|value|return)\D+([0-9,.]+)", text)
    if "roi" in text and roi_match:
        cost = float(roi_match.group(1).replace(",", ""))
        value = float(roi_match.group(2).replace(",", ""))
        roi = ((value - cost) / cost) * 100
        return f"ROI = (({value} - {cost}) / {cost}) * 100 = {roi:.2f}%"

    margin_match = re.search(r"revenue\D+([0-9,.]+)\D+(?:cost|expense)\D+([0-9,.]+)", text)
    if "margin" in text and margin_match:
        revenue = float(margin_match.group(1).replace(",", ""))
        cost = float(margin_match.group(2).replace(",", ""))
        margin = ((revenue - cost) / revenue) * 100
        return f"Profit margin = (({revenue} - {cost}) / {revenue}) * 100 = {margin:.2f}%"

    expression = _extract_arithmetic_expression(question)
    if expression:
        try:
            result = _safe_eval(expression)
            return f"Calculation result for `{expression}` = {result}"
        except ValueError as exc:
            return f"Could not safely calculate expression `{expression}`: {exc}"

    return (
        "No exact numeric formula found. Supported examples: "
        "'ROI if buy 100 and sell 125', 'margin with revenue 1000 and cost 700', or arithmetic like '1200 * 1.08'."
    )


def python_market_analysis(ticker: str) -> str:
    """Simulate a Python REPL style trend analysis using local sample prices."""

    sample_prices = {
        "TSLA": [182.4, 187.1, 185.0, 191.3, 196.8, 193.2, 201.4, 207.0],
        "AAPL": [171.2, 172.6, 170.8, 174.5, 176.1, 175.3, 178.0, 179.4],
        "MSFT": [410.0, 414.2, 417.5, 416.8, 421.0, 425.3, 429.9, 431.1],
        "GOOGL": [141.4, 143.2, 142.7, 145.1, 146.8, 147.0, 148.5, 149.2],
        "NVDA": [880.0, 905.4, 930.2, 918.5, 940.8, 960.2, 975.3, 990.1],
    }
    prices = sample_prices.get(ticker.upper(), sample_prices["TSLA"])
    start = prices[0]
    end = prices[-1]
    change = ((end - start) / start) * 100
    volatility = statistics.pstdev(prices)
    moving_average = sum(prices[-5:]) / 5
    trend = "upward" if change > 2 else "flat" if abs(change) <= 2 else "downward"

    return (
        f"Python analysis for {ticker}: start={start}, end={end}, change={change:.2f}%, "
        f"5-period moving average={moving_average:.2f}, volatility={volatility:.2f}, trend={trend}."
    )


def document_retriever(query: str) -> str:
    """Search local internal documents in docs/*.txt using keyword overlap."""

    docs_dir = Path(__file__).parent / "docs"
    query_words = {word.lower() for word in re.findall(r"[a-zA-Z]{4,}", query)}
    matches = []

    for path in docs_dir.glob("*.txt"):
        text = path.read_text(encoding="utf-8")
        words = {word.lower() for word in re.findall(r"[a-zA-Z]{4,}", text)}
        score = len(query_words & words)
        if score:
            snippet = " ".join(text.split()[:55])
            matches.append((score, path.name, snippet))

    if not matches:
        return "No internal document match found."

    matches.sort(reverse=True)
    return "\n".join(f"{name}: {snippet}" for _, name, snippet in matches[:3])


def _extract_arithmetic_expression(text: str) -> str:
    matches = re.findall(r"[0-9][0-9\s+\-*/().%]*[0-9%]", text)
    return max(matches, key=len).strip() if matches else ""


def _safe_eval(expression: str) -> float:
    expression = expression.replace("%", "/100")
    tree = ast.parse(expression, mode="eval")
    return _eval_node(tree.body)


def _eval_node(node) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        operators = {
            ast.Add: left + right,
            ast.Sub: left - right,
            ast.Mult: left * right,
            ast.Div: left / right,
            ast.Pow: left**right,
        }
        for operator_type, value in operators.items():
            if isinstance(node.op, operator_type):
                return value
    if isinstance(node, ast.UnaryOp):
        value = _eval_node(node.operand)
        if isinstance(node.op, ast.UAdd):
            return value
        if isinstance(node.op, ast.USub):
            return -value
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"sqrt", "log"}:
        args = [_eval_node(arg) for arg in node.args]
        return getattr(math, node.func.id)(*args)
    raise ValueError("unsupported expression")
