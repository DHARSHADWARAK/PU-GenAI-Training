import React, { useState } from "react";
import { generateSupportResponse } from "./api/client";
import ComplaintInput from "./components/ComplaintInput";
import ModeSelector from "./components/ModeSelector";
import ResponseDisplay from "./components/ResponseDisplay";
import SourceDocs from "./components/SourceDocs";

const INITIAL_COMPLAINT =
  "My product arrived late and damaged. Can I get a refund?";

function App() {
  const [complaint, setComplaint] = useState(INITIAL_COMPLAINT);
  const [mode, setMode] = useState("strict");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const data = await generateSupportResponse({ complaint, mode });
      setResult(data);
    } catch (err) {
      setError(err.message || "Failed to generate a response.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-shell">
      <main className="app-shell">
        <section className="hero-card">
          <p className="eyebrow">AI-Assisted Customer Support Response Generator</p>
          <h1>Draft policy-aware replies for repetitive customer complaints.</h1>
          <p className="hero-copy">
            This app retrieves the top local policy matches with BM25 and then
            drafts a response in strict or friendly mode.
          </p>
        </section>

        <section className="panel">
          <form onSubmit={handleSubmit} className="form-grid">
            <ComplaintInput value={complaint} onChange={setComplaint} disabled={loading} />
            <ModeSelector value={mode} onChange={setMode} disabled={loading} />
            <button className="submit-button" type="submit" disabled={loading}>
              {loading ? "Generating..." : "Generate Response"}
            </button>
          </form>
          {error ? <p className="error-banner">{error}</p> : null}
        </section>

        <section className="results-grid">
          <ResponseDisplay result={result} loading={loading} />
          <SourceDocs result={result} />
        </section>
      </main>
    </div>
  );
}

export default App;
