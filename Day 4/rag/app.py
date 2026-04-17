from fastapi import FastAPI
from pydantic import BaseModel
from mini_rag import BM25RAG, generate_answer  # import your code

app = FastAPI()

rag = BM25RAG()

# Load document once
with open("Spider_Man.txt", "r", encoding="utf-8") as f:
    rag.add_document(f.read())

class QueryRequest(BaseModel):
    query: str

@app.post("/ask")
def ask_question(req: QueryRequest):
    results = rag.query(req.query)
    answer = generate_answer(req.query, results)

    return {
        "query": req.query,
        "answer": answer,
        "chunks": [chunk for chunk, _ in results]
    }

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 🔥 ADD THIS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all (dev mode)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)