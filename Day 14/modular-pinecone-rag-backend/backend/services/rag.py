from __future__ import annotations

from openai import OpenAI

from config import settings
from schemas import RetrievedChunk
from services.container import AppContainer


class RAGService:
    def __init__(self, container: AppContainer) -> None:
        self.container = container
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required for answer generation.")
            self._client = OpenAI(api_key=settings.openai_api_key)
        return self._client

    def answer(self, question: str, *, retriever_name: str, namespace: str, top_k: int) -> dict:
        retriever = self.container.retriever_factory.create(retriever_name)
        matches = retriever.retrieve(question, top_k=top_k, namespace=namespace)

        context_parts = []
        serialized_matches: list[RetrievedChunk] = []
        for match in matches:
            metadata = match.get("metadata", {})
            text = metadata.get("text", "")
            context_parts.append(text)
            serialized_matches.append(
                RetrievedChunk(
                    id=str(match.get("id", "")),
                    score=match.get("score"),
                    text=text,
                    source=metadata.get("source"),
                    chunker=metadata.get("chunker"),
                )
            )

        context = "\n\n".join(context_parts)
        prompt = (
            f"Context:\n{context}\n\n"
            f"Question:\n{question}\n\n"
            "Answer using only the context above. If the answer is not in the context, say that clearly."
        )

        response = self.client.chat.completions.create(
            model=settings.openai_chat_model,
            messages=[
                {"role": "system", "content": settings.system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        answer = (response.choices[0].message.content or "").strip()

        return {
            "question": question,
            "answer": answer,
            "retriever": retriever_name,
            "namespace": namespace,
            "top_k": top_k,
            "matches": serialized_matches,
        }
