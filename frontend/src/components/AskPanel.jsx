import { useState } from 'react'
import ErrorBanner from './ErrorBanner'

const EXAMPLES = [
  'Summarize the key points from Lecture 1',
  'Explain the concept of …',
  'What did the reading say about …?',
]

function SendIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4">
      <path
        d="m4 12 16-7-6 16-2.5-6.5L4 12Z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
    </svg>
  )
}

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
    <section className="rounded-xl border border-line bg-paper-raised p-5">
      <h2 className="font-display text-xl font-semibold text-ink">Ask Away!</h2>

      <div className="mt-4 flex items-center gap-2 rounded-full border border-line bg-paper px-4 py-1.5">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask any question about your documents…"
          rows={1}
          className="max-h-32 w-full resize-none bg-transparent py-2 text-sm text-ink placeholder:text-ink-muted focus:outline-none"
        />
        <button
          type="button"
          onClick={submit}
          disabled={!question.trim() || asking}
          aria-label="Ask"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-accent text-white disabled:opacity-40"
        >
          <SendIcon />
        </button>
      </div>

      {!hasDocuments && (
        <p className="mt-2 text-xs text-ink-muted">
          No documents added this session yet. If you've uploaded to this library
          before, it's still searchable — otherwise, add a PDF first.
        </p>
      )}

      <p className="mt-5 text-sm font-medium text-ink">Examples</p>
      <div className="mt-2 flex flex-wrap gap-2">
        {EXAMPLES.map((example) => (
          <button
            key={example}
            type="button"
            onClick={() => setQuestion(example)}
            className="rounded-full border border-line px-3 py-1.5 text-xs text-ink-muted hover:border-accent hover:text-accent"
          >
            {example}
          </button>
        ))}
      </div>

      {asking && <p className="mt-4 text-sm text-ink-muted">Reading your notes…</p>}

      {error && (
        <div className="mt-4">
          <ErrorBanner message={error} />
        </div>
      )}
    </section>
  )
}
