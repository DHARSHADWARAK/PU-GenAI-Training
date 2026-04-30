from __future__ import annotations

from pydantic import BaseModel, Field


class IngestOptions(BaseModel):
    chunker: str = "recursive"
    chunk_size: int = Field(default=800, ge=100, le=4000)
    chunk_overlap: int = Field(default=100, ge=0, le=2000)
    similarity_threshold: float = Field(default=0.82, ge=0.0, le=1.0)
    namespace: str = "default"


class IngestResponse(BaseModel):
    file_name: str
    file_path: str
    namespace: str
    chunker: str
    chunks_indexed: int
    index_name: str


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=2)
    namespace: str = "default"
    top_k: int = Field(default=3, ge=1, le=20)
    retriever: str = "pinecone"


class RetrievedChunk(BaseModel):
    id: str
    score: float | None = None
    text: str
    source: str | None = None
    chunker: str | None = None


class QueryResponse(BaseModel):
    question: str
    answer: str
    retriever: str
    namespace: str
    top_k: int
    matches: list[RetrievedChunk]


class ComponentCatalog(BaseModel):
    loaders: list[str]
    chunkers: list[str]
    retrievers: list[str]
    vectorstores: list[str]
