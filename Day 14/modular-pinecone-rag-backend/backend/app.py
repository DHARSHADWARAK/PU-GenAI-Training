from __future__ import annotations

import shutil
from pathlib import Path
from functools import lru_cache

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from config import UPLOADS_DIR, settings
from loaders import DocumentLoaderFactory
from chunkers.factory import ChunkerFactory
from retrievers.factory import RetrieverFactory
from schemas import ComponentCatalog, IngestOptions, IngestResponse, QueryRequest, QueryResponse
from services import AppContainer, IngestionService, RAGService


@lru_cache(maxsize=1)
def get_container() -> AppContainer:
    return AppContainer()


def get_ingestion_service() -> IngestionService:
    return IngestionService(get_container())


def get_rag_service() -> RAGService:
    return RAGService(get_container())

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    return {
        "message": "Modular Pinecone RAG backend is running.",
        "health": "/health",
        "upload": "/documents/upload",
        "query": "/query",
        "components": "/components",
    }


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "pinecone_index": settings.pinecone_index_name,
        "default_chunker": settings.default_chunker,
        "default_retriever": settings.default_retriever,
        "openai_configured": bool(settings.openai_api_key),
        "pinecone_configured": bool(settings.pinecone_api_key),
    }


@app.get("/components", response_model=ComponentCatalog)
def list_components() -> ComponentCatalog:
    return ComponentCatalog(
        loaders=DocumentLoaderFactory().available_loaders(),
        chunkers=ChunkerFactory.available_chunkers(),
        retrievers=RetrieverFactory.available_retrievers(),
        vectorstores=["PineconeVectorStore"],
    )


@app.post("/documents/upload", response_model=IngestResponse)
async def upload_document(
    file: UploadFile = File(...),
    chunker: str = Form(settings.default_chunker),
    chunk_size: int = Form(settings.default_chunk_size),
    chunk_overlap: int = Form(settings.default_chunk_overlap),
    similarity_threshold: float = Form(settings.default_similarity_threshold),
    namespace: str = Form("default"),
) -> IngestResponse:
    ingestion_service = get_ingestion_service()
    destination = UPLOADS_DIR / Path(file.filename).name
    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    options = IngestOptions(
        chunker=chunker,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        similarity_threshold=similarity_threshold,
        namespace=namespace,
    )

    try:
        result = ingestion_service.ingest_file(destination, options)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to ingest document: {exc}") from exc

    return IngestResponse(**result)


@app.post("/query", response_model=QueryResponse)
def query_documents(payload: QueryRequest) -> QueryResponse:
    rag_service = get_rag_service()
    try:
        result = rag_service.answer(
            payload.question,
            retriever_name=payload.retriever,
            namespace=payload.namespace,
            top_k=payload.top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Query failed: {exc}") from exc

    return QueryResponse(**result)
