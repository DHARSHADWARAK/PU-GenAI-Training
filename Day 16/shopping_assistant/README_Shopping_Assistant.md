# AI Shopping Assistant using Router Chain, Prompt Templates, and Memory

This folder contains a runnable implementation of the Day 16 assignment.

## Run

```powershell
python shopping_assistant.py
```

Optional OpenAI mode:

```powershell
$env:USE_OPENAI="1"
$env:OPENAI_API_KEY="sk-..."
python shopping_assistant.py
```

Without `USE_OPENAI=1`, the app runs fully offline with deterministic fallback responses. It still uses LangChain prompt templates and example selection for the assignment concepts.

## Architecture Diagram

```text
Customer
   |
   v
ShoppingRouterChain
   |
   +--> Product Recommendation Chain --> PromptTemplate ---------> Entity Memory
   |
   +--> Customer Support Chain --------> ChatPromptTemplate ------> Buffer Memory
   |
   +--> Return & Refund FAQ Chain -----> FewShotPromptTemplate ---> Window Memory
   |
   +--> Large FAQ Chain ---------------> Example Selector --------> Summary Memory
   |
   +--> Structured Output Chain -------> Structured JSON Prompt --> Optional Memory
   |
   +--> Upselling Chain ---------------> PromptTemplate ---------> Entity + Window Memory
   |
   v
Assistant Response
```

## Router Logic

`ShoppingRouterChain.route()` reads the user query and maps it to an intent:

- Product recommendation: words like `suggest`, `recommend`, `under`, `buy`, `best`, `need`
- Customer support: order tracking or delivery status queries
- Return and refund FAQ: `return`, `refund`, `replace`, `exchange`
- Large FAQ: `shipping`, `COD`, `cancellation`, `warranty`
- Structured output: `JSON`, `API`, `structured`, `schema`, `format`
- Upselling: `accessory`, `bundle`, `add-on`, `upsell`

The route decides the specialized chain, prompt style, and memory type.

## Chain-wise Explanation

| Chain | Use Case | Prompt Type | Memory Used | Why |
|---|---|---|---|---|
| Product Recommendation | Suggest products based on budget/preferences | `PromptTemplate` | Entity Memory | Product, budget, and customer preferences are reusable entities |
| Customer Support | Track orders and continue support conversations | `ChatPromptTemplate` | Conversation Buffer Memory | Support needs the full context |
| Return & Refund FAQ | Answer policy questions | `FewShotPromptTemplate` | Conversation Window Memory | Few-shot examples keep policy tone consistent; recent context is enough |
| Large FAQ | Shipping, COD, cancellation, warranty | Example Selector | Summary Memory | Dynamic examples and compact history help longer FAQ sessions |
| Structured Output | JSON/API-style product details | Structured Output Prompt | Optional Memory | Output format is more important than chat history |
| Upselling | Suggest a relevant add-on | `PromptTemplate` | Entity + Window Memory | Add-ons should match current product interest |

## Prompt Comparison

| Prompt Type | Best Use |
|---|---|
| `PromptTemplate` | Simple recommendations |
| `ChatPromptTemplate` | Conversation and role-based support |
| `FewShotPromptTemplate` | FAQ learning from examples |
| Example Selector | Large FAQ systems with dynamic examples |
| Structured Output Prompt | JSON/API output |

## Memory Comparison

| Memory Type | Best Use |
|---|---|
| Buffer Memory | Full conversation |
| Window Memory | Recent chat |
| Summary Memory | Long history |
| Entity Memory | Important details like name, order ID, product, budget |

## Example Questions

```text
Suggest headphones under 2000
Where is my order ORD12345?
Can I return electronics?
Is COD available and what about warranty?
Give product details in JSON format for a phone under 20000
I bought a laptop, suggest an accessory
```
