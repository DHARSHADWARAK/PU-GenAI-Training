# Modular Pinecone RAG Backend

This Day 14 project turns the Pinecone notebook flow into a modular FastAPI backend.

## Why this structure

Each concern is isolated so you can swap pieces without rewriting the app:

- `backend/loaders/`: document ingestion by file type
- `backend/chunkers/`: chunking strategies such as fixed, sentence, paragraph, recursive, and semantic
- `backend/embeddings/`: embedding providers
- `backend/vectorstores/`: vector database adapters
- `backend/retrievers/`: retrieval strategies
- `backend/services/`: orchestration for indexing and answering
- `backend/app.py`: API entrypoint only

## Endpoints

- `GET /health`
- `GET /components`
- `POST /documents/upload`
- `POST /query`

## Frontend

A React + Vite frontend is included in `frontend/` so you can upload files, change chunkers, run queries, and inspect retrieved chunks visually.

```bash
cd "Day 14/modular-pinecone-rag-backend/frontend"
npm install
npm run dev
```

Set `VITE_API_BASE_URL` in `frontend/.env` if your backend is running on a different host or port.

## Run locally

```bash
cd "Day 14/modular-pinecone-rag-backend/backend"
pip install -r requirements.txt
uvicorn app:app --reload
```

Copy `.env.example` to `.env` in either the project root or `backend/` and fill in your OpenAI and Pinecone keys.

The app can start without keys, but ingest and query operations will return clear errors until the required credentials are configured.

## Swap components

### Change chunker

Set the default in `.env`:

```env
DEFAULT_CHUNKER=semantic
```

Or send a different `chunker` value during upload:

- `fixed`
- `paragraph`
- `sentence`
- `recursive`
- `semantic`

### Add a new retriever

1. Create a new class in `backend/retrievers/` that extends `BaseRetriever`
2. Register it in `RetrieverFactory.create`
3. Call `/query` with that retriever name

### Add a new loader

1. Create a loader class in `backend/loaders/`
2. Define `supported_extensions`
3. Register it in `DocumentLoaderFactory`

## Example upload request

Use a tool like Postman or curl with multipart form data:

- `file`: your `.pdf` or `.txt`
- `chunker`: `recursive`
- `chunk_size`: `800`
- `chunk_overlap`: `100`
- `similarity_threshold`: `0.82`
- `namespace`: `default`

## Example query payload

```json
{
  "question": "What does the document say about Iron Man?",
  "namespace": "default",
  "top_k": 3,
  "retriever": "pinecone"
}
```
