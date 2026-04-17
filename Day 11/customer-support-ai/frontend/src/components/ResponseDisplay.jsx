import React from "react";

function ResponseDisplay({ result, loading }) {
  return (
    <article className="panel response-panel">
      <div className="panel-header">
        <h2>Generated response</h2>
        {result ? <span className="scenario-badge">{result.scenario}</span> : null}
      </div>

      {loading ? (
        <p className="placeholder-copy">Generating your reply draft...</p>
      ) : result ? (
        <>
          <p className="response-copy">{result.response}</p>
          <div className="meta-grid">
            <div>
              <span className="meta-label">Top BM25 score</span>
              <strong>{result.top_score}</strong>
            </div>
            <div>
              <span className="meta-label">Model</span>
              <strong>{result.llm_model}</strong>
            </div>
            <div>
              <span className="meta-label">Temperature</span>
              <strong>{result.parameters.temperature}</strong>
            </div>
            <div>
              <span className="meta-label">Max tokens</span>
              <strong>{result.parameters.max_tokens}</strong>
            </div>
          </div>
          {result.used_mock ? (
            <p className="warning-note">{result.llm_error}</p>
          ) : null}
        </>
      ) : (
        <p className="placeholder-copy">
          Submit a complaint to see the generated response and the selected scenario.
        </p>
      )}
    </article>
  );
}

export default ResponseDisplay;
