const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail =
      typeof payload === "string"
        ? payload
        : payload?.detail || payload?.message || "Request failed.";
    throw new Error(detail);
  }

  return payload;
}

export async function fetchHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  return parseResponse(response);
}

export async function fetchComponents() {
  const response = await fetch(`${API_BASE_URL}/components`);
  return parseResponse(response);
}

export async function uploadDocument({
  file,
  chunker,
  chunkSize,
  chunkOverlap,
  similarityThreshold,
  namespace,
}) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("chunker", chunker);
  formData.append("chunk_size", String(chunkSize));
  formData.append("chunk_overlap", String(chunkOverlap));
  formData.append("similarity_threshold", String(similarityThreshold));
  formData.append("namespace", namespace);

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: "POST",
    body: formData,
  });
  return parseResponse(response);
}

export async function queryDocuments({ question, namespace, topK, retriever }) {
  const response = await fetch(`${API_BASE_URL}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      namespace,
      top_k: Number(topK),
      retriever,
    }),
  });
  return parseResponse(response);
}
