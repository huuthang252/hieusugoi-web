"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useRef, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { createBrowserClient } from "@/lib/supabase-browser";

const menuItems = [
  { label: "Home", href: "/" },
  { label: "How To Use", href: "/how-to-use" },
  { label: "Applications", href: "/applications" },
  { label: "Download", href: "/download" },
  { label: "About", href: "/about" },
];

export default function TopMenu() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const menuButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    let mounted = true;
    const supabase = createBrowserClient();

    supabase.auth.getSession().then(({ data }) => {
      if (!mounted) return;
      setUserEmail(data.session?.user.email ?? null);
    });

    const { data: listener } = supabase.auth.onAuthStateChange((_, session) => {
      if (!mounted) return;
      setUserEmail(session?.user?.email ?? null);
    });

    return () => {
      mounted = false;
      listener.subscription.unsubscribe();
    };
  }, []);

  // Close mobile menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        menuRef.current &&
        !menuRef.current.contains(event.target as Node) &&
        menuButtonRef.current &&
        !menuButtonRef.current.contains(event.target as Node)
      ) {
        setOpen(false);
      }
    };

    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => {
        document.removeEventListener("mousedown", handleClickOutside);
      };
    }
  }, [open]);

  // Close mobile menu on ESC key
  useEffect(() => {
    const handleEscKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };

    if (open) {
      document.addEventListener("keydown", handleEscKey);
      return () => {
        document.removeEventListener("keydown", handleEscKey);
      };
    }
  }, [open]);

  const handleSignOut = async () => {
    const supabase = createBrowserClient();
    await supabase.auth.signOut();
    setUserEmail(null);
    window.location.href = "/";
  };

  const renderAuthButtons = (isMobile = false) => {
    const baseClass = isMobile
      ? "rounded-2xl px-4 py-3 font-semibold transition-all duration-300 text-slate-300 hover:bg-white/10 hover:text-white"
      : "rounded-full px-4 py-2 text-sm font-semibold transition-all duration-300 text-slate-300 hover:text-white hover:bg-white/10";

    if (userEmail) {
      return (
        <>
          <Link
            href="/account"
            onClick={isMobile ? closeMenu : undefined}
            className={baseClass}
          >
            Account
          </Link>
          <button
            onClick={() => {
              handleSignOut();
              if (isMobile) closeMenu();
            }}
            className={`${baseClass} bg-white/5 hover:bg-white/15`}
          >
            Sign out
          </button>
        </>
      );
    }

    return (
      <>
        <Link
          href="/login"
          onClick={isMobile ? closeMenu : undefined}
          className={baseClass}
        >
          Login
        </Link>
        <Link
          href="/register"
          onClick={isMobile ? closeMenu : undefined}
          className={`${baseClass} bg-cyan-300/10 text-cyan-100 hover:bg-cyan-300/20 hover:text-cyan-50`}
        >
          Register
        </Link>
      </>
    );
  };

  const closeMenu = () => setOpen(false);

  return (
    <header className="fixed left-0 top-0 z-50 w-full px-6 pt-4">
      <nav className="mx-auto flex max-w-5xl items-center justify-between rounded-full border border-white/15 bg-white/8 px-6 py-3 text-white shadow-[0_0_35px_rgba(64,233,255,0.12)] backdrop-blur-xl transition-all duration-300">
        <Link
          href="/"
          className="text-xl font-bold text-cyan-300 transition-all duration-300 hover:text-cyan-200 hover:shadow-[0_0_20px_rgba(64,233,255,0.6)]"
        >
          Hieusugoi
        </Link>

        {/* Desktop Menu */}
        <div className="hidden items-center gap-2 md:flex">
          {menuItems.map((item) => {
            const active = pathname === item.href;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`relative rounded-full px-4 py-2 text-sm font-semibold transition-all duration-300 ${
                  active
                    ? "bg-cyan-300/20 text-cyan-200 shadow-[0_0_20px_rgba(64,233,255,0.5)]"
                    : "text-slate-300 hover:text-white hover:bg-white/10"
                }`}
              >
                {item.label}
                {/* Animated underline for active state */}
                {active && (
                  <span className="absolute bottom-0 left-0 h-0.5 w-full rounded-full bg-gradient-to-r from-transparent via-cyan-300 to-transparent" />
                )}
              </Link>
            );
          })}
          {renderAuthButtons()}
        </div>

        {/* Mobile Button */}
        <button
          ref={menuButtonRef}
          onClick={() => setOpen(!open)}
          className={`rounded-full border border-white/15 bg-white/10 px-4 py-2 text-sm font-semibold transition-all duration-300 md:hidden ${
            open
              ? "bg-white/15 text-cyan-300 shadow-[0_0_15px_rgba(64,233,255,0.4)]"
              : "hover:bg-white/15 hover:text-cyan-300"
          }`}
        >
          {open ? "✕" : "☰"}
        </button>
      </nav>

      {/* Mobile Menu */}
      <AnimatePresence>
        {open && (
          <motion.div
            ref={menuRef}
            initial={{ opacity: 0, y: -20, height: 0 }}
            animate={{ opacity: 1, y: 0, height: "auto" }}
            exit={{ opacity: 0, y: -20, height: 0 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="mx-auto mt-3 max-w-5xl overflow-hidden rounded-3xl border border-white/15 bg-white/8 p-4 text-white shadow-2xl backdrop-blur-xl md:hidden"
          >
            <div className="flex flex-col gap-2">
              {menuItems.map((item) => {
                const active = pathname === item.href;

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={closeMenu}
                    className={`relative rounded-2xl px-4 py-3 font-semibold transition-all duration-300 ${
                      active
                        ? "bg-cyan-300/25 text-cyan-200 shadow-[0_0_15px_rgba(64,233,255,0.5)]"
                        : "text-slate-300 hover:bg-white/10 hover:text-white"
                    }`}
                  >
                    {item.label}
                    {/* Animated underline for active state */}
                    {active && (
                      <span className="absolute bottom-1 left-4 h-0.5 w-12 rounded-full bg-gradient-to-r from-cyan-300 to-blue-300" />
                    )}
                  </Link>
                );
              })}
              {renderAuthButtons(true)}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}