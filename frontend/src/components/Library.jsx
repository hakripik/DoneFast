import { useId, useState } from 'react'
import ErrorBanner from './ErrorBanner'

export default function Library({
  documents,
  onUpload,
  onClear,
  uploading,
  clearing,
  uploadError,
  clearError,
}) {
  const [pendingFiles, setPendingFiles] = useState([])
  const inputId = useId()

  const handleAdd = async () => {
    if (pendingFiles.length === 0) return
    await onUpload(pendingFiles)
    setPendingFiles([])
  }

  const handleClear = () => {
    if (
      window.confirm(
        'Remove every uploaded document and clear the search index? This cannot be undone.'
      )
    ) {
      onClear()
    }
  }

  return (
    <section className="rounded-lg border border-line bg-paper-raised p-5">
      <h2 className="font-display text-lg font-semibold text-ink">Library</h2>
      <p className="mt-1 text-sm text-ink-muted">
        The course material Ask can draw answers from.
      </p>

      <div className="mt-4">
        <input
          id={inputId}
          type="file"
          accept="application/pdf"
          multiple
          className="peer sr-only"
          onChange={(e) => setPendingFiles(Array.from(e.target.files))}
        />
        <label
          htmlFor={inputId}
          className="inline-flex cursor-pointer items-center rounded border border-line bg-paper px-3 py-2 text-sm font-medium text-ink hover:bg-paper-raised peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-ink"
        >
          Choose PDFs
        </label>

        {pendingFiles.length > 0 && (
          <div className="mt-2">
            <ul className="text-sm text-ink-muted">
              {pendingFiles.map((f) => (
                <li key={f.name} className="truncate">
                  {f.name}
                </li>
              ))}
            </ul>
            <button
              type="button"
              onClick={handleAdd}
              disabled={uploading}
              className="mt-2 w-full rounded bg-ink px-3 py-2 text-sm font-medium text-paper-raised disabled:opacity-40"
            >
              {uploading ? 'Uploading…' : `Upload document${pendingFiles.length > 1 ? 's' : ''}`}
            </button>
          </div>
        )}
      </div>

      {uploadError && (
        <div className="mt-3">
          <ErrorBanner message={uploadError} />
        </div>
      )}

      <div className="mt-5">
        {documents.length === 0 ? (
          <p className="rounded border border-dashed border-line px-3 py-6 text-center text-sm text-ink-muted">
            Your library is empty. Add a PDF — lecture slides, textbook chapters, or
            assignment sheets all work.
          </p>
        ) : (
          <ul className="space-y-2">
            {documents.map((doc) => (
              <li
                key={doc.document_name}
                className="rounded border border-line px-3 py-2"
              >
                <p className="truncate text-sm font-medium text-ink" title={doc.document_name}>
                  {doc.document_name}
                </p>
                <p className="font-mono text-xs text-ink-muted">
                  {doc.total_pages} pages · {doc.total_chunks} chunks
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>

      {documents.length > 0 && (
        <button
          type="button"
          onClick={handleClear}
          disabled={clearing}
          className="mt-4 text-xs font-medium text-ink-muted hover:text-accent disabled:opacity-40"
        >
          {clearing ? 'Clearing…' : 'Clear library'}
        </button>
      )}
      {clearError && (
        <div className="mt-2">
          <ErrorBanner message={clearError} />
        </div>
      )}
    </section>
  )
}
