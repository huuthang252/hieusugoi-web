export default function ApplicationsPage() {
  return (
    <main className="page-bg page-enter px-8 py-28 text-white">
      <div className="mx-auto max-w-6xl">
        <h1 className="mb-12 text-5xl font-bold">
          Applications
        </h1>

        <div className="grid gap-8 md:grid-cols-2">

          <div className="rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur">
            <h2 className="mb-4 text-2xl font-semibold text-cyan-300">
              Japanese News
            </h2>

            <p className="text-slate-300">
              Read NHK and Japanese websites naturally without
              copy-paste translation.
            </p>
          </div>

          <div className="rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur">
            <h2 className="mb-4 text-2xl font-semibold text-cyan-300">
              Technical Documents
            </h2>

            <p className="text-slate-300">
              Understand industrial manuals and PDF documents directly
              on screen.
            </p>
          </div>

        </div>
      </div>
    </main>
  );
}