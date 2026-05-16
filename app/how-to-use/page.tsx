export default function HowToUsePage() {
  return (
    <main className="page-bg page-enter px-8 py-28 text-white">
      <div className="mx-auto max-w-6xl">

        <h1 className="mb-6 text-center text-7xl font-bold">
          Cách sử dụng Hieusugoi
        </h1>

        <div className="overflow-hidden rounded-3xl border border-white/10 bg-white/5 shadow-2xl backdrop-blur-md">
          <iframe
            className="aspect-video w-full"
            src="https://www.youtube.com/embed/0GJnI7X-I8Y"
            title="How To Use Hieusugoi"
            allowFullScreen
          />
        </div>

      </div>
    </main>
  );
}