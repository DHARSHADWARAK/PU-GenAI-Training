function StatusStrip({ health, components, loading, error }) {
  return (
    <section className="panel status-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Backend Snapshot</p>
          <h2>Check the API before you start indexing.</h2>
        </div>
        <span className={`status-badge ${health?.status === "ok" ? "is-live" : ""}`}>
          {loading ? "Loading..." : health?.status === "ok" ? "Connected" : "Unavailable"}
        </span>
      </div>

      {error ? <p className="error-banner">{error}</p> : null}

      <div className="status-grid">
        <article className="mini-card">
          <span className="mini-label">App</span>
          <strong>{health?.app || "Not loaded"}</strong>
        </article>
        <article className="mini-card">
          <span className="mini-label">Index</span>
          <strong>{health?.pinecone_index || "Not loaded"}</strong>
        </article>
        <article className="mini-card">
          <span className="mini-label">Default Chunker</span>
          <strong>{health?.default_chunker || "Not loaded"}</strong>
        </article>
        <article className="mini-card">
          <span className="mini-label">Retriever</span>
          <strong>{health?.default_retriever || "Not loaded"}</strong>
        </article>
      </div>

      <div className="chip-section">
        <div>
          <span className="mini-label">Credentials</span>
          <div className="chip-row">
            <span className={`chip ${health?.openai_configured ? "chip-good" : "chip-warn"}`}>
              OpenAI: {health?.openai_configured ? "configured" : "missing"}
            </span>
            <span className={`chip ${health?.pinecone_configured ? "chip-good" : "chip-warn"}`}>
              Pinecone: {health?.pinecone_configured ? "configured" : "missing"}
            </span>
          </div>
        </div>
      </div>

      <div className="chip-section">
        <div>
          <span className="mini-label">Chunkers</span>
          <div className="chip-row">
            {(components?.chunkers || []).map((item) => (
              <span key={item} className="chip">
                {item}
              </span>
            ))}
          </div>
        </div>
        <div>
          <span className="mini-label">Retrievers</span>
          <div className="chip-row">
            {(components?.retrievers || []).map((item) => (
              <span key={item} className="chip">
                {item}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export default StatusStrip;
