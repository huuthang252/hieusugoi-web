"use client";
import { useEffect, useState } from "react";
import Image from "next/image";

const languages = [
  {
    code: "jp",
    flag: "/flags/jp.svg",
    label: "日本語",
    badge: "AI OCR Translation Overlay",
    sub: "スクリーン上のテキストを検出し、瞬時に翻訳します。",
    title1: "Read Japanese",
    title2: "without leaving",
    title3: "your screen.",
    desc: "Hieusugoiは、画面上の日本語や英語を検出し、瞬時に翻訳。文脈を理解しながら、自然に読み進めることができます。",
    original: "補助金",
    reading: "ほじょきん",
    meaning: "Tiền trợ cấp",
  },
  {
    code: "en",
    flag: "/flags/gb.svg",
    label: "English",
    badge: "AI OCR Translation Overlay",
    sub: "Detect text on your screen and translate instantly.",
    title1: "Read English",
    title2: "without leaving",
    title3: "your screen.",
    desc: "Hieusugoi detects English and Japanese text directly on your screen, translates it instantly, and helps you understand naturally in real context.",
    original: "Subsidy",
    reading: "/ˈsʌb.sə.di/",
    meaning: "Tiền trợ cấp",
  },
  {
    code: "vi",
    flag: "/flags/vn.svg",
    label: "Tiếng Việt",
    badge: "AI OCR Translation Overlay",
    sub: "Hiểu nội dung ngay trên màn hình, không cần copy paste.",
    title1: "Hiểu nội dung",
    title2: "ngay trên",
    title3: "màn hình.",
    desc: "Hieusugoi giúp phát hiện văn bản trên màn hình, dịch nhanh và hỗ trợ học ngoại ngữ trong đúng ngữ cảnh đang đọc.",
    original: "補助金",
    reading: "ほじょきん",
    meaning: "Tiền trợ cấp",
  },
];

export default function HeroSection() {
  const [active, setActive] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setActive((prev) => (prev + 1) % languages.length);
    }, 10000);

    return () => clearInterval(timer);
  }, []);

  const lang = languages[active];

  return (
    <section className="relative min-h-screen overflow-hidden bg-[#07111f] text-white">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(64,233,255,0.18),transparent_30%),radial-gradient(circle_at_80%_10%,rgba(79,140,255,0.16),transparent_32%)]" />

      <div className="relative z-10 mx-auto flex min-h-screen max-w-7xl items-center px-8 py-20">
        <div className="grid w-full grid-cols-1 items-center gap-16 lg:grid-cols-2">
          <div>
            {/* Flag Switcher */}
            <div className="mb-6 inline-flex items-center gap-4 rounded-full border border-cyan-300/30 bg-white/10 px-5 py-3 shadow-[0_0_30px_rgba(64,233,255,0.18)] backdrop-blur-xl">
              {languages.map((item, index) => (
                <button
                  key={item.code}
                  onClick={() => setActive(index)}
                  className={`relative flex h-14 w-14 items-center justify-center rounded-full text-3xl transition-all duration-500 ${
                    active === index
                      ? "scale-110 bg-cyan-300/20 shadow-[0_0_25px_rgba(64,233,255,0.9)] ring-2 ring-cyan-300"
                      : "opacity-55 hover:scale-105 hover:opacity-100"
                  }`}
                >
                  <Image
                    src={item.flag}
                    alt={item.label}
                    width={34}
                    height={34}
                    className="rounded-full object-cover shadow-[0_0_20px_rgba(64,233,255,0.35)]"
                    />
                </button>
              ))}
            </div>

            <div className="mb-4 flex flex-wrap gap-3">
              <div className="rounded-xl border border-cyan-300/25 bg-cyan-300/10 px-5 py-2 text-lg font-semibold text-cyan-100 backdrop-blur">
                {lang.label}
              </div>

              <div className="rounded-full border border-cyan-300/20 bg-white/10 px-5 py-2 text-sm text-cyan-200 backdrop-blur">
                {lang.badge}
              </div>
            </div>

            <p className="mb-6 text-lg text-cyan-300">{lang.sub}</p>

            <h1 className="text-5xl font-bold leading-tight tracking-tight md:text-7xl">
              {lang.title1}
              <span className="block bg-gradient-to-r from-cyan-300 to-blue-400 bg-clip-text text-transparent">
                {lang.title2}
              </span>
              <span className="block bg-gradient-to-r from-cyan-300 to-blue-400 bg-clip-text text-transparent">
                {lang.title3}
              </span>
            </h1>

            <p className="mt-6 max-w-xl text-lg leading-8 text-slate-300">
              {lang.desc}
            </p>

            <div className="mt-10 flex flex-wrap gap-4">
              <button className="rounded-full bg-cyan-300 px-7 py-3 font-semibold text-slate-950 shadow-[0_0_30px_rgba(64,233,255,0.45)] transition hover:scale-105">
                Download for Windows
              </button>

              <button className="rounded-full border border-white/20 bg-white/10 px-7 py-3 font-semibold text-white backdrop-blur transition hover:bg-white/20">
                Watch Demo
              </button>
            </div>
          </div>

          {/* Right demo */}
          <div className="relative">
            <div className="relative overflow-hidden rounded-[32px] border border-white/15 bg-white/10 p-5 shadow-2xl backdrop-blur-xl">
              <div className="rounded-2xl bg-[#f7f7f4] p-8 text-slate-900">
                <div className="mb-6 flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-red-400" />
                  <div className="h-3 w-3 rounded-full bg-yellow-400" />
                  <div className="h-3 w-3 rounded-full bg-green-400" />
                  <div className="ml-6 text-sm text-slate-500">
                    https://www3.nhk.or.jp/news/
                  </div>
                </div>

                <h2 className="mb-6 text-4xl font-bold leading-tight">
                  ガソリン補助 3月は1800億円支出
                </h2>

                <p className="mb-5 text-lg leading-9">
                  政府はガソリン価格の急激な上昇を抑えるため、
                  石油元売り各社に補助金を出しています。
                </p>

                <p className="relative mb-5 text-lg leading-9">
                  中東情勢の緊迫化を受けて、政府は
                  <span className="relative mx-1 rounded bg-yellow-200/80 px-2">
                    {active === 1 ? "Subsidy" : "補助金"}
                    <span className="absolute inset-0 animate-pulse rounded border border-cyan-300" />
                  </span>
                  を継続しています。
                </p>

                <p className="text-lg leading-9">
                  ガソリン価格を抑えるための対策が続いています。
                </p>
              </div>

              <div className="absolute left-14 top-60 h-1 w-[72%] animate-[scan_2.5s_ease-in-out_infinite] rounded-full bg-cyan-300 shadow-[0_0_35px_rgba(64,233,255,1)]" />

              <div className="absolute right-8 top-64 animate-[float_4s_ease-in-out_infinite] rounded-2xl border border-cyan-300/30 bg-slate-950/80 p-5 text-sm text-white shadow-[0_0_45px_rgba(64,233,255,0.45)] backdrop-blur-xl">
                <div className="mb-3 text-cyan-300">Hieusugoi OCR</div>

                <div className="space-y-2">
                  <div>
                    <span className="text-slate-400">Original:</span>{" "}
                    <span className="font-semibold">{lang.original}</span>
                  </div>

                  <div>
                    <span className="text-slate-400">Reading:</span>{" "}
                    <span className="font-semibold">{lang.reading}</span>
                  </div>

                  <div>
                    <span className="text-slate-400">Meaning:</span>{" "}
                    <span className="font-semibold">{lang.meaning}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-center">
              <div className="rounded-full border border-cyan-300/20 bg-white/10 px-5 py-2 text-sm text-cyan-100 backdrop-blur">
                Auto switching language... {lang.label}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}