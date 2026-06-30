/**
 * entitlement.ts — 29B server-side entitlement computation.
 *
 * The desktop app (29A) reads the structured `entitlement` block from the
 * /api/auth/validate response. This module is the single authoritative source
 * for computing that block from the Supabase `licenses` row.
 *
 * The server always computes trial_active / trial_days_left — the desktop
 * NEVER calculates expiry locally.
 */

export interface EntitlementInfo {
  plan: "trial" | "openai_key";
  trial_active: boolean;
  trial_started_at: string;     // ISO-8601 UTC — display-only on desktop
  trial_ends_at: string;        // ISO-8601 UTC — display-only on desktop
  trial_days_left: number;      // server-computed ceil of days remaining
  requires_user_openai_key: boolean;
  token_source: "system_trial" | "user_openai_key" | "missing_after_trial";
}

export interface LicenseRow {
  id?: string;
  user_id: string;
  plan: string;
  status: string;
  trial_start: string | null;
  trial_end: string | null;
  free_token_enabled?: boolean;  // 29B: admin override (true = system key allowed)
  license_key?: string;
  max_devices?: number;
  created_at?: string;
  updated_at?: string;
}

/**
 * Compute the full entitlement block from a licenses row.
 *
 * Rules (29B Part 3):
 * - status === 'active': paid/upgraded user — no trial, owns personal key
 * - status === 'trial' AND now < trial_end: trial active → system_trial key
 * - status === 'trial' AND now >= trial_end: trial expired → missing_after_trial
 * - free_token_enabled === false: admin-override disables system key even in trial
 */
export function computeEntitlement(license: LicenseRow): EntitlementInfo {
  const now = new Date();

  // Paid / upgraded user — no free trial tokens
  if (license.status === "active") {
    return {
      plan: "openai_key",
      trial_active: false,
      trial_started_at: license.trial_start ?? "",
      trial_ends_at: license.trial_end ?? "",
      trial_days_left: 0,
      requires_user_openai_key: false,   // they have their own arrangement
      token_source: "user_openai_key",
    };
  }

  // Admin has explicitly disabled system token
  const tokenEnabled = license.free_token_enabled !== false;  // default true when not set

  if (!license.trial_end) {
    return {
      plan: "openai_key",
      trial_active: false,
      trial_started_at: license.trial_start ?? "",
      trial_ends_at: "",
      trial_days_left: 0,
      requires_user_openai_key: true,
      token_source: "missing_after_trial",
    };
  }

  const trialEnd = new Date(license.trial_end);
  if (isNaN(trialEnd.getTime())) {
    return {
      plan: "openai_key",
      trial_active: false,
      trial_started_at: license.trial_start ?? "",
      trial_ends_at: license.trial_end,
      trial_days_left: 0,
      requires_user_openai_key: true,
      token_source: "missing_after_trial",
    };
  }

  if (tokenEnabled && now < trialEnd) {
    // Trial active
    const msRemaining = trialEnd.getTime() - now.getTime();
    const daysLeft = Math.ceil(msRemaining / (1000 * 60 * 60 * 24));
    return {
      plan: "trial",
      trial_active: true,
      trial_started_at: license.trial_start ?? "",
      trial_ends_at: license.trial_end,
      trial_days_left: daysLeft,
      requires_user_openai_key: false,
      token_source: "system_trial",
    };
  }

  // Trial expired (or admin-disabled)
  return {
    plan: "openai_key",
    trial_active: false,
    trial_started_at: license.trial_start ?? "",
    trial_ends_at: license.trial_end,
    trial_days_left: 0,
    requires_user_openai_key: true,
    token_source: "missing_after_trial",
  };
}
