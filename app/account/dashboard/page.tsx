import { redirect } from "next/navigation";
import { createServerClient } from "@/lib/supabase-server";
import {
  ensureProfileExists,
  ensureLicenseExists,
  getLicense,
  getProfile,
} from "@/lib/profile";
import SignOutButton from "@/components/SignOutButton";

export const dynamic = "force-dynamic";

// ── Helpers ────────────────────────────────────────────────────────────────────

function fmt(n: number | null | undefined): string {
  if (!n) return "0";
  return n.toLocaleString("en-US");
}

function fmtDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-US", {
    year:   "numeric",
    month:  "short",
    day:    "numeric",
    hour:   "2-digit",
    minute: "2-digit",
  });
}

function fmtShortDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-US", {
    year:  "numeric",
    month: "short",
    day:   "numeric",
  });
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default async function DashboardPage() {
  const supabase = createServerClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session?.user) {
    redirect("/login");
  }

  // ── Profile + license (same pattern as /account) ──────────────────────────
  const { profile: ensuredProfile } = await ensureProfileExists(
    supabase,
    session.user.id,
    session.user.email ?? "",
    session.user.user_metadata?.username,
  );
  const { license: ensuredLicense } = await ensureLicenseExists(
    supabase,
    session.user.id,
  );
  const profile  = ensuredProfile  ?? (await getProfile(supabase, session.user.id));
  const license  = ensuredLicense  ?? (await getLicense(supabase, session.user.id));

  const trialEndDate = license?.trial_end
    ? new Date(license.trial_end).toLocaleDateString("en-US", {
        year: "numeric", month: "short", day: "numeric",
      })
    : "N/A";

  // ── Current month key ─────────────────────────────────────────────────────
  const monthKey = new Date().toISOString().slice(0, 7); // "YYYY-MM"

  // ── login_logs — latest login event ──────────────────────────────────────
  const userEmail = session.user.email ?? "";
  const { data: loginRows } = await supabase
    .from("login_logs")
    .select("created_at, app_version, event_type")
    .eq("email", userEmail)
    .in("event_type", ["login_success", "session_resume"])
    .order("created_at", { ascending: false })
    .limit(1);
  const lastLogin = loginRows?.[0] ?? null;

  // ── usage_monthly — current month ─────────────────────────────────────────
  const { data: usageRows } = await supabase
    .from("usage_monthly")
    .select("turns, input_tokens, output_tokens, total_tokens")
    .eq("email", userEmail)
    .eq("month_key", monthKey)
    .limit(1);
  const usage = usageRows?.[0] ?? null;

  // ── download_logs — last 10 ───────────────────────────────────────────────
  const { data: downloads } = await supabase
    .from("download_logs")
    .select("downloaded_at, version, file_name")
    .eq("user_id", session.user.id)
    .order("downloaded_at", { ascending: false })
    .limit(10);

  // ── Derived display values ────────────────────────────────────────────────
  const accountFields: [string, string][] = [
    ["Username",        profile?.username ?? "—"],
    ["Email",           userEmail || "—"],
    ["Plan",            license?.plan ?? profile?.plan ?? "standard"],
    ["Status",          license?.status ?? profile?.status ?? "—"],
    ["License Expiry",  trialEndDate],
  ];

  const usageStats = [
    { label: "Turns",         value: fmt(usage?.turns) },
    { label: "Input Tokens",  value: fmt(usage?.input_tokens) },
    { label: "Output Tokens", value: fmt(usage?.output_tokens) },
    { label: "Total Tokens",  value: fmt(usage?.total_tokens) },
  ];

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <main className="page-bg page-enter min-h-screen px-6 py-28 text-white">
      <div className="mx-auto max-w-5xl space-y-6">

        {/* ── Page header ─────────────────────────────────────────────────── */}
        <div className="text-center">
          <h1 className="text-4xl font-bold text-cyan-300">Account Dashboard</h1>
          <p className="mt-2 text-slate-400">
            {profile?.username ?? userEmail}
          </p>
        </div>

        {/* ── Row 1: Account Info + Login Info ────────────────────────────── */}
        <div className="grid gap-6 md:grid-cols-2">

          {/* Account Information */}
          <section className="rounded-3xl border border-white/15 bg-white/5 p-6 shadow-[0_0_35px_rgba(64,233,255,0.08)] backdrop-blur-xl">
            <h2 className="mb-5 text-xs font-bold uppercase tracking-[0.2em] text-cyan-300">
              Account Information
            </h2>
            <dl className="space-y-4">
              {accountFields.map(([label, value]) => (
                <div key={label}>
                  <dt className="text-xs uppercase tracking-[0.2em] text-cyan-200/70">
                    {label}
                  </dt>
                  <dd className="mt-0.5 text-sm text-slate-300">{value}</dd>
                </div>
              ))}
            </dl>
          </section>

          {/* Login Information */}
          <section className="rounded-3xl border border-white/15 bg-white/5 p-6 shadow-[0_0_35px_rgba(64,233,255,0.08)] backdrop-blur-xl">
            <h2 className="mb-5 text-xs font-bold uppercase tracking-[0.2em] text-cyan-300">
              Login Information
            </h2>
            <dl className="space-y-4">
              <div>
                <dt className="text-xs uppercase tracking-[0.2em] text-cyan-200/70">
                  Last Login
                </dt>
                <dd className="mt-0.5 text-sm text-slate-300">
                  {fmtDate(lastLogin?.created_at)}
                </dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-[0.2em] text-cyan-200/70">
                  Latest Desktop Version
                </dt>
                <dd className="mt-0.5 text-sm text-slate-300">
                  {lastLogin?.app_version ?? "—"}
                </dd>
              </div>
            </dl>
          </section>
        </div>

        {/* ── Monthly Usage ────────────────────────────────────────────────── */}
        <section className="rounded-3xl border border-white/15 bg-white/5 p-6 shadow-[0_0_35px_rgba(64,233,255,0.08)] backdrop-blur-xl">
          <div className="mb-5 flex items-baseline gap-3">
            <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-cyan-300">
              Monthly Usage
            </h2>
            <span className="text-xs text-slate-500">{monthKey}</span>
          </div>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {usageStats.map(({ label, value }) => (
              <div
                key={label}
                className="rounded-2xl border border-white/10 bg-white/5 px-4 py-5 text-center transition-all duration-200 hover:border-cyan-300/20 hover:bg-white/8"
              >
                <p className="text-2xl font-bold tracking-tight text-cyan-300">
                  {value}
                </p>
                <p className="mt-1.5 text-[10px] uppercase tracking-[0.18em] text-slate-400">
                  {label}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* ── Download History ─────────────────────────────────────────────── */}
        <section className="rounded-3xl border border-white/15 bg-white/5 p-6 shadow-[0_0_35px_rgba(64,233,255,0.08)] backdrop-blur-xl">
          <h2 className="mb-5 text-xs font-bold uppercase tracking-[0.2em] text-cyan-300">
            Download History
          </h2>

          {!downloads || downloads.length === 0 ? (
            <p className="text-sm text-slate-500">No downloads recorded yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="pb-3 text-left text-[10px] font-medium uppercase tracking-[0.18em] text-cyan-200/70">
                      Date
                    </th>
                    <th className="pb-3 text-left text-[10px] font-medium uppercase tracking-[0.18em] text-cyan-200/70">
                      Version
                    </th>
                    <th className="pb-3 text-left text-[10px] font-medium uppercase tracking-[0.18em] text-cyan-200/70">
                      File Name
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {downloads.map((dl, i) => (
                    <tr
                      key={i}
                      className="border-b border-white/5 transition-colors last:border-0 hover:bg-white/5"
                    >
                      <td className="py-2.5 pr-4 text-slate-400">
                        {fmtShortDate(dl.downloaded_at)}
                      </td>
                      <td className="py-2.5 pr-4 text-slate-300">
                        {dl.version ?? "—"}
                      </td>
                      <td className="py-2.5 font-mono text-xs text-slate-400">
                        {dl.file_name ?? "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* ── Sign out ─────────────────────────────────────────────────────── */}
        <div className="flex justify-center pt-2 pb-4">
          <SignOutButton />
        </div>

      </div>
    </main>
  );
}
