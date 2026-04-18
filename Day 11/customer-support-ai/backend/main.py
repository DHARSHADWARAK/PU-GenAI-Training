from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import settings
from llm_client import generate_response
from logger import get_app_logger, log_interaction
from prompt_builder import build_prompt
from retriever import PolicyRetriever


app_logger = get_app_logger()
retriever: PolicyRetriever | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global retriever
    retriever = PolicyRetriever(settings.policies_path)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    complaint: str = Field(..., min_length=5)
    mode: Literal["strict", "friendly"] = "strict"


class RetrievedDoc(BaseModel):
    id: int | None = None
    title: str
    category: str | None = None
    solution: str | None = None
    alternate_solution: str | None = None
    company_response: str | None = None
    bm25_score: float | None = None


class GenerateResponse(BaseModel):
    complaint: str
    mode: str
    response: str
    scenario: str
    parameters: dict
    top_score: float
    is_fallback: bool
    docs: list[RetrievedDoc]
    prompt: str
    context: str
    llm_model: str
    used_mock: bool
    llm_error: str | None = None


@app.get("/")
def root() -> dict:
    return {
        "message": "Customer Support AI backend is running.",
        "health": "/health",
        "generate": "/generate",
    }


@app.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "groq_configured": bool(settings.groq_api_key),
        "policies_path": str(settings.policies_path),
    }


@app.post("/generate", response_model=GenerateResponse)
def generate_support_response(payload: GenerateRequest) -> GenerateResponse:
    if retriever is None:
        raise HTTPException(status_code=503, detail="Retriever is not ready yet.")

    complaint = payload.complaint.strip()
    if not complaint:
        raise HTTPException(status_code=400, detail="Complaint cannot be empty.")

    retrieval = retriever.retrieve(complaint, top_k=settings.top_k)
    prompt_data = build_prompt(complaint, retrieval["docs"], payload.mode, retrieval["is_fallback"])
    llm_output = generate_response(
        prompt_data["prompt"],
        prompt_data["temperature"],
        prompt_data["max_tokens"],
        system_prompt=prompt_data["system_prompt"],
        query=complaint,
        docs=retrieval["docs"],
        retry_prompt=prompt_data["retry_prompt"],
        is_fallback=retrieval["is_fallback"],
        mode=payload.mode,
    )

    result = GenerateResponse(
        complaint=complaint,
        mode=payload.mode,
        response=llm_output["text"],
        scenario=prompt_data["scenario"],
        parameters={
            "temperature": prompt_data["temperature"],
            "max_tokens": prompt_data["max_tokens"],
            "top_k": settings.top_k,
        },
        top_score=retrieval["top_score"],
        is_fallback=retrieval["is_fallback"],
        docs=retrieval["docs"],
        prompt=prompt_data["prompt"],
        context=prompt_data["context"],
        llm_model=llm_output["model"],
        used_mock=llm_output["used_mock"],
        llm_error=llm_output["error"],
    )

    log_interaction(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": complaint,
            "mode": payload.mode,
            "scenario": result.scenario,
            "retrieved_docs": [doc["title"] for doc in retrieval["docs"]],
            "top_score": retrieval["top_score"],
            "is_fallback": retrieval["is_fallback"],
            "prompt": prompt_data["prompt"],
            "parameters": result.parameters,
            "llm_model": llm_output["model"],
            "used_mock": llm_output["used_mock"],
            "llm_error": llm_output["error"],
            "response": llm_output["text"],
        }
    )
    app_logger.info("Processed complaint in %s mode", payload.mode)
    return result
