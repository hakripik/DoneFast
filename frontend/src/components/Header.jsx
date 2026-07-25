export default function Header() {
  return (
    <header className="border-b border-line bg-paper-raised">
      <div className="mx-auto flex max-w-5xl items-center gap-3 px-4 py-4 sm:px-6">
        <span
          className="flex h-8 w-8 shrink-0 rotate-[-4deg] items-center justify-center rounded-sm border-2 border-accent font-mono text-xs font-bold text-accent"
          aria-hidden="true"
        >
          SA
        </span>
        <div>
          <h1 className="font-display text-xl font-semibold text-ink">Study Assistant</h1>
          <p className="hidden text-xs text-ink-muted sm:block">
            Ask your notes anything. Every answer shows its work.
          </p>
        </div>
      </div>
    </header>
  )
}
