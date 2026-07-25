import ConfidenceStamp from './ConfidenceStamp'
import CitationChips from './CitationChips'
import ErrorBanner from './ErrorBanner'

export default function ResultPanel({
  question,
  result,
  exportDoc,
  onExportDocChange,
  onExport,
  exporting,
  exportError,
}) {
  const citedDocuments = [...new Set(result.citations.map((c) => c.document_name))]

  return (
    <section className="motion-safe:animate-[fade-in_0.3s_ease-out] rounded-lg border border-line bg-paper-raised p-5">
      <p className="text-xs font-semibold tracking-widest text-ink-muted uppercase">
        Answer
      </p>
      <p className="mt-2 max-w-prose text-base leading-relaxed text-ink">
        {result.answer}
      </p>

      {result.retried && (
        <p className="mt-2 text-xs text-ink-muted italic">
          Needed a second look to find better evidence before answering.
        </p>
      )}

      <div className="mt-6 flex flex-wrap items-start gap-6">
        <ConfidenceStamp score={result.confidence} />

        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold tracking-widest text-ink-muted uppercase">
            Citations
          </p>
          <div className="mt-2">
            <CitationChips citations={result.citations} />
          </div>
        </div>
      </div>

      {result.confidence_breakdown.length > 0 && (
        <details className="mt-4 text-sm text-ink-muted">
          <summary className="cursor-pointer font-medium text-ink">
            Why this score?
          </summary>
          <ul className="mt-2 list-inside list-disc space-y-1">
            {result.confidence_breakdown.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
        </details>
      )}

      {citedDocuments.length > 0 && (
        <div className="mt-6 flex flex-wrap items-center gap-3 border-t border-line pt-4">
          {citedDocuments.length > 1 && (
            <select
              value={exportDoc}
              onChange={(e) => onExportDocChange(e.target.value)}
              className="rounded border border-line bg-paper px-2 py-2 text-sm text-ink"
              aria-label="Document to export"
            >
              {citedDocuments.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          )}
          <button
            type="button"
            onClick={() => onExport(question, result)}
            disabled={!exportDoc || exporting}
            className="rounded border border-ink px-4 py-2 text-sm font-medium text-ink disabled:opacity-40"
          >
            {exporting ? 'Exporting…' : 'Export annotated PDF'}
          </button>
        </div>
      )}

      {exportError && (
        <div className="mt-3">
          <ErrorBanner message={exportError} />
        </div>
      )}
    </section>
  )
}
