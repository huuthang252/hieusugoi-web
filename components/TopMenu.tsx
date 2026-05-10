"use client";

export default function TopMenu() {
  return (
    <div className="fixed top-6 left-1/2 -translate-x-1/2 z-50">
      <div className="flex items-center gap-8 px-8 py-3 rounded-full border border-white/10 bg-white/10 backdrop-blur-xl shadow-2xl">
        <div className="font-bold text-cyan-300 mr-4">
          Hieusugoi
        </div>

        <button className="text-sm text-cyan-300">Home</button>
        <button className="text-sm text-white/70 hover:text-white">How To Use</button>
        <button className="text-sm text-white/70 hover:text-white">Applications</button>
        <button className="text-sm text-white/70 hover:text-white">Download</button>
        <button className="text-sm text-white/70 hover:text-white">About</button>
      </div>
    </div>
  );
}