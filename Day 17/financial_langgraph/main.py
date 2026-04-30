"""Financial Research Assistant using LangGraph.

Run:
    python main.py

Optional API keys can be placed in a local .env file:
    OPENAI_API_KEY=sk-...
    SERPER_API_KEY=...
"""

from __future__ import annotations

from dotenv import load_dotenv

from workflow import build_financial_graph


def run_question(question: str) -> None:
    graph = build_financial_graph()
    initial_state = {
        "question": question,
        "ticker": "",
        "selected_tools": [],
        "tool_results": {},
        "memory": [],
        "final_answer": "",
    }

    print("=" * 80)
    print(f"User: {question}")
    print("=" * 80)

    result = initial_state
    previous_tool_results = {}

    for event in graph.stream(initial_state):
        node_name, state = next(iter(event.items()))
        result = state

        if node_name == "router":
            print("[Agent Node] Thinking...")
            print(f"[Agent Node] Detected ticker/context: {state['ticker']}")
            print(f"[Agent Node] Decided to use tool(s): {state['selected_tools']}")

        elif node_name in {"web_search", "calculator", "python_repl", "document_retriever"}:
            new_results = {
                name: value
                for name, value in state["tool_results"].items()
                if name not in previous_tool_results
            }
            if new_results:
                print("[Tool Node] Executing tool(s)...")
                for tool_name, value in new_results.items():
                    args = _tool_args(tool_name, state)
                    print(f"[Tool Node] Running '{tool_name}' with args: {args}")
                    print(f"[Tool Node] Result: {value}")
                previous_tool_results = dict(state["tool_results"])

        elif node_name == "synthesize":
            print("[Agent Node] Thinking...")
            print("[Agent Node] No more tools needed. Combining evidence into final answer.")

    print("\nAgent:", result["final_answer"])


def _tool_args(tool_name: str, state: dict) -> dict:
    if tool_name == "web_search":
        return {"query": state["question"], "ticker": state["ticker"]}
    if tool_name == "calculator":
        return {"question": state["question"]}
    if tool_name == "python_repl":
        return {"ticker": state["ticker"]}
    if tool_name == "document_retriever":
        return {"query": state["question"]}
    return {}


def main() -> None:
    load_dotenv()
    print("Financial Research Assistant using LangGraph")
    print("Type 'exit' to stop.\n")

    while True:
        question = input("Analyst question: ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        if not question:
            continue
        run_question(question)
        print("\n" + "-" * 80 + "\n")


if __name__ == "__main__":
    main()
