/**
 * /api/auth/validate — desktop app token validation endpoint (29B updated).
 *
 * Changes from 29B:
 * - Returns `entitlement` block in every success response.
 * - Expired trial is no longer a hard failure: returns success with
 *   `entitlement.trial_active = false` so the desktop can show "enter your key".
 * - Auto-creates a license row if the user has none (first desktop login).
 *
 * Desktop contract (29A/29B):
 *   { success: true, user, license, entitlement, server_date }
 */

import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import { computeEntitlement, EntitlementInfo, LicenseRow } from "@/lib/entitlement";

const supabaseUrl =
  process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL;

const supabaseAnonKey =
  process.env.SUPABASE_ANON_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

const supabaseServiceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseAnonKey || !supabaseServiceRoleKey) {
  throw new Error(
    "SUPABASE_URL, SUPABASE_ANON_KEY, and SUPABASE_SERVICE_ROLE_KEY must be set."
  );
}

// ── Types ─────────────────────────────────────────────────────────────────────

type AuthUser = {
  id: string;
  email: string;
  user_metadata?: { username?: string };
};

type ApiProfile = {
  id: string;
  user_id: string;
  username: string;
  email: string;
  plan: string;
  status: string;
};

type ApiLicense = LicenseRow & {
  id: string;
  license_key: string;
  max_devices: number;
  created_at: string;
  updated_at: string;
};

type ValidationSuccessResponse = {
  success: true;
  user: {
    id: string;
    username: string;
    email: string;
  };
  license: {
    plan: string;
    status: string;
    trial_end: string | null;
  };
  entitlement: EntitlementInfo;   // 29B: always present in success response
  server_date: string;
};

type ValidationFailureReason =
  | "invalid_token"
  | "no_license"
  | "inactive_account"
  | "banned";
  // Note: "trial_expired" removed in 29B — expired trial now returns success
  // with entitlement.trial_active = false so desktop handles it gracefully.

type ValidationFailureResponse = {
  success: false;
  reason: ValidationFailureReason;
};

type ValidationResponse = ValidationSuccessResponse | ValidationFailureResponse;

// ── Helpers ───────────────────────────────────────────────────────────────────

const getAccessToken = async (request: Request): Promise<string | null> => {
  const authHeader = request.headers.get("authorization");
  if (authHeader?.toLowerCase().startsWith("bearer ")) {
    return authHeader.slice(7).trim();
  }

  const url = new URL(request.url);
  const queryToken = url.searchParams.get("access_token");
  if (queryToken) return queryToken;

  if (request.method === "POST") {
    try {
      const body = (await request.json()) as { access_token?: string };
      return body?.access_token ?? null;
    } catch {
      return null;
    }
  }
  return null;
};

const fetchSupabaseUser = async (accessToken: string): Promise<AuthUser | null> => {
  console.log("DEBUG: Token received, validating with user-scoped Supabase client");

  const userSupabase = createClient(supabaseUrl!, supabaseAnonKey!, {
    global: { headers: { Authorization: `Bearer ${accessToken}` } },
    auth: { persistSession: false, autoRefreshToken: false },
  });

  const { data: { user }, error } = await userSupabase.auth.getUser();

  if (error) {
    console.log("DEBUG: Supabase user validation error:", error.message);
    return null;
  }
  if (!user) {
    console.log("DEBUG: Supabase auth.getUser() returned null user");
    return null;
  }
  console.log("DEBUG: Supabase auth validation success, user ID:", user.id);
  return {
    id: user.id,
    email: user.email || "",
    user_metadata: user.user_metadata as { username?: string } | undefined,
  };
};

/** Fetch a single row from any table via Supabase REST (service role). */
const fetchSingleRecord = async <T>(
  table: string,
  userId: string,
): Promise<T | null> => {
  const url = new URL(`${supabaseUrl}/rest/v1/${table}`);
  url.searchParams.set("select", "*");
  url.searchParams.set("user_id", `eq.${userId}`);
  url.searchParams.set("limit", "1");

  const response = await fetch(url.toString(), {
    headers: {
      Authorization: `Bearer ${supabaseServiceRoleKey}`,
      apikey: supabaseServiceRoleKey!,
      Accept: "application/json",
    },
  });

  if (!response.ok) return null;
  const data = (await response.json()) as T[];
  return Array.isArray(data) && data.length > 0 ? data[0] : null;
};

/**
 * 29B: Auto-create a license record for a user who has none.
 * Uses table defaults: trial_start = NOW(), trial_end = NOW() + 14 days.
 * This is the "first desktop login" path.
 */
const createLicenseForUser = async (userId: string): Promise<ApiLicense | null> => {
  const url = `${supabaseUrl}/rest/v1/licenses`;
  const response = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${supabaseServiceRoleKey}`,
      apikey: supabaseServiceRoleKey!,
      "Content-Type": "application/json",
      "Prefer": "return=representation",
    },
    body: JSON.stringify({ user_id: userId }),
  });

  if (!response.ok) {
    // Handle unique constraint race condition — retry fetch
    if (response.status === 409) {
      return fetchSingleRecord<ApiLicense>("licenses", userId);
    }
    console.error("[Validate] Failed to create license:", await response.text());
    return null;
  }

  const data = await response.json() as ApiLicense[] | ApiLicense;
  if (Array.isArray(data)) return data.length > 0 ? data[0] : null;
  return data ?? null;
};

const createErrorResponse = (reason: ValidationFailureReason) =>
  NextResponse.json({ success: false, reason } as ValidationFailureResponse, {
    status: 401,
  });

// ── Main handler ──────────────────────────────────────────────────────────────

export async function POST(request: Request) {
  return validate(request);
}

export async function GET(request: Request) {
  return validate(request);
}

const validate = async (request: Request): Promise<NextResponse> => {
  console.log("DEBUG: Authorization header exists:", !!request.headers.get("authorization"));

  const accessToken = await getAccessToken(request);
  console.log("DEBUG: Token extraction succeeded:", !!accessToken);
  if (!accessToken) {
    console.log("DEBUG: Validation failed - no token provided");
    return createErrorResponse("invalid_token");
  }

  // ── 1. Verify JWT with Supabase ──────────────────────────────────────────
  const user = await fetchSupabaseUser(accessToken);
  if (!user?.id || !user.email) {
    console.log("DEBUG: Validation failed - invalid token or user not found");
    return createErrorResponse("invalid_token");
  }

  // ── 2. Profile check ─────────────────────────────────────────────────────
  const profile = await fetchSingleRecord<ApiProfile>("profiles", user.id);
  if (!profile) {
    console.log("DEBUG: Validation failed - profile not found for user:", user.id);
    return createErrorResponse("inactive_account");
  }

  if (profile.status === "banned") {
    console.log("DEBUG: Validation failed - user banned:", user.id);
    return createErrorResponse("banned");
  }

  if (profile.status !== "active") {
    console.log("DEBUG: Validation failed - profile not active:", user.id);
    return createErrorResponse("inactive_account");
  }

  // ── 3. License: fetch or auto-create (29B: first-login initialization) ───
  let license = await fetchSingleRecord<ApiLicense>("licenses", user.id);
  if (!license) {
    console.log("[Validate] No license found — auto-creating for user:", user.id);
    license = await createLicenseForUser(user.id);
  }

  if (!license) {
    console.log("DEBUG: Validation failed - could not obtain license for user:", user.id);
    return createErrorResponse("no_license");
  }

  if (license.status === "banned") {
    console.log("DEBUG: Validation failed - license banned for user:", user.id);
    return createErrorResponse("banned");
  }

  if (!["active", "trial"].includes(license.status)) {
    console.log("DEBUG: Validation failed - license not active for user:", user.id);
    return createErrorResponse("inactive_account");
  }

  // ── 4. Compute server-authoritative entitlement (29B) ────────────────────
  // NOTE: trial_expired is no longer a hard failure. An expired trial returns
  // success with entitlement.trial_active = false. The desktop app (29A) then
  // shows "trial expired — enter your personal OpenAI key" and disables AI.
  const entitlement = computeEntitlement(license);

  const serverDate = new Date().toISOString().slice(0, 10);
  console.log(
    `DEBUG: Validation success for user: ${user.id}`
    + ` trial_active=${entitlement.trial_active}`
    + ` days_left=${entitlement.trial_days_left}`
  );

  return NextResponse.json({
    success: true,
    user: {
      id: user.id,
      username: profile.username,
      email: user.email,
    },
    license: {
      plan: license.plan,
      status: license.status,
      trial_end: license.trial_end ?? null,
    },
    entitlement,        // 29B: structured entitlement block for desktop 29A
    server_date: serverDate,
  } satisfies ValidationSuccessResponse);
};
