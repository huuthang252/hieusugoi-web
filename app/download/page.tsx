import { redirect } from "next/navigation";
import { createServerClient } from "@/lib/supabase-server";
import { isEmailConfirmed } from "@/lib/profile";

export const dynamic = "force-dynamic";

const DOWNLOAD_URL = "/api/download?version=2.1.3";

const RELEASE_NOTES = [
  "Kết hợp đồng thời OCR và Mouse Polling để tăng độ ổn định khi nhận diện văn bản",
  "Hệ thống tự động chuyển đổi giữa OCR và Copy mode tùy theo trạng thái màn hình",
  "Giảm độ trễ khi dịch và cải thiện phản hồi khi bôi đen văn bản",
];

const VERSIONS = [
  {
    badge: "Latest Version",
    version: "2.1.3",
    filename: "Hieusugoi_Setup_v2.1.3.exe",
    description:
      "Phiên bản chính thức mới nhất. Yêu cầu đăng nhập tài khoản.",
    buttonText: "Download Hieusugoi v2.1.3",
    url: "https://github.com/huuthang252/hieusugoi-web/releases/download/v2.1.3/Hieusugoi_Setup_v2.1.3.exe",
    buttonClass:
      "inline-block rounded-full bg-cyan-300 px-10 py-4 text-lg font-semibold text-slate-950 shadow-[0_0_30px_rgba(64,233,255,0.4)] transition hover:scale-105 hover:shadow-[0_0_40px_rgba(64,233,255,0.6)]",
    tags: ["Windows 10/11", "64-bit", "AI Translation", "Chat"],
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

              <p className="mb-1 text-2xl font-bold text-white">
                Hieusugoi v{v.version}
              </p>

              <p className="mb-2 text-sm text-slate-400 font-mono">
                {v.filename}
              </p>

              <p className="mb-5 text-sm text-slate-400">{v.description}</p>

              {v.tags.length > 0 && (
                <div className="mb-6 flex flex-wrap justify-center gap-2">
                  {v.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-xs font-medium text-cyan-300"
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

              {/* Release notes — only shown for the latest version entry */}
              {v.version === "2.1.3" && (
                <div className="mt-8 rounded-xl border border-white/10 bg-white/5 px-6 py-5 text-left">
                  <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-400">
                    Có gì mới trong v2.1.3
                  </p>
                  <ul className="space-y-1">
                    {RELEASE_NOTES.map((note) => (
                      <li key={note} className="text-sm text-slate-300">
                        <span className="mr-2 text-cyan-400">✦</span>
                        {note}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
