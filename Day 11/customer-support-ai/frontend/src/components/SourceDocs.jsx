import React from "react";

function SourceDocs({ result }) {
  const docs = result?.docs ?? [];

  return (
    <article className="panel docs-panel">
      <div className="panel-header">
        <h2>Retrieved documents</h2>
        <span className="doc-count">{docs.length} docs</span>
      </div>

      {docs.length === 0 ? (
        <p className="placeholder-copy">
          Top BM25 policy matches will appear here after you generate a response.
        </p>
      ) : (
        <div className="doc-list">
          {docs.map((doc) => (
            <section key={`${doc.id}-${doc.title}`} className="doc-card">
              <div className="doc-card-top">
                <h3>{doc.title}</h3>
                <span>{doc.category}</span>
              </div>
              <p>
                <strong>Primary:</strong> {doc.solution}
              </p>
              <p>
                <strong>Alternate:</strong> {doc.alternate_solution}
              </p>
              <p>
                <strong>Standard reply:</strong> {doc.company_response}
              </p>
              <p className="score-pill">BM25 score: {doc.bm25_score}</p>
            </section>
          ))}
        </div>
      )}
    </article>
  );
}

export default SourceDocs;
