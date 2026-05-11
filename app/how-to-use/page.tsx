export default function HowToUsePage() {
  return (
    <main className="page-bg page-enter px-8 py-28 text-white">
      <div className="mx-auto max-w-5xl">
        <h1 className="mb-8 text-5xl font-bold">
          How To Use Hieusugoi
        </h1>

        <div className="space-y-8 text-lg text-slate-300">

          <div>
            <h2 className="mb-2 text-2xl font-semibold text-cyan-300">
              1. Launch Hieusugoi
            </h2>

            <p>
              Start the application and place the transparent overlay
              on top of your screen.
            </p>
          </div>

          <div>
            <h2 className="mb-2 text-2xl font-semibold text-cyan-300">
              2. Detect Text
            </h2>

            <p>
              Hover over Japanese or English text to activate OCR.
            </p>
          </div>

          <div>
            <h2 className="mb-2 text-2xl font-semibold text-cyan-300">
              3. Instant Translation
            </h2>

            <p>
              Hieusugoi instantly shows translation, pronunciation,
              and explanation.
            </p>
          </div>

        </div>
      </div>
    </main>
  );
}