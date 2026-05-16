"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { createBrowserClient } from "@/lib/supabase-browser";

export default function RegisterPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setMessage(null);

    const supabase = createBrowserClient();
    const redirectUrl = "https://hieusugoi.com/auth/callback";
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          username,
        },
        emailRedirectTo: redirectUrl,
      },
    });

    setLoading(false);

    if (error) {
      setMessage(error.message);
      return;
    }

    if (data.user) {
      setMessage("Account created! Check your email for a confirmation link to activate your account.");
      setTimeout(() => {
        router.push("/login");
      }, 3000);
    }
  };

  return (
    <main className="page-bg page-enter px-8 py-28 text-white">
      <div className="mx-auto max-w-3xl rounded-3xl border border-white/15 bg-white/5 p-10 shadow-[0_0_35px_rgba(64,233,255,0.12)] backdrop-blur-xl">
        <h1 className="mb-4 text-4xl font-bold text-cyan-300">Create your account</h1>
        <p className="mb-8 text-slate-300">Register with email and password to access downloads and account settings.</p>

        <form onSubmit={handleSubmit} className="space-y-6">
          <label className="block space-y-2 text-sm text-slate-100">
            <span>Username</span>
            <input
              type="text"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
              className="w-full rounded-2xl border border-white/15 bg-slate-950/80 px-4 py-3 text-white outline-none transition focus:border-cyan-300"
            />
          </label>

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

          {message && <p className="text-sm text-emerald-300">{message}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-full bg-cyan-300 px-6 py-3 text-lg font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {loading ? "Registering..." : "Register"}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-slate-400">
          Already registered? <Link href="/login" className="text-cyan-300 hover:underline">Sign in</Link>
        </div>
      </div>
    </main>
  );
}
