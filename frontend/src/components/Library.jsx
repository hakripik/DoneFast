import { useId, useState } from 'react'
import ErrorBanner from './ErrorBanner'

function UploadIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4">
      <path
        d="M12 16V4m0 0 4 4m-4-4-4 4M5 16v3a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-3"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function FileIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5 text-accent">
      <path
        d="M7 3h7l4 4v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z"
        stroke="currentColor"
        strokeWidth="1.5"
      />
      <path d="M14 3v4h4" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  )
}

function TrashIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" className="h-3.5 w-3.5">
      <path
        d="M4 7h16M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2m-8 0 1 12a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1l1-12"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  )
}

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
    <section className="rounded-xl border border-line bg-paper-raised p-5">
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
        className="flex cursor-pointer items-center justify-center gap-2 rounded-lg bg-accent px-4 py-3 text-sm font-medium text-white hover:bg-accent/90 peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-accent"
      >
        <UploadIcon />
        Upload PDFs
      </label>
      <p className="mt-3 text-sm text-ink-muted">
        Upload your slides, notes, or readings to get started.
      </p>

      {pendingFiles.length > 0 && (
        <div className="mt-3">
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
            className="mt-2 w-full rounded-lg bg-ink px-3 py-2 text-sm font-medium text-white disabled:opacity-40"
          >
            {uploading ? 'Uploading…' : `Upload document${pendingFiles.length > 1 ? 's' : ''}`}
          </button>
        </div>
      )}

      {uploadError && (
        <div className="mt-3">
          <ErrorBanner message={uploadError} />
        </div>
      )}

      <div className="mt-5 border-t border-line pt-4">
        <h2 className="font-display text-base font-semibold text-ink">Library</h2>
        <p className="mt-0.5 text-xs text-ink-muted">Uploaded files</p>

        <div className="mt-3">
          {documents.length === 0 ? (
            <p className="rounded-lg border border-dashed border-line px-3 py-6 text-center text-sm text-ink-muted">
              Your library is empty. Add a PDF — lecture slides, textbook chapters, or
              assignment sheets all work.
            </p>
          ) : (
            <ul className="space-y-2">
              {documents.map((doc) => (
                <li
                  key={doc.document_name}
                  className="flex items-start gap-2.5 rounded-lg border border-line px-3 py-2.5"
                >
                  <span className="mt-0.5 shrink-0" aria-hidden="true">
                    <FileIcon />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-ink" title={doc.document_name}>
                      {doc.document_name}
                    </p>
                    <p className="font-mono text-xs text-ink-muted">
                      {doc.total_pages} pages · {doc.total_chunks} chunks
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {documents.length > 0 && (
        <button
          type="button"
          onClick={handleClear}
          disabled={clearing}
          className="mt-4 flex items-center gap-1.5 text-xs font-medium text-red-600 hover:text-red-700 disabled:opacity-40"
        >
          <TrashIcon />
          {clearing ? 'Clearing…' : 'Clear all uploads'}
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
