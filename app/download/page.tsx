import { redirect } from "next/navigation";
import { createServerClient } from "@/lib/supabase-server";
import { isEmailConfirmed } from "@/lib/profile";

export const dynamic = "force-dynamic";

export default async function DownloadPage() {
  const supabase = createServerClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session?.user) {
    redirect("/login");
  }

  const emailConfirmed = await isEmailConfirmed(session.user);
  if (!emailConfirmed) {
    redirect("/auth/error?message=Please confirm your email to access downloads");
  }

  return (
    <main className="page-bg page-enter px-8 py-28 text-white">
      <div className="mx-auto max-w-4xl text-center">
        <h1 className="mb-6 text-5xl font-bold">
          Download Hieusugoi
        </h1>

        <p className="mb-3 text-lg text-slate-300">
          Hãy đăng ký tài khoản để có thể tải miễn phí phần mềm Hieusugoi.
        </p>

        <p className="mb-1 text-xs font-semibold uppercase tracking-widest text-cyan-400">
          Latest Version
        </p>

        <p className="mb-10 text-sm text-cyan-300">
          Hieusugoi version: 1.1.0
        </p>

        <a
          href="https://github.com/huuthang252/hieusugoi-web/releases/download/v1.1.0/Hieusugoi_Setup_v1.1.0.exe"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block rounded-full bg-cyan-300 px-10 py-4 text-lg font-semibold text-slate-950 shadow-[0_0_30px_rgba(64,233,255,0.4)] transition hover:scale-105 hover:shadow-[0_0_40px_rgba(64,233,255,0.6)]"
        >
          Download for Windows
        </a>
      </div>
    </main>
  );
}