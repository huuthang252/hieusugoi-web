import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

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

type ApiLicense = {
  id: string;
  user_id: string;
  plan: string;
  status: string;
  trial_start: string;
  trial_end: string;
  license_key: string;
  max_devices: number;
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
  server_date: string;
};

type ValidationFailureReason =
  | "invalid_token"
  | "no_license"
  | "inactive_account"
  | "banned"
  | "trial_expired";

type ValidationFailureResponse = {
  success: false;
  reason: ValidationFailureReason;
};

type ValidationResponse = ValidationSuccessResponse | ValidationFailureResponse;

const getAccessToken = async (request: Request) => {
  const authHeader = request.headers.get("authorization");
  if (authHeader?.toLowerCase().startsWith("bearer ")) {
    return authHeader.slice(7).trim();
  }

  const url = new URL(request.url);
  const queryToken = url.searchParams.get("access_token");
  if (queryToken) {
    return queryToken;
  }

  if (request.method === "POST") {
    try {
      const body = (await request.json()) as { access_token?: string };
      return body?.access_token;
    } catch {
      return null;
    }
  }

  return null;
};

const fetchSupabaseUser = async (accessToken: string): Promise<AuthUser | null> => {
  console.log("DEBUG: Token received, validating with user-scoped Supabase client");

  const userSupabase = createClient(supabaseUrl, supabaseAnonKey, {
    global: {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    },
    auth: {
      persistSession: false,
      autoRefreshToken: false,
    },
  });

  const {
    data: { user },
    error,
  } = await userSupabase.auth.getUser();

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

const fetchSingleRecord = async <T>(table: string, userId: string, accessToken: string): Promise<T | null> => {
  const url = new URL(`${supabaseUrl}/rest/v1/${table}`);
  url.searchParams.set("select", "*");
  url.searchParams.set("user_id", `eq.${userId}`);
  url.searchParams.set("limit", "1");

  const response = await fetch(url.toString(), {
    headers: {
      Authorization: `Bearer ${supabaseServiceRoleKey}`,
      apikey: supabaseServiceRoleKey,
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    return null;
  }

  const data = (await response.json()) as T[];
  return Array.isArray(data) && data.length > 0 ? data[0] : null;
};

const createErrorResponse = (reason: ValidationFailureReason) =>
  NextResponse.json({ success: false, reason } as ValidationFailureResponse, {
    status: 401,
  });

export async function POST(request: Request) {
  return validate(request);
}

export async function GET(request: Request) {
  return validate(request);
}

const validate = async (request: Request) => {
  console.log("DEBUG: Authorization header exists:", !!request.headers.get("authorization"));
  const accessToken = await getAccessToken(request);
  console.log("DEBUG: Token extraction succeeded:", !!accessToken);
  if (!accessToken) {
    console.log("DEBUG: Validation failed - no token provided");
    return createErrorResponse("invalid_token");
  }

  const user = await fetchSupabaseUser(accessToken);
  if (!user || !user.id || !user.email) {
    console.log("DEBUG: Validation failed - invalid token or user not found");
    return createErrorResponse("invalid_token");
  }

  const profile = await fetchSingleRecord<ApiProfile>("profiles", user.id, accessToken);
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

  const license = await fetchSingleRecord<ApiLicense>("licenses", user.id, accessToken);
  if (!license) {
    console.log("DEBUG: Validation failed - no license for user:", user.id);
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

  if (license.status === "trial") {
    const trialEnd = new Date(license.trial_end || "");
    if (Number.isNaN(trialEnd.getTime()) || trialEnd < new Date()) {
      console.log("DEBUG: Validation failed - trial expired for user:", user.id);
      return createErrorResponse("trial_expired");
    }
  }

  const serverDate = new Date().toISOString().slice(0, 10);
  console.log("DEBUG: Validation success for user:", user.id);

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
      trial_end: license.trial_end || null,
    },
    server_date: serverDate,
  } as ValidationSuccessResponse);
};
