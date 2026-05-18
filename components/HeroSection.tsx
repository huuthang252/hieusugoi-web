"use client";
import { useLanguage } from "@/components/LanguageProvider";

export default function HeroSection() {
  const { lang } = useLanguage();

  return (
    <section
      className="relative min-h-screen w-full overflow-hidden text-white"
      style={{
        backgroundImage: "url('/images/hero-hieusugoi.png')",
        backgroundSize: "cover",
        backgroundPosition: "center right",
        backgroundRepeat: "no-repeat",
      }}
    >
      {/* Overlay tối toàn màn hình — giúp chữ dễ đọc */}
      <div className="absolute inset-0 bg-black/50" />

      {/* Gradient từ trái sang phải — nội dung trái nổi bật, phải hiện ảnh */}
      <div className="absolute inset-0 bg-gradient-to-r from-black/80 via-black/40 to-transparent" />

      {/* Accent glow cyan giữ phong cách SaaS */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_15%_50%,rgba(64,233,255,0.12),transparent_45%)]" />

      {/* Nội dung */}
      <div className="relative z-10 mx-auto flex min-h-screen max-w-7xl items-center px-6 py-20 sm:px-10">
        <div className="w-full max-w-xl">
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
              className="inline-block rounded-full bg-cyan-300 px-7 py-3 font-semibold text-slate-950 shadow-[0_0_30px_rgba(64,233,255,0.45)] transition hover:scale-105"
            >
              Download for Windows
            </a>

            <a
              href="https://www.hieusugoi.com/how-to-use"
              className="inline-block rounded-full border border-white/20 bg-white/10 px-7 py-3 font-semibold text-white backdrop-blur transition hover:bg-white/20"
            >
              Watch Demo
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
