"use client";

import Link from "next/link";
import { FormEvent, useEffect, useRef, useState } from "react";
import { createBrowserClient } from "@/lib/supabase-browser";
import {
  inspectRecoveryUrl,
  updateRecoveredPassword,
  validateNewPassword,
} from "@/lib/password-recovery";

type PageState = "checking" | "ready" | "invalid" | "expired" | "success";

export default function ResetPasswordPage() {
  const [pageState, setPageState] = useState<PageState>("checking");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const clientRef = useRef<ReturnType<typeof createBrowserClient> | null>(null);

  useEffect(() => {
    const linkState = inspectRecoveryUrl(window.location.href);
    if (linkState.error) {
      const timer = window.setTimeout(() => setPageState(linkState.error!), 0);
      return () => window.clearTimeout(timer);
    }
    if (!linkState.hasRecoveryIntent) {
      const timer = window.setTimeout(() => setPageState("invalid"), 0);
      return () => window.clearTimeout(timer);
    }

    const supabase = createBrowserClient();
    clientRef.current = supabase;
    let active = true;
    let validated = false;

    const validateSession = async () => {
      const { data: sessionData, error: sessionError } = await supabase.auth.getSession();
      if (!active || sessionError || !sessionData.session) return false;
      const { data: userData, error: userError } = await supabase.auth.getUser();
      if (!active || userError || !userData.user) return false;
      validated = true;
      window.history.replaceState({}, "", "/reset-password");
      setPageState("ready");
      return true;
    };

    const { data: listener } = supabase.auth.onAuthStateChange((event) => {
      if (event === "PASSWORD_RECOVERY") {
        void validateSession();
      }
    });

    void (async () => {
      // Supabase JS consumes implicit recovery fragments automatically. A code
      // may also arrive when the project uses PKCE.
      if (linkState.code) {
        const { error } = await supabase.auth.exchangeCodeForSession(linkState.code);
        if (error && !validated) {
          // Initialization may have exchanged it already; validate that session.
          if (!(await validateSession()) && active) setPageState("invalid");
          return;
        }
      }
      if (!(await validateSession()) && active) setPageState("invalid");
    })();

    return () => {
      active = false;
      listener.subscription.unsubscribe();
    };
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const validationError = validateNewPassword(password, confirmation);
    if (validationError) {
      setMessage(validationError);
      return;
    }
    if (!clientRef.current) {
      setPageState("invalid");
      return;
    }

    setLoading(true);
    setMessage(null);
    try {
      const result = await updateRecoveredPassword(clientRef.current.auth, password);
      if (!result.ok) {
        setMessage(
          "Không thể cập nhật mật khẩu. Liên kết có thể đã hết hạn hoặc đã được sử dụng.",
        );
        return;
      }
      setPassword("");
      setConfirmation("");
      setPageState("success");
    } catch {
      setMessage("Lỗi kết nối. Vui lòng kiểm tra mạng và thử lại.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page-bg page-enter flex min-h-screen items-center px-6 py-28 text-white">
      <section className="mx-auto w-full max-w-xl rounded-3xl border border-white/15 bg-white/5 p-8 shadow-[0_0_35px_rgba(64,233,255,0.12)] backdrop-blur-xl sm:p-10">
        <h1 className="mb-3 text-3xl font-bold text-cyan-300">Đặt lại mật khẩu</h1>

        {pageState === "checking" && (
          <p className="text-slate-300">Đang xác thực liên kết đặt lại mật khẩu…</p>
        )}

        {(pageState === "invalid" || pageState === "expired") && (
          <div className="space-y-5">
            <p className="text-rose-300">
              {pageState === "expired"
                ? "Liên kết đặt lại mật khẩu đã hết hạn. Vui lòng yêu cầu một liên kết mới từ Hieusugoi."
                : "Liên kết đặt lại mật khẩu không hợp lệ hoặc đã được sử dụng."}
            </p>
            <Link href="/login" className="inline-block text-cyan-300 hover:underline">
              Quay lại trang đăng nhập
            </Link>
          </div>
        )}

        {pageState === "ready" && (
          <form onSubmit={handleSubmit} className="mt-7 space-y-5">
            <label className="block space-y-2 text-sm text-slate-100">
              <span>Mật khẩu mới</span>
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="new-password"
                minLength={6}
                required
                className="w-full rounded-2xl border border-white/15 bg-slate-950/80 px-4 py-3 text-white outline-none transition focus:border-cyan-300"
              />
            </label>
            <label className="block space-y-2 text-sm text-slate-100">
              <span>Xác nhận mật khẩu mới</span>
              <input
                type="password"
                value={confirmation}
                onChange={(event) => setConfirmation(event.target.value)}
                autoComplete="new-password"
                minLength={6}
                required
                className="w-full rounded-2xl border border-white/15 bg-slate-950/80 px-4 py-3 text-white outline-none transition focus:border-cyan-300"
              />
            </label>
            {message && <p className="text-sm text-rose-300">{message}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-full bg-cyan-300 px-6 py-3 text-lg font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {loading ? "Đang cập nhật…" : "Cập nhật mật khẩu"}
            </button>
          </form>
        )}

        {pageState === "success" && (
          <div className="mt-6 space-y-4">
            <p className="font-medium text-emerald-300">
              Mật khẩu của bạn đã được cập nhật thành công.
            </p>
            <p className="text-slate-300">
              Bạn có thể quay lại Hieusugoi và đăng nhập bằng mật khẩu mới.
            </p>
          </div>
        )}
      </section>
    </main>
  );
}
