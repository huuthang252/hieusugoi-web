import { redirect } from "next/navigation";
import { createServerClient } from "@/lib/supabase-server";
import { ensureProfileExists, ensureLicenseExists, getLicense, getProfile } from "@/lib/profile";
import { computeEntitlement } from "@/lib/entitlement";
import SignOutButton from "@/components/SignOutButton";

export const dynamic = "force-dynamic";

export default async function AccountPage() {
  const supabase = createServerClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session?.user) {
    redirect("/login");
  }

  // Ensure profile exists
  const username = session.user.user_metadata?.username;
  const { profile: ensuredProfile, error: ensureError } = await ensureProfileExists(
    supabase,
    session.user.id,
    session.user.email || "",
    username
  );

  if (ensureError) {
    console.error("[Account] Profile ensure error:", ensureError);
  }

  const { license: ensuredLicense, error: licenseEnsureError } = await ensureLicenseExists(
    supabase,
    session.user.id
  );

  if (licenseEnsureError) {
    console.error("[Account] License ensure error:", licenseEnsureError);
  }

  let profile = ensuredProfile;
  if (!profile) {
    profile = await getProfile(supabase, session.user.id);
  }

  let license = ensuredLicense;
  if (!license) {
    license = await getLicense(supabase, session.user.id);
  }

  const trialEndDate = license?.trial_end
    ? new Date(license.trial_end).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      })
    : "N/A";

  // 29B: server-authoritative entitlement
  const entitlement = license
    ? computeEntitlement({
        user_id: license.user_id,
        plan: license.plan,
        status: license.status,
        trial_start: license.trial_start,
        trial_end: license.trial_end,
      })
    : null;

  return (
    <main className="page-bg page-enter px-8 py-28 text-white">
      <div className="mx-auto max-w-4xl rounded-3xl border border-white/15 bg-white/5 p-10 shadow-[0_0_35px_rgba(64,233,255,0.12)] backdrop-blur-xl text-center">
        <h1 className="mb-4 text-4xl font-bold text-cyan-300">Your account</h1>
        <p className="mb-6 text-lg text-slate-300">
          You are signed in as <strong>{(profile?.username || session.user.email) ?? "your account"}</strong>.
        </p>
        <div className="space-y-4 text-left text-slate-200">
          <div>
            <h2 className="text-sm uppercase tracking-[0.2em] text-cyan-200">Account</h2>
            <p className="mt-2 text-base text-slate-300">Manage your session, download access, and sign out when finished.</p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <h3 className="text-xs uppercase tracking-[0.2em] text-cyan-200">Username</h3>
              <p className="mt-2 text-base text-slate-300">{profile?.username ?? "-"}</p>
            </div>
            <div>
              <h3 className="text-xs uppercase tracking-[0.2em] text-cyan-200">Email</h3>
              <p className="mt-2 text-base text-slate-300">{session.user.email ?? "-"}</p>
            </div>
            <div>
              <h3 className="text-xs uppercase tracking-[0.2em] text-cyan-200">Plan</h3>
              <p className="mt-2 text-base text-slate-300">{license?.plan ?? profile?.plan ?? "standard"}</p>
            </div>
            <div>
              <h3 className="text-xs uppercase tracking-[0.2em] text-cyan-200">License status</h3>
              <p className="mt-2 text-base text-slate-300">{license?.status ?? profile?.status ?? "unknown"}</p>
            </div>
            <div className="sm:col-span-2">
              <h3 className="text-xs uppercase tracking-[0.2em] text-cyan-200">Trial ends</h3>
              <p className="mt-2 text-base text-slate-300">{trialEndDate}</p>
            </div>

            {/* 29B: trial status inline */}
            {entitlement && (
              <div className="sm:col-span-2">
                <h3 className="text-xs uppercase tracking-[0.2em] text-cyan-200">Trial status</h3>
                {entitlement.trial_active ? (
                  <p className="mt-2 text-base text-cyan-200">
                    Active —{" "}
                    <strong>
                      {entitlement.trial_days_left} day{entitlement.trial_days_left !== 1 ? "s" : ""}
                    </strong>{" "}
                    remaining
                  </p>
                ) : (
                  <p className="mt-2 text-base text-amber-300">
                    Expired — enter your OpenAI API key in the desktop app to continue
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
        <SignOutButton />
      </div>
    </main>
  );
}
