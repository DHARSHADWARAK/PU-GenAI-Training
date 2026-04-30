"""AI Shopping Assistant using router logic, prompt templates, and memory.

Run:
    python shopping_assistant.py

Optional OpenAI mode:
    set USE_OPENAI=1
    set OPENAI_API_KEY=sk-...
    python shopping_assistant.py
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from dotenv import load_dotenv
from langchain_core.example_selectors import LengthBasedExampleSelector
from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotPromptTemplate,
    PromptTemplate,
)

try:
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover - optional runtime dependency
    ChatOpenAI = None


@dataclass
class BufferMemory:
    """Stores the full support conversation."""

    messages: List[Dict[str, str]] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})

    def context(self) -> str:
        if not self.messages:
            return "No previous support conversation."
        return "\n".join(f"{item['role']}: {item['content']}" for item in self.messages)


@dataclass
class WindowMemory:
    """Stores only recent messages for lightweight FAQ flows."""

    k: int = 4
    messages: List[Dict[str, str]] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        self.messages = self.messages[-self.k :]

    def context(self) -> str:
        if not self.messages:
            return "No recent context."
        return "\n".join(f"{item['role']}: {item['content']}" for item in self.messages)


@dataclass
class SummaryMemory:
    """Keeps a compact running summary for larger FAQ sessions."""

    summary: str = ""

    def add(self, user_query: str, assistant_reply: str) -> None:
        event = f"User asked about '{user_query[:80]}'; assistant answered '{assistant_reply[:120]}'."
        if not self.summary:
            self.summary = event
            return
        self.summary = f"{self.summary} {event}"
        words = self.summary.split()
        self.summary = " ".join(words[-90:])

    def context(self) -> str:
        return self.summary or "No long-running FAQ summary yet."


@dataclass
class EntityMemory:
    """Stores useful shopping entities for personalization."""

    entities: Dict[str, str] = field(default_factory=dict)

    def update_from_text(self, text: str) -> None:
        name_match = re.search(r"\b(?:my name is|i am|i'm)\s+([a-zA-Z]+)", text, re.I)
        if name_match:
            self.entities["customer_name"] = name_match.group(1).title()

        order_match = re.search(r"\b(?:order\s*(?:id|number)?\s*[:#-]?\s*)([A-Z0-9-]{5,})\b", text, re.I)
        if order_match:
            self.entities["order_id"] = order_match.group(1).upper()

        budget_match = re.search(r"(?:under|below|less than|budget(?: is)?|up to)\s*(?:rs\.?|inr|₹)?\s*([0-9,]+)", text, re.I)
        if budget_match:
            self.entities["budget"] = budget_match.group(1).replace(",", "")

        product_words = [
            "phone",
            "laptop",
            "headphones",
            "earbuds",
            "shoes",
            "watch",
            "bag",
            "keyboard",
            "monitor",
            "tablet",
        ]
        lowered = text.lower()
        for word in product_words:
            if word in lowered:
                self.entities["product_interest"] = word

    def context(self) -> str:
        if not self.entities:
            return "No saved customer entities yet."
        return json.dumps(self.entities, indent=2)


@dataclass(frozen=True)
class Route:
    name: str
    chain_label: str
    prompt_type: str
    memory_type: str


class ShoppingRouterChain:
    """A simple router chain that maps customer intent to a specialized flow."""

    routes = {
        "product": Route(
            "product",
            "Product Recommendation Chain",
            "PromptTemplate",
            "Entity Memory",
        ),
        "support": Route(
            "support",
            "Customer Support Chain",
            "ChatPromptTemplate",
            "Conversation Buffer Memory",
        ),
        "return_refund": Route(
            "return_refund",
            "Return & Refund FAQ Chain",
            "FewShotPromptTemplate",
            "Conversation Window Memory",
        ),
        "large_faq": Route(
            "large_faq",
            "Large FAQ Chain",
            "Example Selector",
            "Summary Memory",
        ),
        "structured": Route(
            "structured",
            "Structured Output Chain",
            "Structured Output Prompt",
            "Optional Memory",
        ),
        "upsell": Route(
            "upsell",
            "Upselling Chain",
            "PromptTemplate",
            "Entity + Window Memory",
        ),
    }

    def route(self, query: str) -> Route:
        text = query.lower()
        if any(word in text for word in ["json", "api", "structured", "schema", "format"]):
            return self.routes["structured"]
        if any(word in text for word in ["bag too", "accessory", "accessories", "bundle", "add-on", "addon", "upsell"]):
            return self.routes["upsell"]
        if any(word in text for word in ["where is my order", "track", "delivery status", "order id", "order number"]):
            return self.routes["support"]
        if any(word in text for word in ["return", "refund", "replace", "exchange"]):
            return self.routes["return_refund"]
        if any(word in text for word in ["shipping", "cod", "cash on delivery", "cancel", "cancellation", "warranty"]):
            return self.routes["large_faq"]
        if any(word in text for word in ["suggest", "recommend", "under", "below", "buy", "best", "need"]):
            return self.routes["product"]
        return self.routes["support"]


class AIShoppingAssistant:
    def __init__(self, use_openai: bool = False) -> None:
        load_dotenv()
        self.router = ShoppingRouterChain()
        self.buffer_memory = BufferMemory()
        self.window_memory = WindowMemory(k=4)
        self.summary_memory = SummaryMemory()
        self.entity_memory = EntityMemory()
        self.llm = self._build_llm() if use_openai else None

        self.product_prompt = PromptTemplate.from_template(
            "You are an e-commerce product expert.\n"
            "Customer entities:\n{entities}\n"
            "User query: {query}\n"
            "Recommend 3 suitable products with short reasons, budget fit, and one buying tip."
        )

        self.support_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a calm customer support executive for an online shopping platform."),
                ("human", "Conversation so far:\n{history}\n\nLatest customer query: {query}"),
            ]
        )

        self.faq_example_prompt = PromptTemplate(
            input_variables=["question", "answer"],
            template="Customer: {question}\nAssistant: {answer}",
        )
        self.return_refund_prompt = FewShotPromptTemplate(
            examples=[
                {
                    "question": "Can I return shoes after delivery?",
                    "answer": "Yes. If they are unused and in original packaging, start a return from the order page within the return window.",
                },
                {
                    "question": "How long does refund take?",
                    "answer": "Refunds usually start after pickup or inspection and then follow the payment method timeline.",
                },
                {
                    "question": "Can I replace a damaged electronic item?",
                    "answer": "Yes. Share photos if requested and choose replacement from the order help page if the item is eligible.",
                },
            ],
            example_prompt=self.faq_example_prompt,
            prefix="Answer return and refund questions using the policy style in these examples.",
            suffix="Recent context:\n{recent_context}\n\nCustomer: {query}\nAssistant:",
            input_variables=["query", "recent_context"],
        )

        self.large_faq_examples = [
            {
                "question": "Is cash on delivery available?",
                "answer": "COD availability depends on pincode, product, and seller. Check it on the checkout page.",
            },
            {
                "question": "Can I cancel my order?",
                "answer": "You can cancel before shipping from the order details page. After shipping, return options may apply.",
            },
            {
                "question": "What is covered in warranty?",
                "answer": "Warranty is usually handled by the brand and covers manufacturing defects, not physical damage.",
            },
            {
                "question": "How fast is shipping?",
                "answer": "Delivery speed depends on location, seller, and item availability. The checkout page shows the exact estimate.",
            },
        ]
        self.large_faq_selector = LengthBasedExampleSelector(
            examples=self.large_faq_examples,
            example_prompt=self.faq_example_prompt,
            max_length=90,
        )

        self.structured_prompt = PromptTemplate.from_template(
            "Return product information as valid JSON only.\n"
            "Customer entities: {entities}\n"
            "Customer query: {query}\n"
            "Required keys: intent, product_type, budget, recommendation_summary, next_action."
        )

        self.upsell_prompt = PromptTemplate.from_template(
            "Customer entities:\n{entities}\n"
            "Recent context:\n{recent_context}\n"
            "User query: {query}\n"
            "Suggest one useful add-on product without being pushy."
        )

    def _build_llm(self):
        api_key = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")
        if not ChatOpenAI or not api_key.startswith("sk-"):
            return None
        return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0.2)

    def ask(self, query: str) -> Dict[str, str]:
        self.entity_memory.update_from_text(query)
        route = self.router.route(query)

        if route.name == "product":
            prompt = self.product_prompt.format(query=query, entities=self.entity_memory.context())
            answer = self._llm_or_fallback(prompt, self._product_answer(query))
            self.entity_memory.update_from_text(answer)
        elif route.name == "support":
            prompt_value = self.support_prompt.format_messages(history=self.buffer_memory.context(), query=query)
            prompt = "\n".join(f"{message.type}: {message.content}" for message in prompt_value)
            answer = self._llm_or_fallback(prompt, self._support_answer(query))
            self.buffer_memory.add("customer", query)
            self.buffer_memory.add("assistant", answer)
        elif route.name == "return_refund":
            prompt = self.return_refund_prompt.format(query=query, recent_context=self.window_memory.context())
            answer = self._llm_or_fallback(prompt, self._return_refund_answer(query))
            self.window_memory.add("customer", query)
            self.window_memory.add("assistant", answer)
        elif route.name == "large_faq":
            examples = self.large_faq_selector.select_examples({"question": query})
            rendered_examples = "\n\n".join(self.faq_example_prompt.format(**example) for example in examples)
            prompt = (
                "Answer using the most relevant FAQ examples.\n\n"
                f"Running summary:\n{self.summary_memory.context()}\n\n"
                f"Selected examples:\n{rendered_examples}\n\n"
                f"Customer: {query}\nAssistant:"
            )
            answer = self._llm_or_fallback(prompt, self._large_faq_answer(query))
            self.summary_memory.add(query, answer)
        elif route.name == "structured":
            prompt = self.structured_prompt.format(query=query, entities=self.entity_memory.context())
            answer = self._structured_answer(query)
        else:
            prompt = self.upsell_prompt.format(
                query=query,
                entities=self.entity_memory.context(),
                recent_context=self.window_memory.context(),
            )
            answer = self._llm_or_fallback(prompt, self._upsell_answer(query))
            self.window_memory.add("customer", query)
            self.window_memory.add("assistant", answer)

        return {
            "route": route.chain_label,
            "prompt_type": route.prompt_type,
            "memory_type": route.memory_type,
            "prompt": prompt,
            "answer": answer,
        }

    def _llm_or_fallback(self, prompt: str, fallback: str) -> str:
        if self.llm is None:
            return fallback
        try:
            return self.llm.invoke(prompt).content
        except Exception as exc:
            return f"{fallback}\n\n[Local fallback used because the LLM call failed: {exc}]"

    def _product_answer(self, query: str) -> str:
        product = self.entity_memory.entities.get("product_interest", "product")
        budget = self.entity_memory.entities.get("budget", "your budget")
        return (
            f"Here are 3 {product} options that should fit around {budget}: "
            f"1. Value pick for everyday use, 2. Balanced pick with better durability, "
            f"3. Premium pick if you can stretch slightly. Check ratings, return window, and warranty before ordering."
        )

    def _support_answer(self, query: str) -> str:
        text = query.lower()
        customer_name = self.entity_memory.entities.get("customer_name")
        if "my name" in text or "what is my name" in text:
            if customer_name:
                return f"Your name is {customer_name}."
            return "I do not know your name yet. You can tell me by saying, 'my name is ...'."

        order_id = self.entity_memory.entities.get("order_id")
        if order_id:
            return (
                f"I found order {order_id} in the conversation. Please check the order page for the live status; "
                "if it is delayed, I can help raise a delivery support request."
            )
        if any(word in text for word in ["hello", "hi", "hey"]):
            if customer_name:
                return f"Hello {customer_name}, how can I help with your shopping today?"
            return "Hello, how can I help with your shopping today?"
        return "I can help track it. Please share your order ID or the phone/email used for the order."

    def _return_refund_answer(self, query: str) -> str:
        text = query.lower()
        if "refund" in text:
            return "Refunds usually begin after pickup or inspection. Bank/card timelines can take a few business days."
        if "electronics" in text:
            return "Electronics are usually eligible only if the item is defective, damaged, or not as described, and within the policy window."
        return "You can request a return or replacement from the order page if the item is eligible and inside the return window."

    def _large_faq_answer(self, query: str) -> str:
        text = query.lower()
        if "cod" in text or "cash on delivery" in text:
            return "COD depends on your pincode, seller, item value, and account eligibility. The checkout page confirms availability."
        if "cancel" in text:
            return "You can cancel before shipping from the order details page. After dispatch, use return/refund options if eligible."
        if "warranty" in text:
            return "Warranty is normally provided by the brand and covers manufacturing defects. Keep the invoice for claims."
        return "Shipping estimates depend on pincode, seller, and stock. The exact promise date appears on product and checkout pages."

    def _structured_answer(self, query: str) -> str:
        entities = self.entity_memory.entities
        payload = {
            "intent": "structured_product_details",
            "product_type": entities.get("product_interest", "unknown"),
            "budget": entities.get("budget", "not specified"),
            "recommendation_summary": "Share product, budget, and must-have features for a precise recommendation.",
            "next_action": "collect_missing_preferences" if "product_interest" not in entities else "show_ranked_options",
        }
        return json.dumps(payload, indent=2)

    def _upsell_answer(self, query: str) -> str:
        product = self.entity_memory.entities.get("product_interest", "item")
        addons = {
            "laptop": "a padded laptop bag or wireless mouse",
            "phone": "a tempered glass screen protector and protective case",
            "headphones": "a compact carry case",
            "shoes": "shoe cleaner or comfort insoles",
            "watch": "an extra strap",
        }
        addon = addons.get(product, "a useful compatible accessory")
        return f"Since you are considering a {product}, you may also find {addon} helpful. I can keep it within your budget."


def run_demo(queries: Iterable[str]) -> None:
    load_dotenv()
    assistant = AIShoppingAssistant(use_openai=os.getenv("USE_OPENAI") == "1")
    for query in queries:
        result = assistant.ask(query)
        print("\nUser:", query)
        print("Route:", result["route"])
        print("Prompt:", result["prompt_type"])
        print("Memory:", result["memory_type"])
        print("Assistant:", result["answer"])


def main() -> None:
    load_dotenv()
    assistant = AIShoppingAssistant(use_openai=os.getenv("USE_OPENAI") == "1")
    print("AI Shopping Assistant")
    print(f"Mode: {'OpenAI LLM' if assistant.llm else 'Local fallback'}")
    print("Type 'exit' to stop. Type 'debug: your question' to see the rendered prompt.")
    while True:
        query = input("\nCustomer: ").strip()
        if query.lower() in {"exit", "quit"}:
            break
        show_prompt = query.lower().startswith("debug:")
        if show_prompt:
            query = query.split(":", 1)[1].strip()
        result = assistant.ask(query)
        print(f"\nRoute: {result['route']} | Prompt: {result['prompt_type']} | Memory: {result['memory_type']}")
        if show_prompt:
            print("\nRendered prompt:\n" + result["prompt"])
        print("\nAssistant:", result["answer"])


if __name__ == "__main__":
    main()
