function QueryPanel({
  queryForm,
  onQueryChange,
  onQuerySubmit,
  querying,
  queryError,
  availableRetrievers,
}) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Retrieval</p>
          <h2>Ask questions against your indexed namespace.</h2>
        </div>
      </div>

      <form className="form-grid" onSubmit={onQuerySubmit}>
        <label className="field-group">
          <span className="field-label">Question</span>
          <textarea
            className="query-input"
            name="question"
            value={queryForm.question}
            onChange={onQueryChange}
            disabled={querying}
          />
        </label>

        <div className="three-up">
          <label className="field-group">
            <span className="field-label">Namespace</span>
            <input
              className="text-input"
              name="namespace"
              value={queryForm.namespace}
              onChange={onQueryChange}
              disabled={querying}
            />
          </label>

          <label className="field-group">
            <span className="field-label">Retriever</span>
            <select
              className="text-input"
              name="retriever"
              value={queryForm.retriever}
              onChange={onQueryChange}
              disabled={querying}
            >
              {availableRetrievers.map((retriever) => (
                <option key={retriever} value={retriever}>
                  {retriever}
                </option>
              ))}
            </select>
          </label>

          <label className="field-group">
            <span className="field-label">Top K</span>
            <input
              className="text-input"
              type="number"
              name="topK"
              value={queryForm.topK}
              onChange={onQueryChange}
              disabled={querying}
            />
          </label>
        </div>

        <button className="primary-button secondary-glow" type="submit" disabled={querying}>
          {querying ? "Searching..." : "Run Query"}
        </button>
      </form>

      {queryError ? <p className="error-banner">{queryError}</p> : null}
    </section>
  );
}

export default QueryPanel;
