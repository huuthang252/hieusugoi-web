"use client";
import { useLanguage } from "@/components/LanguageProvider";

export default function HeroSection() {
  const { lang } = useLanguage();

  return (
    <section className="relative min-h-screen overflow-hidden bg-[#07111f] text-white">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(64,233,255,0.18),transparent_30%),radial-gradient(circle_at_80%_10%,rgba(79,140,255,0.16),transparent_32%)]" />

      <div className="relative z-10 mx-auto flex min-h-screen max-w-7xl items-center px-8 py-20">
        <div className="w-full max-w-3xl">
          <h1 className="text-5xl font-bold leading-tight tracking-tight md:text-7xl">
            <span className="bg-gradient-to-r from-cyan-300 to-blue-400 bg-clip-text text-transparent">
              {lang.title}
            </span>
          </h1>

          <p className="mt-6 text-lg leading-8 text-slate-300">
            {lang.desc}
          </p>

          <div className="mt-10 flex flex-wrap gap-4">
            <a
              href="https://www.hieusugoi.com/download"
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-full bg-cyan-300 px-7 py-3 font-semibold text-slate-950 shadow-[0_0_30px_rgba(64,233,255,0.45)] transition hover:scale-105 inline-block"
            >
              Download for Windows
            </a>

            <a
            href="https://www.hieusugoi.com/how-to-use"
            className="rounded-full border border-white/20 bg-white/10 px-7 py-3 font-semibold text-white backdrop-blur transition hover:bg-white/20 inline-block"
          >
            Watch Demo
          </a>
          </div>
        </div>
      </div>
    </section>
  );
}
