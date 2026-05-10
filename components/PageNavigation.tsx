"use client";

export default function PageNavigation() {
  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-4">
      <button className="px-5 py-2 rounded-full border border-white/10 bg-white/10 backdrop-blur-xl text-white/70 hover:text-cyan-300">
        ← Prev
      </button>

      <div className="text-white/50 text-sm">
        1 / 5
      </div>

      <button className="px-5 py-2 rounded-full border border-white/10 bg-white/10 backdrop-blur-xl text-white/70 hover:text-cyan-300">
        Next →
      </button>
    </div>
  );
}