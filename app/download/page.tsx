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

  // Verify email is confirmed
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

        <p className="mb-10 text-lg text-slate-300">
          AI OCR Translation Overlay for Windows
        </p>

        <button className="rounded-full bg-cyan-300 px-10 py-4 text-lg font-semibold text-slate-950 shadow-[0_0_30px_rgba(64,233,255,0.4)]">
          Download for Windows
        </button>

      </div>
    </main>
  );
}