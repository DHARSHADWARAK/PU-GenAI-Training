function MatchesPanel({ matches }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Retrieved Chunks</p>
          <h2>Inspect what Pinecone sent back to the answer step.</h2>
        </div>
        <span className="pill">{matches.length} matches</span>
      </div>

      {!matches.length ? (
        <p className="placeholder-copy">Retrieved chunks will appear here after you run a query.</p>
      ) : (
        <div className="match-list">
          {matches.map((match) => (
            <article className="match-card" key={match.id}>
              <div className="match-top">
                <strong>{match.source?.split(/[\\/]/).pop() || "Chunk"}</strong>
                <span className="score-chip">
                  {typeof match.score === "number" ? match.score.toFixed(4) : "n/a"}
                </span>
              </div>
              <p className="muted-line">Chunker: {match.chunker || "unknown"}</p>
              <p className="match-text">{match.text}</p>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export default MatchesPanel;
