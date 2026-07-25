import { explainError } from '../lib/api'

/** A plain-language error box: what happened, and — when we know it — what to do next. */
export default function ErrorBanner({ message }) {
  if (!message) return null
  const { summary, detail } = explainError(message)

  return (
    <div
      role="alert"
      className="border-l-4 border-accent bg-accent-soft text-ink rounded-r px-4 py-3 text-sm"
    >
      <p className="font-medium">{summary}</p>
      {detail && <p className="mt-1 text-ink-muted">{detail}</p>}
    </div>
  )
}
