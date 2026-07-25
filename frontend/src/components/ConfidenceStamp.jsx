function tierFor(score) {
  if (score >= 70) return { label: 'Checks out', filled: true }
  if (score >= 40) return { label: 'Partially verified', filled: false }
  if (score > 0) return { label: 'Weak evidence', filled: false }
  return { label: 'Unverified', filled: false }
}

/**
 * The confidence score styled like a marking-pen stamp rather than a progress
 * bar. A passing result (>=70) is a fully-inked, squarely-pressed stamp — it
 * should read as bold, not faded. Below that, the stamp gets progressively
 * fainter and more crookedly angled as the score drops, like a mark made in a
 * hurry with a drying pen. Ink color stays constant (it's a stamp, not a
 * traffic light) — the tier is read from the label and the ink weight, never
 * from hue, so the product keeps a single accent color throughout.
 */
export default function ConfidenceStamp({ score }) {
  const { label, filled } = tierFor(score)
  const rotation = filled ? -2 : -2 - ((70 - score) / 70) * 6
  const opacity = filled ? 1 : 0.55 + (score / 70) * 0.45

  return (
    <div
      className={`inline-flex flex-col items-center justify-center rounded-md border-2 border-accent px-4 py-2 font-mono select-none ${
        filled ? 'bg-accent text-white' : 'text-accent'
      }`}
      style={{ transform: `rotate(${rotation}deg)`, opacity }}
      role="img"
      aria-label={`Confidence ${score} percent — ${label}`}
    >
      <span className="text-2xl font-bold leading-none">{score}%</span>
      <span className="mt-1 text-[10px] font-semibold tracking-widest uppercase">
        {label}
      </span>
    </div>
  )
}
