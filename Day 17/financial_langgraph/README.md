# Financial Research Assistant using LangGraph

This project implements the Day 17 use case from the PDF: an agentic AI workflow for financial research.

## What It Does

The assistant receives an analyst question, routes it through a LangGraph workflow, calls the relevant tools, and combines the evidence into an investment research summary.

Example:

```text
Should we recommend investing in Tesla this quarter? Include latest news, trend analysis, and previous internal recommendations.
```

## Architecture

```text
Analyst Question
      |
      v
Router Node
      |
      +--> Web Search Tool: latest market news through Serper API
      |
      +--> Calculator Tool: ROI, margin, interest, ratios, arithmetic
      |
      +--> Python REPL Tool: trend analysis and performance calculations
      |
      +--> Document Retriever Tool: internal reports and policy docs
      |
      v
Synthesis Node
      |
      v
Investment Research Summary
```

## Files

| File | Purpose |
|---|---|
| `main.py` | CLI entry point |
| `workflow.py` | LangGraph state, nodes, routing, and synthesis |
| `tools.py` | Web search, calculator, Python analysis, document retriever |
| `docs/` | Sample internal company documents |
| `.env.example` | Optional API key template |
| `requirements.txt` | Dependencies |

## Setup

```powershell
cd "c:\Users\Administrator\Downloads\ML\PU-GenAI-Training\Day 17\financial_langgraph"
pip install -r requirements.txt
```

Create `.env` if you want live LLM synthesis or Serper search:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
SERPER_API_KEY=your_serper_key
```

The project still runs without API keys using local fallbacks.

## Run

```powershell
python main.py
```

## Sample Questions

```text
Should we recommend investing in Tesla this quarter? Include latest news, trend analysis, and previous internal recommendations.
Calculate ROI if we buy at 100 and sell at 125.
Analyze NVDA trend performance and compare with internal recommendation.
What does internal policy say about high volatility growth stocks?
Calculate profit margin with revenue 1000000 and cost 720000.
```

## Tool Routing Logic

| Query Signal | Tool |
|---|---|
| latest, news, market, earnings, sentiment, quarter | Web Search |
| ROI, return, margin, interest, calculate, ratio, % | Calculator |
| trend, forecast, performance, compare, chart, analysis | Python REPL |
| internal, report, policy, client, previous, recommendation | Document Retriever |

## Notes

- This is an educational assistant and not financial advice.
- Serper search needs `SERPER_API_KEY`.
- OpenAI synthesis needs `OPENAI_API_KEY`; otherwise the local synthesis node is used.
