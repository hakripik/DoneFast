import { useState } from 'react'
import ErrorBanner from './ErrorBanner'

export default function AskPanel({ onAsk, asking, error, hasDocuments }) {
  const [question, setQuestion] = useState('')

  const submit = () => {
    if (!question.trim() || asking) return
    onAsk(question.trim())
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <section className="rounded-lg border border-line bg-paper-raised p-5">
      <h2 className="font-display text-lg font-semibold text-ink">Ask</h2>
      <p className="mt-1 text-sm text-ink-muted">
        Answers are grounded in your library, checked against the source, and scored
        before you see them.
      </p>

      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="What do you want to know?"
        rows={3}
        className="mt-4 w-full resize-none rounded border border-line bg-paper px-3 py-2 text-sm text-ink placeholder:text-ink-muted"
      />

      {!hasDocuments && (
        <p className="mt-2 text-xs text-ink-muted">
          No documents added this session yet. If you've uploaded to this library
          before, it's still searchable — otherwise, add a PDF first.
        </p>
      )}

      <button
        type="button"
        onClick={submit}
        disabled={!question.trim() || asking}
        className="mt-3 rounded bg-ink px-4 py-2 text-sm font-medium text-paper-raised disabled:opacity-40"
      >
        {asking ? 'Reading your notes…' : 'Ask'}
      </button>

      {error && (
        <div className="mt-3">
          <ErrorBanner message={error} />
        </div>
      )}
    </section>
  )
}
