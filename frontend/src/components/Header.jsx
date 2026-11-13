export default function Header() {
  return (
    <header className="bg-accent">
      <div className="mx-auto flex max-w-5xl items-center gap-3 px-4 py-4 sm:px-6">
        <img
          src="/DoneFastLogo.png"
          alt="DoneFast logo"
          className="h-10 w-10 shrink-0 object-contain"
        />
        <div className="min-w-0 flex-1">
          <h1 className="font-display text-xl font-semibold text-white">DoneFast</h1>
          <p className="hidden text-xs text-white/70 sm:block">
            Your Reliable Study Assistant.
          </p>
        </div>
      </div>
    </header>
  )
}
