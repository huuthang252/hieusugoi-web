"use client";

import Link from "next/link";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

function AuthErrorContent() {
  const searchParams = useSearchParams();
  const message = searchParams.get("message") || "An error occurred during authentication.";

  return (
    <>
      <h1 className="mb-4 text-4xl font-bold text-rose-300">Authentication Error</h1>
      <p className="mb-8 text-slate-300">{message}</p>

      <div className="space-y-4">
        <Link
          href="/login"
          className="inline-block rounded-full bg-cyan-300 px-6 py-3 text-lg font-semibold text-slate-950 transition hover:bg-cyan-200"
        >
          Try signing in again
        </Link>
        <p className="mt-4 text-sm text-slate-400">
          If the problem persists, please contact support or{" "}
          <Link href="/" className="text-cyan-300 hover:underline">
            return to home
          </Link>
          .
        </p>
      </div>
    </>
  );
}

export default function AuthErrorPage() {
  return (
    <main className="page-bg page-enter px-8 py-28 text-white">
      <div className="mx-auto max-w-3xl rounded-3xl border border-white/15 bg-white/5 p-10 shadow-[0_0_35px_rgba(64,233,255,0.12)] backdrop-blur-xl">
        <Suspense
          fallback={
            <>
              <h1 className="mb-4 text-4xl font-bold text-rose-300">Authentication Error</h1>
              <p className="mb-8 text-slate-300">Loading error details...</p>
            </>
          }
        >
          <AuthErrorContent />
        </Suspense>
      </div>
    </main>
  );
}
