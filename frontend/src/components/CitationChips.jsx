const TILTS = [-2, 1.5, -1, 2, -1.5, 1]

/** Citations rendered as small pinned tabs — a nod to the sticky notes this
 * same answer would leave on the exported PDF. */
export default function CitationChips({ citations }) {
  if (citations.length === 0) {
    return (
      <p className="text-sm text-ink-muted italic">
        No citations — the library doesn't appear to cover this.
      </p>
    )
  }

  return (
    <ul className="flex flex-wrap gap-3">
      {citations.map((c, i) => (
        <li
          key={`${c.document_name}-${c.page_number}-${i}`}
          className="relative min-w-36 max-w-56 rounded-sm border border-line bg-paper-raised px-3 py-2 shadow-sm"
          style={{ transform: `rotate(${TILTS[i % TILTS.length]}deg)` }}
        >
          <span
            className="absolute -top-1.5 left-3 h-3 w-3 rounded-full bg-accent"
            aria-hidden="true"
          />
          <p className="truncate text-xs font-medium text-ink" title={c.document_name}>
            {c.document_name}
          </p>
          <p className="font-mono text-sm font-bold text-accent">p. {c.page_number}</p>
          {c.heading && (
            <p className="truncate text-[11px] text-ink-muted italic" title={c.heading}>
              {c.heading}
            </p>
          )}
        </li>
      ))}
    </ul>
  )
}
