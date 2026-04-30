"""LangGraph workflow for the financial research assistant."""

from __future__ import annotations

import os
import re
from typing import Dict, List, TypedDict

from dotenv import load_dotenv
from langgraph.graph import END, StateGraph

from tools import calculator, document_retriever, python_market_analysis, web_search

try:
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover - optional dependency
    ChatOpenAI = None


class FinancialResearchState(TypedDict):
    question: str
    ticker: str
    selected_tools: List[str]
    tool_results: Dict[str, str]
    memory: List[str]
    final_answer: str


TICKERS = {
    "tesla": "TSLA",
    "apple": "AAPL",
    "microsoft": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "nvidia": "NVDA",
    "meta": "META",
    "netflix": "NFLX",
}

NON_TICKER_WORDS = {
    "API",
    "COD",
    "EPS",
    "FAQ",
    "JSON",
    "LLM",
    "ROI",
    "ROE",
}


def _extract_ticker(question: str) -> str:
    upper_symbol = re.search(r"\b[A-Z]{2,5}\b", question)
    if upper_symbol and upper_symbol.group(0) not in NON_TICKER_WORDS:
        return upper_symbol.group(0)

    text = question.lower()
    for company, ticker in TICKERS.items():
        if company in text:
            return ticker
    return "TSLA"


def route_tools(state: FinancialResearchState) -> FinancialResearchState:
    """Central agent node: decides which tools the query needs."""

    question = state["question"]
    text = question.lower()
    selected = []

    if any(word in text for word in ["latest", "news", "market", "earnings", "sentiment", "quarter"]):
        selected.append("web_search")
    if any(word in text for word in ["roi", "return", "margin", "interest", "calculate", "ratio", "%"]):
        selected.append("calculator")
    if any(word in text for word in ["trend", "forecast", "performance", "compare", "chart", "analysis"]):
        selected.append("python_repl")
    if any(word in text for word in ["internal", "report", "policy", "client", "previous", "recommendation"]):
        selected.append("document_retriever")

    if not selected:
        selected = ["web_search", "python_repl", "document_retriever"]

    state["ticker"] = _extract_ticker(question)
    state["selected_tools"] = selected
    state["memory"].append(f"Router selected {', '.join(selected)} for ticker {state['ticker']}.")
    return state


def run_web_search(state: FinancialResearchState) -> FinancialResearchState:
    if "web_search" in state["selected_tools"]:
        state["tool_results"]["web_search"] = web_search(state["question"], state["ticker"])
    return state


def run_calculator(state: FinancialResearchState) -> FinancialResearchState:
    if "calculator" in state["selected_tools"]:
        state["tool_results"]["calculator"] = calculator(state["question"])
    return state


def run_python_repl(state: FinancialResearchState) -> FinancialResearchState:
    if "python_repl" in state["selected_tools"]:
        state["tool_results"]["python_repl"] = python_market_analysis(state["ticker"])
    return state


def run_document_retriever(state: FinancialResearchState) -> FinancialResearchState:
    if "document_retriever" in state["selected_tools"]:
        state["tool_results"]["document_retriever"] = document_retriever(state["question"])
    return state


def synthesize_answer(state: FinancialResearchState) -> FinancialResearchState:
    """Combine tool outputs into an analyst-ready investment summary."""

    load_dotenv()
    prompt = _build_synthesis_prompt(state)

    api_key = os.getenv("OPENAI_API_KEY", "")
    if ChatOpenAI and api_key.startswith("sk-"):
        try:
            llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0.2)
            state["final_answer"] = llm.invoke(prompt).content
            state["memory"].append("Final answer synthesized with OpenAI.")
            return state
        except Exception as exc:
            state["memory"].append(f"OpenAI synthesis failed; used local synthesis. Error: {exc}")

    state["final_answer"] = _local_synthesis(state)
    state["memory"].append("Final answer synthesized locally.")
    return state


def _build_synthesis_prompt(state: FinancialResearchState) -> str:
    tool_text = "\n\n".join(f"{name}:\n{value}" for name, value in state["tool_results"].items())
    return (
        "You are a financial research assistant for investment analysts. "
        "Use the tool evidence below to produce a balanced research summary. "
        "Do not pretend this is financial advice. Include recommendation, rationale, risks, and next checks.\n\n"
        f"Analyst question: {state['question']}\n"
        f"Ticker: {state['ticker']}\n\n"
        f"Tool evidence:\n{tool_text}"
    )


def _local_synthesis(state: FinancialResearchState) -> str:
    lines = [
        f"Question: {state['question']}",
        f"Ticker analyzed: {state['ticker']}",
        "",
        "Tool findings:",
    ]
    for name, value in state["tool_results"].items():
        lines.append(f"- {name}: {value}")

    lines.extend(
        [
            "",
            "Investment summary:",
            "The available evidence supports a cautious, research-first view rather than an automatic buy/sell call.",
            "A recommendation should be finalized only after validating fresh market news, financial statements, valuation multiples, and internal risk rules.",
            "",
            "Suggested next checks:",
            "- Confirm the latest earnings release and guidance.",
            "- Compare valuation with sector peers.",
            "- Review internal client suitability and risk policy.",
            "- Stress test upside and downside scenarios before publishing a client report.",
            "",
            "Disclaimer: This is an educational research assistant output, not financial advice.",
        ]
    )
    return "\n".join(lines)


def build_financial_graph():
    graph = StateGraph(FinancialResearchState)

    graph.add_node("router", route_tools)
    graph.add_node("web_search", run_web_search)
    graph.add_node("calculator", run_calculator)
    graph.add_node("python_repl", run_python_repl)
    graph.add_node("document_retriever", run_document_retriever)
    graph.add_node("synthesize", synthesize_answer)

    graph.set_entry_point("router")
    graph.add_edge("router", "web_search")
    graph.add_edge("web_search", "calculator")
    graph.add_edge("calculator", "python_repl")
    graph.add_edge("python_repl", "document_retriever")
    graph.add_edge("document_retriever", "synthesize")
    graph.add_edge("synthesize", END)

    return graph.compile()
