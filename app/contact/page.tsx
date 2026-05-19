"use client";

import { useState } from "react";

type FormState = {
  name: string;
  email: string;
  subject: string;
  message: string;
};

type Status = "idle" | "loading" | "success" | "error";

export default function ContactPage() {
  const [form, setForm] = useState<FormState>({
    name: "",
    email: "",
    subject: "",
    message: "",
  });
  const [status, setStatus] = useState<Status>("idle");
  const [errorMsg, setErrorMsg] = useState("");

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("loading");
    setErrorMsg("");

    try {
      const res = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      if (res.ok) {
        setStatus("success");
        setForm({ name: "", email: "", subject: "", message: "" });
      } else {
        const data = await res.json().catch(() => ({}));
        setErrorMsg(data.error || "Gửi thất bại. Vui lòng thử lại.");
        setStatus("error");
      }
    } catch {
      setErrorMsg("Lỗi kết nối. Vui lòng thử lại.");
      setStatus("error");
    }
  };

  const inputClass =
    "w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder-slate-500 outline-none backdrop-blur-sm transition focus:border-cyan-400/60 focus:ring-1 focus:ring-cyan-400/40";

  return (
    <main className="page-bg page-enter px-6 py-28 text-white">
      <div className="mx-auto max-w-2xl">

        {/* Header */}
        <div className="mb-12 text-center">
          <h1 className="mb-3 text-5xl font-bold">Contact Hieusugoi</h1>
          <p className="text-slate-400">
            Có câu hỏi hoặc muốn hợp tác? Hãy liên hệ với chúng tôi.
          </p>
        </div>

        {/* Contact info card */}
        <div className="mb-8 rounded-2xl border border-white/10 bg-white/5 px-6 py-5 backdrop-blur-sm">
          <p className="text-xs font-semibold uppercase tracking-widest text-cyan-400 mb-2">
            Thông tin liên hệ
          </p>
          <p className="text-sm text-slate-300">
            Email:{" "}
            <a
              href="mailto:huuthang252@gmail.com"
              className="text-cyan-300 transition hover:text-cyan-200"
            >
              huuthang252@gmail.com
            </a>
          </p>
        </div>

        {/* Form card */}
        <div className="rounded-2xl border border-white/10 bg-white/5 px-8 py-10 backdrop-blur-sm">
          <p className="mb-6 text-xs font-semibold uppercase tracking-widest text-cyan-400">
            Gửi liên hệ
          </p>

          {status === "success" ? (
            <div className="rounded-xl border border-emerald-400/30 bg-emerald-400/10 px-6 py-8 text-center">
              <p className="text-lg font-semibold text-emerald-300">
                ✓ Gửi thành công!
              </p>
              <p className="mt-2 text-sm text-slate-400">
                Chúng tôi sẽ phản hồi sớm nhất có thể.
              </p>
              <button
                onClick={() => setStatus("idle")}
                className="mt-6 text-sm text-cyan-400 underline transition hover:text-cyan-300"
              >
                Gửi tin nhắn khác
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-xs text-slate-400">
                    Họ tên *
                  </label>
                  <input
                    type="text"
                    name="name"
                    value={form.name}
                    onChange={handleChange}
                    placeholder="Nguyễn Văn A"
                    required
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className="mb-1.5 block text-xs text-slate-400">
                    Email *
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={form.email}
                    onChange={handleChange}
                    placeholder="email@example.com"
                    required
                    className={inputClass}
                  />
                </div>
              </div>

              <div>
                <label className="mb-1.5 block text-xs text-slate-400">
                  Tiêu đề *
                </label>
                <input
                  type="text"
                  name="subject"
                  value={form.subject}
                  onChange={handleChange}
                  placeholder="Chủ đề bạn muốn trao đổi"
                  required
                  className={inputClass}
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs text-slate-400">
                  Nội dung *
                </label>
                <textarea
                  name="message"
                  value={form.message}
                  onChange={handleChange}
                  placeholder="Nội dung cần trao đổi..."
                  required
                  rows={5}
                  className={`${inputClass} resize-none`}
                />
              </div>

              {status === "error" && (
                <p className="rounded-lg border border-red-400/30 bg-red-400/10 px-4 py-2 text-sm text-red-300">
                  {errorMsg}
                </p>
              )}

              <button
                type="submit"
                disabled={status === "loading"}
                className="mt-2 inline-block rounded-full bg-cyan-300 px-10 py-4 text-lg font-semibold text-slate-950 shadow-[0_0_30px_rgba(64,233,255,0.4)] transition hover:scale-105 hover:shadow-[0_0_40px_rgba(64,233,255,0.6)] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {status === "loading" ? "Đang gửi…" : "Gửi liên hệ"}
              </button>
            </form>
          )}
        </div>
      </div>
    </main>
  );
}
