"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

export type Language = {
  code: "jp" | "en" | "vi";
  flag: string;
  label: string;
  title: string;
  desc: string;
  original: string;
  reading: string;
  meaning: string;
};

const languages: Language[] = [
  {
    code: "vi",
    flag: "/flags/vn.svg",
    label: "Tiếng Việt",
    title: "Đọc ngoại ngữ ngay trên màn hình.",
    desc: "Hieusugoi hiển thị trong suốt chồng trên tài liệu gốc, dịch tức thì và hỗ trợ học ngoại ngữ mà không cần copy paste.",
    original: "補助金",
    reading: "ほじょきん",
    meaning: "Tiền trợ cấp",
  },
  {
    code: "jp",
    flag: "/flags/jp.svg",
    label: "日本語",
    title: "画面を離れずに外国語を読む。",
    desc: "Hieusugoiは透明な画面を資料に重ね、コピー＆ペーストなしでその場で翻訳と学習をサポートします。",
    original: "補助金",
    reading: "ほじょきん",
    meaning: "Tiền trợ cấp",
  },
  {
    code: "en",
    flag: "/flags/gb.svg",
    label: "English",
    title: "Read foreign languages without leaving your screen.",
    desc: "Hieusugoi overlays transparently on your documents, translates instantly, and helps you learn without copy-paste.",
    original: "Subsidy",
    reading: "/ˈsʌb.sə.di/",
    meaning: "Tiền trợ cấp",
  },
];

type LanguageContextValue = {
  activeIndex: number;
  lang: Language;
  languages: Language[];
  dropdownOpen: boolean;
  toggleDropdown: () => void;
  selectLanguage: (index: number) => void;
};

const LanguageContext = createContext<LanguageContextValue | undefined>(
  undefined
);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [isAutoSwitching, setIsAutoSwitching] = useState(true);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (isAutoSwitching) {
      timerRef.current = setInterval(() => {
        setActiveIndex((prev) => (prev + 1) % languages.length);
      }, 15000);
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isAutoSwitching]);

  const selectLanguage = (index: number) => {
    setActiveIndex(index);
    setIsAutoSwitching(false);
    setDropdownOpen(false);
  };

  const toggleDropdown = () => {
    setDropdownOpen((prev) => !prev);
  };

  const value = useMemo(
    () => ({
      activeIndex,
      lang: languages[activeIndex],
      languages,
      dropdownOpen,
      toggleDropdown,
      selectLanguage,
    }),
    [activeIndex, dropdownOpen]
  );

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used within LanguageProvider");
  }
  return context;
}
