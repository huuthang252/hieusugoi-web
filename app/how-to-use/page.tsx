"use client";

import { useState } from "react";

const videos = [
  {
    title: "Tải và Cài Đặt",
    url: "https://www.youtube.com/embed/BxKOZlo2dbs",
  },
  {
    title: "Cách thiết lập",
    url: "https://www.youtube.com/embed/0GJnI7X-I8Y",
  },
  {
    title: "Cách sử dụng",
    url: "https://www.youtube.com/embed/0GJnI7X-I8Y",
  },
  {
    title: "Lưu ý",
    url: "https://www.youtube.com/embed/0GJnI7X-I8Y",
  },
];

export default function HowToUsePage() {
  const [selectedVideo, setSelectedVideo] = useState(videos[0]);

  return (
    <main className="page-bg page-enter px-8 py-28 text-white">
      <div className="mx-auto max-w-7xl">

        <h3 className="mb-8 text-center text-4xl font-bold">
          Cách sử dụng Hieusugoi
        </h3>

        <div className="grid gap-6 lg:grid-cols-[280px_1fr]">

          {/* Left Menu */}
          <aside className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-2xl backdrop-blur-md">

            <h4 className="mb-5 text-xl font-bold text-cyan-300">
              Video hướng dẫn
            </h4>

            <div className="space-y-3">

              {videos.map((video) => (
                <button
                  key={video.title}
                  onClick={() => setSelectedVideo(video)}
                  className={`w-full rounded-2xl px-4 py-4 text-left text-base font-semibold transition-all duration-200 ${
                    selectedVideo.title === video.title
                      ? "border border-cyan-300 bg-cyan-400/20 text-cyan-200"
                      : "border border-white/5 bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white"
                  }`}
                >
                  {video.title}
                </button>
              ))}

            </div>
          </aside>

          {/* Video Area */}
          <section className="overflow-hidden rounded-3xl border border-white/10 bg-white/5 shadow-2xl backdrop-blur-md">

            <iframe
              className="aspect-video w-full"
              src={selectedVideo.url}
              title={selectedVideo.title}
              allowFullScreen
            />

          </section>

        </div>
      </div>
    </main>
  );
}