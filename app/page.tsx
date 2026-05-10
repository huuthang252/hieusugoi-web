"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

import HieusugoiWindow from "@/components/HieusugoiWindow";
import DownloadCard from "@/components/DownloadCard";

const pages = ["home", "how", "applications", "download", "about"];

export default function Home() {
  const [pageIndex, setPageIndex] = useState(0);

  const page = pages[pageIndex];

  const goToPage = (index: number) => {
    setPageIndex(index);
  };

  const nextPage = () => {
    setPageIndex((prev) => Math.min(prev + 1, pages.length - 1));
  };

  const prevPage = () => {
    setPageIndex((prev) => Math.max(prev - 1, 0));
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") nextPage();
      if (e.key === "ArrowLeft") prevPage();
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <main className="w-screen h-screen overflow-hidden bg-[#0b1020] text-white relative">

      {/* Background */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,#1e293b,#0b1020_65%)]" />

      {/* Top Menu */}
      <div className="absolute top-6 left-1/2 -translate-x-1/2 z-50">
        <div className="flex items-center gap-8 px-8 py-3 rounded-full border border-white/10 bg-white/10 backdrop-blur-xl shadow-2xl">
          <div className="font-bold text-cyan-300 mr-4">
            Hieusugoi
          </div>

          <MenuButton active={page === "home"} onClick={() => goToPage(0)}>
            Home
          </MenuButton>

          <MenuButton active={page === "how"} onClick={() => goToPage(1)}>
            How To Use
          </MenuButton>

          <MenuButton active={page === "applications"} onClick={() => goToPage(2)}>
            Applications
          </MenuButton>

          <MenuButton active={page === "download"} onClick={() => goToPage(3)}>
            Download
          </MenuButton>

          <MenuButton active={page === "about"} onClick={() => goToPage(4)}>
            About
          </MenuButton>
        </div>
      </div>

      {/* Page Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={page}
          initial={{ opacity: 0, y: 40, filter: "blur(8px)" }}
          animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
          exit={{ opacity: 0, y: -40, filter: "blur(8px)" }}
          transition={{ duration: 0.45 }}
          className="w-full h-full flex items-center justify-center pt-20"
        >
          {page === "home" && <HomePage />}
          {page === "how" && <HowToUsePage />}
          {page === "applications" && <ApplicationsPage />}
          {page === "download" && <DownloadPage />}
          {page === "about" && <AboutPage />}
        </motion.div>
      </AnimatePresence>

      {/* Bottom Navigation */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-4">
        <button
          onClick={prevPage}
          className="px-5 py-2 rounded-full border border-white/10 bg-white/10 backdrop-blur-xl text-white/70 hover:text-cyan-300"
        >
          ← Prev
        </button>

        <div className="text-white/50 text-sm">
          {pageIndex + 1} / {pages.length}
        </div>

        <button
          onClick={nextPage}
          className="px-5 py-2 rounded-full border border-white/10 bg-white/10 backdrop-blur-xl text-white/70 hover:text-cyan-300"
        >
          Next →
        </button>
      </div>

    </main>
  );
}

function MenuButton({
  children,
  active,
  onClick,
}: {
  children: React.ReactNode;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`
        text-sm transition
        ${active ? "text-cyan-300" : "text-white/70 hover:text-white"}
      `}
    >
      {children}
    </button>
  );
}

function HomePage() {
  return (
    <div className="w-full h-full flex items-center justify-center">
      <HieusugoiWindow />
    </div>
  );
}

function HowToUsePage() {
  return (
    <div className="w-[1100px] h-[620px] rounded-3xl border border-white/10 bg-white/10 backdrop-blur-xl shadow-2xl p-14">
      <h1 className="text-5xl font-bold mb-10">
        How To Use
      </h1>

      <div className="grid grid-cols-3 gap-8 h-[420px]">
        <StepCard
          number="01"
          title="Capture Area"
          text="Kéo vùng OCR lên nội dung cần đọc trên màn hình."
        />

        <StepCard
          number="02"
          title="AI Detects Text"
          text="Hieusugoi nhận diện tiếng Nhật hoặc tiếng Anh bằng OCR."
        />

        <StepCard
          number="03"
          title="Translation Appears"
          text="Kết quả dịch, cách đọc và ý nghĩa hiển thị ngay lập tức."
        />
      </div>
    </div>
  );
}

function ApplicationsPage() {
  return (
    <div className="w-[1100px] h-[620px] rounded-3xl border border-white/10 bg-white/10 backdrop-blur-xl shadow-2xl p-14">
      <h1 className="text-5xl font-bold mb-10">
        Applications
      </h1>

      <div className="grid grid-cols-2 gap-6">
        <AppCard title="Foreign Language Learning" text="Học tiếng Nhật và tiếng Anh trực tiếp trên màn hình." />
        <AppCard title="Technical Documents" text="Đọc manual, datasheet, tài liệu kỹ thuật tiếng Nhật." />
        <AppCard title="Manga / Anime / Subtitle" text="Dịch phụ đề, manga, visual novel và nội dung giải trí." />
        <AppCard title="Engineering Research" text="Hỗ trợ nghiên cứu, dịch thuật trong công việc kỹ thuật." />
      </div>
    </div>
  );
}

function DownloadPage() {
  return (
    <div className="w-full h-full flex items-center justify-center">
      <DownloadCard />
    </div>
  );
}

function AboutPage() {
  return (
    <div className="w-[900px] h-[520px] rounded-3xl border border-white/10 bg-white/10 backdrop-blur-xl shadow-2xl p-16 flex flex-col items-center justify-center text-center">
      <h1 className="text-5xl font-bold mb-8">
        About Hieusugoi
      </h1>

      <p className="text-xl text-white/75 leading-relaxed max-w-[680px]">
        Hieusugoi is built by engineers who love AI, languages,
        industrial technology, and futuristic desktop experiences.
      </p>
    </div>
  );
}

function StepCard({
  number,
  title,
  text,
}: {
  number: string;
  title: string;
  text: string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/20 p-8 flex flex-col justify-between">
      <div className="text-cyan-300 text-3xl font-bold">
        {number}
      </div>

      <div>
        <h2 className="text-2xl font-bold mb-4">
          {title}
        </h2>

        <p className="text-white/65 leading-relaxed">
          {text}
        </p>
      </div>
    </div>
  );
}

function AppCard({
  title,
  text,
}: {
  title: string;
  text: string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/20 p-8">
      <h2 className="text-2xl font-bold mb-4 text-cyan-300">
        {title}
      </h2>

      <p className="text-white/70 leading-relaxed">
        {text}
      </p>
    </div>
  );
}