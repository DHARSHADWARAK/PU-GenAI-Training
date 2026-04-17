import re
from rank_bm25 import BM25Okapi
from sarvamai import SarvamAI

# ----------------------------
# PREPROCESS
# ----------------------------
def preprocess(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# ----------------------------
# TOKENIZATION
# ----------------------------
def tokenize(text):
    return text.split()

# ----------------------------
# CHUNKING
# ----------------------------
def chunk_text(text, size=100, overlap=30):
    words = text.split()
    chunks = []

    for i in range(0, len(words), size - overlap):
        chunk = ' '.join(words[i:i+size])
        chunks.append(chunk)

    return chunks

# ----------------------------
# BM25 RAG CLASS
# ----------------------------
class BM25RAG:
    def __init__(self):
        self.chunks = []
        self.tokenized_chunks = []
        self.bm25 = None

    def add_document(self, text):
        text = preprocess(text)
        chunks = chunk_text(text)

        original_chunks = chunk_text(text)   # BEFORE preprocess

        processed_text = preprocess(text)
        processed_chunks = chunk_text(processed_text)

        self.chunks.extend(original_chunks)  # store ORIGINAL
        self.tokenized_chunks = [tokenize(c) for c in processed_chunks]
        self.tokenized_chunks = [tokenize(c) for c in self.chunks]

        self.bm25 = BM25Okapi(self.tokenized_chunks)

    def query(self, query_text, top_k=3):
        query_text = preprocess(query_text)
        tokenized_query = tokenize(query_text)

        scores = self.bm25.get_scores(tokenized_query)

        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = [(self.chunks[i], scores[i]) for i in top_indices]
        return results


# ----------------------------
# LLM SETUP
# ----------------------------
from urllib import response


client = SarvamAI(
    api_subscription_key="",
)

def generate_answer(query, retrieved_chunks):
    # 🔥 Create context
    context = "\n\n".join([chunk for chunk, _ in retrieved_chunks])

    # 🔥 Prompt engineering (VERY IMPORTANT)
    prompt = f"""
You are a helpful AI assistant.

Use ONLY the context below to answer the question.
If the answer is not in the context, say "Not found in document".

Context:
{context}

Question:
{query}

Answer:
"""

    response = client.chat.completions(
        model="sarvam-105b",
        messages=[

            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
    )

    print(response)
    return response.choices[0].message.content or "⚠️ Empty response from LLM"

# ----------------------------
# MAIN
# ----------------------------
if __name__ == "__main__":
    rag = BM25RAG()

    file_path = input("Enter file path: ")

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    rag.add_document(text)

    while True:
        query = input("\nEnter query (or 'exit'): ")
        if query.lower() == "exit":
            break

        # 🔍 Retrieve chunks
        results = rag.query(query)

        print("\nTop Retrieved Chunks:\n")
        for chunk, score in results:
            print(f"Score: {score:.4f}")
            print(chunk)
            print("-" * 50)

        # 🤖 Generate answer using LLM
        answer = generate_answer(query, results)

        print("\n🧠 Final Answer:\n")
        print(answer)