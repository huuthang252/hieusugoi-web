"use client";

import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";

type Phase = "focus" | "scan" | "translating" | "result";

const targets = [
  {
    word: "安全装置",
    reading: "あんぜんそうち",
    meaning: "Thiết bị an toàn",
    explanation: "Thiết bị dùng để bảo vệ người vận hành và máy móc.",
    pdfY: 0,
    x: 155,
    y: 134,
    w: 92,
    h: 30,
    scrollTop: 30,
  },
  {
    word: "非常停止",
    reading: "ひじょうていし",
    meaning: "Dừng khẩn cấp",
    explanation: "Chức năng dừng máy ngay lập tức khi có nguy hiểm.",
    pdfY: -115,
    x: 470,
    y: 132,
    w: 92,
    h: 30,
    scrollTop: 150,
  },
  {
    word: "作業者",
    reading: "さぎょうしゃ",
    meaning: "Người thao tác / người vận hành",
    explanation: "Người trực tiếp thao tác hoặc làm việc với thiết bị.",
    pdfY: -225,
    x: 170,
    y: 212,
    w: 78,
    h: 30,
    scrollTop: 265,
  },
];

export default function HieusugoiWindow() {
  const [index, setIndex] = useState(0);
  const [phase, setPhase] = useState<Phase>("focus");
  const [shownIndex, setShownIndex] = useState(0);

  const current = targets[index];
  const shown = targets[shownIndex];

  useEffect(() => {
    setPhase("focus");

    const t1 = setTimeout(() => setPhase("scan"), 700);
    const t2 = setTimeout(() => setPhase("translating"), 1500);
    const t3 = setTimeout(() => {
      setShownIndex(index);
      setPhase("result");
    }, 2300);

    const t4 = setTimeout(() => {
      setIndex((prev) => (prev + 1) % targets.length);
    }, 5000);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      clearTimeout(t4);
    };
  }, [index]);

  const toolbarText = useMemo(() => {
    if (phase === "focus") return "テキストを検出中...";
    if (phase === "scan") return "Đang quét OCR...";
    if (phase === "translating") return `Đang dịch: ${current.word}`;
    return `${shown.word}(${shown.reading}) → ${shown.meaning}`;
  }, [phase, current, shown]);

  const popupText = useMemo(() => {
    if (phase === "focus") return "Focus...";
    if (phase === "scan") return "Đang quét OCR...";
    if (phase === "translating") return `Đang dịch: ${current.word}`;
    return `${shown.word} → ${shown.meaning}`;
  }, [phase, current, shown]);

  return (
    <div className="relative w-[1100px] h-[620px]">

      {/* LEFT PANEL */}
      <div className="
        absolute left-0 top-0
        w-[300px] h-[620px]
        rounded-xl border border-[#d0d0d0]
        bg-[#f3f3f3]/95
        overflow-hidden shadow-2xl
        text-[#222]
      ">
        <div className="p-4 pb-2">
          <div className="text-[17px] text-[#333] font-medium">Notes</div>
          <div className="text-[12px] text-[#777] mt-1">Mode: JP → VI</div>
        </div>

        <div className="px-3 pb-3 flex gap-2 border-b border-[#d0d0d0]">
          <div className="h-[30px] flex-1 rounded-md border border-[#d0d0d0] bg-white text-[12px] flex items-center justify-center">
            2026-05-10
          </div>
          <button className="h-[30px] px-3 rounded-md border border-[#d0d0d0] bg-[#f0f0f0] text-[12px]">
            Load history
          </button>
          <button className="h-[30px] px-3 rounded-md border border-[#d0d0d0] bg-[#f0f0f0] text-[12px]">
            Today
          </button>
        </div>

        {/* CURRENT RESULT */}
        <div className="p-3">
          <div className="
            h-[230px]
            rounded-lg border border-[#dcdcdc]
            bg-white p-4
            overflow-y-auto
            text-[16px]
            leading-[1.65]
            font-serif
          ">
            {phase !== "result" ? (
              <div className="text-[#777]">
                {phase === "focus" && "Đang xác định vùng chữ..."}
                {phase === "scan" && "Đang quét OCR..."}
                {phase === "translating" && `Đang xử lý OCR và dịch: ${current.word}`}
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <span className="font-bold">Nội dung gốc:</span>{" "}
                  {shown.word}
                </div>

                <div>
                  <span className="font-bold">Cách đọc:</span>{" "}
                  {shown.reading}
                </div>

                <div>
                  <span className="font-bold">Dịch nghĩa:</span>{" "}
                  {shown.meaning}
                </div>

                <div>
                  <span className="font-bold">Diễn giải:</span>{" "}
                  {shown.explanation}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="px-3 pb-3 flex gap-2">
          <button className="flex-1 h-[30px] rounded-md border border-[#d0d0d0] bg-[#f0f0f0] text-[12px]">
            Clear history
          </button>
          <button className="flex-1 h-[30px] rounded-md border border-[#d0d0d0] bg-[#f0f0f0] text-[12px]">
            Copy current
          </button>
        </div>

        {/* HISTORY */}
        <div className="px-3 pb-3">
          <div className="
            h-[245px]
            rounded-md border border-[#dcdcdc]
            bg-white p-4
            overflow-y-auto
            text-[13px]
            leading-[1.55]
            font-serif
            text-[#444]
          ">
            <div className="mb-4">[12:15:26] “{shown.word}”</div>

            <div className="space-y-3">
              <div>
                <span className="font-bold text-[#222]">Nội dung gốc:</span>{" "}
                {shown.word}
              </div>
              <div>
                <span className="font-bold text-[#222]">Cách đọc:</span>{" "}
                {shown.reading}
              </div>
              <div>
                <span className="font-bold text-[#222]">Dịch nghĩa:</span>{" "}
                {shown.meaning}
              </div>
              <div>
                <span className="font-bold text-[#222]">Diễn giải:</span>{" "}
                {shown.explanation}
              </div>
            </div>

            <div className="mt-4 text-[#999]">━━━━━━━━━━━━━━━━━━━━</div>
          </div>
        </div>
      </div>

      {/* MAIN WINDOW */}
      <div className="
        absolute left-[320px] top-0
        w-[760px] h-[620px]
        rounded-xl border border-white/20
        bg-black/10
        backdrop-blur-[4px]
        overflow-hidden shadow-2xl
      ">
        {/* TOOLBAR */}
        <div className="
          h-[52px]
          flex items-center
          px-4 gap-4
          bg-[#f3f3f3]
          border-b border-[#d0d0d0]
        ">
          <div className="
            w-[34px] h-[28px]
            rounded-md border border-[#d0d0d0]
            bg-[#f0f0f0]
            flex items-center justify-center
          ">
            <div className="space-y-[3px]">
              <div className="w-[14px] h-[1px] bg-[#333]" />
              <div className="w-[14px] h-[1px] bg-[#333]" />
              <div className="w-[14px] h-[1px] bg-[#333]" />
            </div>
          </div>

          <div className="flex-1 text-[13px] text-[#333] font-serif truncate">
            {toolbarText}
          </div>

          <div className="
            w-[36px] h-[28px]
            rounded-md border border-[#d0d0d0]
            bg-[#f0f0f0]
            flex items-center justify-center
            text-[14px]
          ">
            🔊
          </div>

          <div className="w-[36px] h-[28px] flex items-center justify-center text-[#333]">
            —
          </div>

          <div className="w-[36px] h-[28px] flex items-center justify-center text-[#333]">
            ✕
          </div>
        </div>

        {/* CONTENT AREA */}
        <div className="relative w-full h-[calc(100%-52px)] overflow-hidden bg-[#d8d8d8]">

          {/* FAKE PDF */}
          <motion.div
            animate={{ y: current.pdfY }}
            transition={{ duration: 1.4, ease: "easeInOut" }}
            className="
              absolute
              left-[60px]
              top-[34px]
              w-[650px]
              min-h-[980px]
              bg-[#f8f8f3]
              text-[#222]
              shadow-2xl
              px-12
              py-10
              font-serif
            "
          >
            <h2 className="text-[24px] font-bold mb-6">
              安全装置に関する取扱説明書
            </h2>

            <p className="text-[16px] leading-[2.15] mb-7">
              本書は、機械設備に使用される
              <span className="font-bold"> 安全装置 </span>
              の基本的な使用方法と注意事項について説明するものです。
              作業を開始する前に、必ず本書の内容を確認してください。
            </p>

            <p className="text-[16px] leading-[2.15] mb-7">
              装置を使用する際には、周囲の状況を確認し、
              作業者が危険区域に入っていないことを確認してください。
              異常が発生した場合は、速やかに
              <span className="font-bold"> 非常停止 </span>
              ボタンを押してください。
            </p>

            <p className="text-[16px] leading-[2.15] mb-7">
              点検作業は、教育を受けた
              <span className="font-bold"> 作業者 </span>
              が行う必要があります。
              センサーの位置、配線、表示灯の状態を確認し、
              異常がある場合は使用を中止してください。
            </p>

            <p className="text-[16px] leading-[2.15] mb-7">
              安全を確保するためには、定期的な点検と記録が重要です。
              また、機械の動作中に保護カバーを開けたり、
              センサーを無効化したりしないでください。
            </p>

            <p className="text-[16px] leading-[2.15] mb-7">
              本装置は、作業者の安全を補助するためのものであり、
              すべての危険を完全に取り除くものではありません。
              必ず現場の安全ルールに従って使用してください。
            </p>
          </motion.div>

          <div className="absolute inset-0 bg-black/10 pointer-events-none" />

          {/* PDF SCROLLBAR */}
          <div className="absolute right-[60px] top-[34px] w-[8px] h-[500px] rounded-full bg-black/10">
            <motion.div
              animate={{ y: current.scrollTop }}
              transition={{ duration: 1.4, ease: "easeInOut" }}
              className="w-full h-[90px] rounded-full bg-black/35"
            />
          </div>

          {/* OCR YELLOW BOX */}
          <motion.div
            animate={{
              x: current.x,
              y: current.y,
              width: current.w,
              height: current.h,
              opacity: phase === "focus" ? 0.15 : 1,
            }}
            transition={{ duration: 1.0, ease: "easeInOut" }}
            className="
              absolute
              bg-yellow-300/35
              border
              border-yellow-200/70
            "
          />

          {/* QUICK POPUP */}
          <motion.div
            animate={{
              x: current.x,
              y: current.y - 44,
              opacity: phase === "focus" ? 0 : 1,
            }}
            transition={{ duration: 0.8, ease: "easeInOut" }}
            className="
              absolute
              px-4 py-2
              rounded-md
              border border-[#d0c080]
              bg-[#ffffe6]/90
              text-[#222]
              text-[13px]
              shadow-lg
              font-serif
              whitespace-nowrap
            "
          >
            {popupText}
          </motion.div>

          <div className="absolute right-[40px] bottom-[8px] text-[12px] text-gray-500">
            Mode: JP → VI | Drag area | ESC
          </div>

          <div className="
            absolute right-0 bottom-0
            w-[24px] h-[24px]
            bg-black/70
            flex items-center justify-center
            text-white text-[12px]
          ">
            ⇲
          </div>
        </div>
      </div>
    </div>
  );
}