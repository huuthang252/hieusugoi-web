import { redirect } from "next/navigation";
import { createServerClient } from "@/lib/supabase-server";
import { isEmailConfirmed } from "@/lib/profile";

export const dynamic = "force-dynamic";
const VERSIONS = [
  {
    badge: "Latest Version",
    version: "1.1.0",
    description: "Phiên bản chính thức mới nhất. Yêu cầu đăng nhập tài khoản.",
    buttonText: "Download for Windows",
    url: "https://github.com/huuthang252/hieusugoi-web/releases/download/v1.1.0/Hieusugoi_Setup_v1.1.0.exe",
    buttonClass:
      "inline-block rounded-full bg-cyan-300 px-10 py-4 text-lg font-semibold text-slate-950 shadow-[0_0_30px_rgba(64,233,255,0.4)] transition hover:scale-105 hover:shadow-[0_0_40px_rgba(64,233,255,0.6)]",
    tags: [],
  },
  {
    badge: "beta Version",
    version: "1.2.0",
    description: " Không cần đăng nhập — cài đặt và sử dụng ngay.",
    buttonText: "Download for Windows",
    url: "https://github.com/huuthang252/hieusugoi-web/releases/download/v1.2.0_VN/Hieusugoi_Setup_v1.2.0_VN.exe",
    buttonClass:
      "inline-block rounded-full bg-emerald-400 px-10 py-4 text-lg font-semibold text-slate-950 shadow-[0_0_30px_rgba(52,211,153,0.4)] transition hover:scale-105 hover:shadow-[0_0_40px_rgba(52,211,153,0.6)]",
    tags: [],
  },
];

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
        <h1 className="mb-4 text-5xl font-bold">Download Hieusugoi</h1>

        <p className="mb-16 text-lg text-slate-300">
          Hãy đăng ký tài khoản để có thể tải miễn phí phần mềm Hieusugoi.
        </p>

        <div className="flex flex-col gap-10">
          {VERSIONS.map((v) => (
            <div
              key={v.version}
              className="rounded-2xl border border-white/10 bg-white/5 px-8 py-10 backdrop-blur-sm"
            >
              <p className="mb-1 text-xs font-semibold uppercase tracking-widest text-cyan-400">
                {v.badge}
              </p>

              <p className="mb-2 text-sm text-cyan-300">
                Version: {v.version}
              </p>

              <p className="mb-5 text-sm text-slate-400">{v.description}</p>

              {v.tags.length > 0 && (
                <div className="mb-6 flex flex-wrap justify-center gap-2">
                  {v.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-xs font-medium text-emerald-300"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              <a
                href={v.url}
                target="_blank"
                rel="noopener noreferrer"
                className={v.buttonClass}
              >
                {v.buttonText}
              </a>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
