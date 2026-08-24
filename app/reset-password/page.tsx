"use client";

import Link from "next/link";
import { FormEvent, useEffect, useRef, useState } from "react";
import { createImplicitRecoveryClient } from "@/lib/supabase-browser";
import {
  inspectRecoveryUrl,
  keepCurrentPassword,
  monitorRecoverySession,
  updateRecoveredPassword,
  validateNewPassword,
} from "@/lib/password-recovery";

type PageState = "checking" | "ready" | "invalid" | "expired" | "success" | "kept";

export default function ResetPasswordPage() {
  const [pageState, setPageState] = useState<PageState>("checking");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [samePassword, setSamePassword] = useState(false);
  const clientRef = useRef<ReturnType<typeof createImplicitRecoveryClient> | null>(null);

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

    const supabase = createImplicitRecoveryClient();
    clientRef.current = supabase;
    let active = true;

    const monitor = monitorRecoverySession(supabase.auth, () => {
      if (!active) return;
      // Supabase has established the session and the Auth server verified its user.
      // Only now remove recovery credentials from the visible URL.
      window.history.replaceState({}, "", "/reset-password");
      setPageState("ready");
    });

    void (async () => {
      // getSession waits for this client's URL/session initialization. Do not
      // reject the link while Supabase is still processing its callback.
      if (!(await monitor.validate()) && active) setPageState("invalid");
    })();

    return () => {
      active = false;
      monitor.stop();
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
      if (result.status === "same_password") {
        setSamePassword(true);
        return;
      }
      if (result.status === "error") {
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

  const handleKeepCurrentPassword = async () => {
    if (!clientRef.current) return;
    setLoading(true);
    setMessage(null);
    try {
      await keepCurrentPassword(clientRef.current.auth);
      setPassword("");
      setConfirmation("");
      setPageState("kept");
    } catch {
      setMessage("Could not finish the recovery session. Please try again.");
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

        {pageState === "ready" && !samePassword && (
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

        {pageState === "ready" && samePassword && (
          <div className="mt-6 space-y-5">
            <h2 className="text-xl font-semibold text-amber-300">Password Already Used</h2>
            <p className="text-slate-300">
              This password is the same as your current password.
            </p>
            {message && <p className="text-sm text-rose-300">{message}</p>}
            <div className="flex flex-col gap-3 sm:flex-row">
              <button
                type="button"
                disabled={loading}
                onClick={handleKeepCurrentPassword}
                className="flex-1 rounded-full border border-cyan-300 px-5 py-3 font-semibold text-cyan-200 transition hover:bg-cyan-300/10 disabled:opacity-70"
              >
                Keep Current Password
              </button>
              <button
                type="button"
                disabled={loading}
                onClick={() => {
                  setPassword("");
                  setConfirmation("");
                  setMessage(null);
                  setSamePassword(false);
                }}
                className="flex-1 rounded-full bg-cyan-300 px-5 py-3 font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:opacity-70"
              >
                Choose Another Password
              </button>
            </div>
          </div>
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

        {pageState === "kept" && (
          <div className="mt-6 space-y-4">
            <p className="font-medium text-emerald-300">
              Your current password has been kept.
            </p>
            <p className="text-slate-300">
              You can return to Hieusugoi and sign in with your existing password.
            </p>
          </div>
        )}
      </section>
    </main>
  );
}
