"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { createBrowserClient } from "@/lib/supabase-browser";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setMessage(null);

    const supabase = createBrowserClient();
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    setLoading(false);

    if (error) {
      setMessage(error.message);
      return;
    }

    // Check if email is confirmed
    if (data.user && !data.user.email_confirmed_at) {
      setMessage("Please confirm your email before accessing your account. Check your inbox for a confirmation link.");
      return;
    }

    router.push("/account");
  };

  return (
    <main className="page-bg page-enter px-8 py-28 text-white">
      <div className="mx-auto max-w-3xl rounded-3xl border border-white/15 bg-white/5 p-10 shadow-[0_0_35px_rgba(64,233,255,0.12)] backdrop-blur-xl">
        <h1 className="mb-4 text-4xl font-bold text-cyan-300">Chào mừng bạn đã tới Hieusugoi</h1>
        <p className="mb-8 text-slate-300">Hãy đăng ký tài khoản để có thể tải bản mới nhất của hieusugoi.</p>

        <form onSubmit={handleSubmit} className="space-y-6">
          <label className="block space-y-2 text-sm text-slate-100">
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              className="w-full rounded-2xl border border-white/15 bg-slate-950/80 px-4 py-3 text-white outline-none transition focus:border-cyan-300"
            />
          </label>

          <label className="block space-y-2 text-sm text-slate-100">
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
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
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-slate-400">
          Don&apos;t have an account? <Link href="/register" className="text-cyan-300 hover:underline">Register</Link>
        </div>
      </div>
    </main>
  );
}
