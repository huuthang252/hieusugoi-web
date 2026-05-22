"use client";

import { motion } from "framer-motion";

const DOWNLOAD_URL =
  "https://github.com/huuthang252/hieusugoi-web/releases/download/v2.1.1/Hieusugoi_Setup_v2.1.1.exe";

export default function DownloadCard() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="
        w-[720px]
        h-[500px]
        rounded-3xl
        border
        border-white/10
        bg-white/10
        backdrop-blur-xl
        shadow-2xl
        flex
        flex-col
        items-center
        justify-center
        text-center
        p-16
      "
    >
      {/* TITLE */}
      <div className="text-5xl font-bold mb-6">Hieusugoi</div>

      {/* VERSION */}
      <div className="text-cyan-300 text-2xl mb-2">Version 2.1.1</div>
      <div className="text-cyan-200 text-sm mb-10">
        Latest version: v2.1.1
      </div>

      {/* PLATFORM */}
      <div className="text-white/70 text-lg mb-12 leading-relaxed">
        Windows 10 / 11
        <br />
        64-bit Desktop Application
      </div>

      {/* DOWNLOAD BUTTON */}
      <motion.a
        href={DOWNLOAD_URL}
        target="_blank"
        rel="noopener noreferrer"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.98 }}
        className="
          px-10
          py-5
          rounded-2xl
          bg-cyan-400
          text-black
          font-bold
          text-lg
          shadow-xl
        "
      >
        Download Hieusugoi v2.1.1
      </motion.a>

      {/* FEATURES */}
      <div className="
        mt-14
        grid
        grid-cols-2
        gap-x-10
        gap-y-4
        text-white/60
        text-sm
      ">
        <div>• AI Translation</div>
        <div>• Chat với Hieusugoi</div>
        <div>• AI Voice (TTS)</div>
        <div>• Notes Workspace</div>
        <div>• Hiragana Reading</div>
        <div>• Local Cache</div>
      </div>
    </motion.div>
  );
}