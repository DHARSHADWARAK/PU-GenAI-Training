import { useEffect, useState, startTransition } from "react";
import { fetchComponents, fetchHealth, queryDocuments, uploadDocument } from "./api/client";
import AnswerPanel from "./components/AnswerPanel";
import MatchesPanel from "./components/MatchesPanel";
import QueryPanel from "./components/QueryPanel";
import StatusStrip from "./components/StatusStrip";
import UploadPanel from "./components/UploadPanel";

const initialUploadForm = {
  chunker: "recursive",
  namespace: "default",
  chunkSize: 800,
  chunkOverlap: 100,
  similarityThreshold: 0.82,
};

const initialQueryForm = {
  question: "What are the main ideas in this document?",
  namespace: "default",
  retriever: "pinecone",
  topK: 3,
};

function App() {
  const [health, setHealth] = useState(null);
  const [components, setComponents] = useState({ chunkers: ["recursive"], retrievers: ["pinecone"] });
  const [statusError, setStatusError] = useState("");
  const [statusLoading, setStatusLoading] = useState(true);

  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadForm, setUploadForm] = useState(initialUploadForm);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError] = useState("");

  const [queryForm, setQueryForm] = useState(initialQueryForm);
  const [querying, setQuerying] = useState(false);
  const [queryResult, setQueryResult] = useState(null);
  const [queryError, setQueryError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadStatus() {
      setStatusLoading(true);
      setStatusError("");

      try {
        const [healthData, componentData] = await Promise.all([fetchHealth(), fetchComponents()]);
        if (cancelled) {
          return;
        }

        startTransition(() => {
          setHealth(healthData);
          setComponents(componentData);
          setUploadForm((current) => ({
            ...current,
            chunker: componentData.chunkers?.includes(current.chunker)
              ? current.chunker
              : componentData.chunkers?.[0] || current.chunker,
          }));
          setQueryForm((current) => ({
            ...current,
            retriever: componentData.retrievers?.includes(current.retriever)
              ? current.retriever
              : componentData.retrievers?.[0] || current.retriever,
          }));
        });
      } catch (error) {
        if (!cancelled) {
          setStatusError(error.message || "Failed to connect to the backend.");
        }
      } finally {
        if (!cancelled) {
          setStatusLoading(false);
        }
      }
    }

    loadStatus();
    return () => {
      cancelled = true;
    };
  }, []);

  function handleUploadChange(event) {
    const { name, value } = event.target;
    setUploadForm((current) => ({ ...current, [name]: value }));
  }

  function handleQueryChange(event) {
    const { name, value } = event.target;
    setQueryForm((current) => ({ ...current, [name]: value }));
  }

  function handleFileChange(event) {
    setSelectedFile(event.target.files?.[0] || null);
  }

  async function handleUploadSubmit(event) {
    event.preventDefault();
    if (!selectedFile) {
      setUploadError("Choose a document before uploading.");
      return;
    }

    setUploading(true);
    setUploadError("");

    try {
      const result = await uploadDocument({
        file: selectedFile,
        chunker: uploadForm.chunker,
        chunkSize: uploadForm.chunkSize,
        chunkOverlap: uploadForm.chunkOverlap,
        similarityThreshold: uploadForm.similarityThreshold,
        namespace: uploadForm.namespace,
      });
      setUploadResult(result);
      setQueryForm((current) => ({ ...current, namespace: result.namespace }));
    } catch (error) {
      setUploadError(error.message || "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  async function handleQuerySubmit(event) {
    event.preventDefault();
    setQuerying(true);
    setQueryError("");

    try {
      const result = await queryDocuments({
        question: queryForm.question,
        namespace: queryForm.namespace,
        topK: queryForm.topK,
        retriever: queryForm.retriever,
      });
      setQueryResult(result);
    } catch (error) {
      setQueryError(error.message || "Query failed.");
    } finally {
      setQuerying(false);
    }
  }

  return (
    <div className="page-shell">
      <main className="app-shell">
        <section className="hero-card">
          <div className="hero-copy-wrap">
            <p className="eyebrow">Day 14 • Modular Pinecone RAG Studio</p>
            <h1>Upload documents, switch chunkers, and inspect retrieval without touching backend code.</h1>
            <p className="hero-copy">
              This frontend sits on top of your modular FastAPI backend and gives you a single workspace for
              ingestion, retrieval, and answer inspection. It is designed to make experimentation fast when you
              change chunkers, retrievers, namespaces, or future loader implementations.
            </p>
          </div>
          <div className="hero-orbital">
            <div className="orbit-card">
              <span>Load</span>
              <strong>Documents</strong>
            </div>
            <div className="orbit-card">
              <span>Swap</span>
              <strong>Chunkers</strong>
            </div>
            <div className="orbit-card">
              <span>Inspect</span>
              <strong>Matches</strong>
            </div>
          </div>
        </section>

        <StatusStrip
          health={health}
          components={components}
          loading={statusLoading}
          error={statusError}
        />

        <div className="workspace-grid">
          <UploadPanel
            uploadForm={uploadForm}
            onUploadChange={handleUploadChange}
            onFileChange={handleFileChange}
            onUploadSubmit={handleUploadSubmit}
            uploading={uploading}
            uploadResult={uploadResult}
            uploadError={uploadError}
            availableChunkers={components.chunkers || ["recursive"]}
          />

          <QueryPanel
            queryForm={queryForm}
            onQueryChange={handleQueryChange}
            onQuerySubmit={handleQuerySubmit}
            querying={querying}
            queryError={queryError}
            availableRetrievers={components.retrievers || ["pinecone"]}
          />
        </div>

        <div className="results-grid">
          <AnswerPanel result={queryResult} loading={querying} />
          <MatchesPanel matches={queryResult?.matches || []} />
        </div>
      </main>
    </div>
  );
}

export default App;
