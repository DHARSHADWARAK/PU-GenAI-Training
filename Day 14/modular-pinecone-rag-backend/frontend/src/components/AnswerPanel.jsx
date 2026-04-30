function AnswerPanel({ result, loading }) {
  return (
    <section className="panel answer-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Answer</p>
          <h2>Generated response from the retrieved context.</h2>
        </div>
        {result ? <span className="pill">{result.retriever}</span> : null}
      </div>

      {loading ? <p className="placeholder-copy">Querying the backend and composing an answer...</p> : null}

      {!loading && !result ? (
        <p className="placeholder-copy">
          Run a query after uploading a document and the answer will appear here with the retrieval metadata.
        </p>
      ) : null}

      {result ? (
        <>
          <p className="answer-copy">{result.answer}</p>
          <div className="meta-grid">
            <div>
              <span className="mini-label">Namespace</span>
              <strong>{result.namespace}</strong>
            </div>
            <div>
              <span className="mini-label">Top K</span>
              <strong>{result.top_k}</strong>
            </div>
            <div>
              <span className="mini-label">Retrieved Matches</span>
              <strong>{result.matches.length}</strong>
            </div>
            <div>
              <span className="mini-label">Question</span>
              <strong>{result.question}</strong>
            </div>
          </div>
        </>
      ) : null}
    </section>
  );
}

export default AnswerPanel;
