function UploadPanel({
  uploadForm,
  onUploadChange,
  onFileChange,
  onUploadSubmit,
  uploading,
  uploadResult,
  uploadError,
  availableChunkers,
}) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Ingestion</p>
          <h2>Upload a document and choose how it gets chunked.</h2>
        </div>
      </div>

      <form className="form-grid" onSubmit={onUploadSubmit}>
        <label className="field-group">
          <span className="field-label">Document</span>
          <span className="field-help">Upload a `.txt`, `.md`, or `.pdf` file for indexing.</span>
          <input className="file-input" type="file" accept=".txt,.md,.pdf" onChange={onFileChange} disabled={uploading} />
        </label>

        <div className="two-up">
          <label className="field-group">
            <span className="field-label">Chunker</span>
            <select
              className="text-input"
              name="chunker"
              value={uploadForm.chunker}
              onChange={onUploadChange}
              disabled={uploading}
            >
              {availableChunkers.map((chunker) => (
                <option key={chunker} value={chunker}>
                  {chunker}
                </option>
              ))}
            </select>
          </label>

          <label className="field-group">
            <span className="field-label">Namespace</span>
            <input
              className="text-input"
              name="namespace"
              value={uploadForm.namespace}
              onChange={onUploadChange}
              disabled={uploading}
            />
          </label>
        </div>

        <div className="three-up">
          <label className="field-group">
            <span className="field-label">Chunk Size</span>
            <input
              className="text-input"
              type="number"
              name="chunkSize"
              value={uploadForm.chunkSize}
              onChange={onUploadChange}
              disabled={uploading}
            />
          </label>

          <label className="field-group">
            <span className="field-label">Overlap</span>
            <input
              className="text-input"
              type="number"
              name="chunkOverlap"
              value={uploadForm.chunkOverlap}
              onChange={onUploadChange}
              disabled={uploading}
            />
          </label>

          <label className="field-group">
            <span className="field-label">Similarity Threshold</span>
            <input
              className="text-input"
              type="number"
              step="0.01"
              min="0"
              max="1"
              name="similarityThreshold"
              value={uploadForm.similarityThreshold}
              onChange={onUploadChange}
              disabled={uploading}
            />
          </label>
        </div>

        <button className="primary-button" type="submit" disabled={uploading}>
          {uploading ? "Indexing..." : "Upload and Index"}
        </button>
      </form>

      {uploadError ? <p className="error-banner">{uploadError}</p> : null}

      {uploadResult ? (
        <div className="result-card success-card">
          <div className="result-topline">
            <strong>{uploadResult.file_name}</strong>
            <span className="pill">{uploadResult.chunker}</span>
          </div>
          <p>
            Indexed <strong>{uploadResult.chunks_indexed}</strong> chunks into namespace{" "}
            <strong>{uploadResult.namespace}</strong>.
          </p>
          <p className="muted-line">Pinecone index: {uploadResult.index_name}</p>
        </div>
      ) : null}
    </section>
  );
}

export default UploadPanel;
