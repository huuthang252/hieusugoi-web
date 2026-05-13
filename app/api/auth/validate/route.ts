import { NextResponse } from "next/server";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseServiceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseServiceRoleKey) {
  throw new Error("NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set.");
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
  const response = await fetch(`${supabaseUrl}/auth/v1/user`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
      apikey: supabaseServiceRoleKey,
      Accept: "application/json",
    },
  });

  console.log("Supabase auth response status:", response.status);

  if (!response.ok) {
    return null;
  }

  const data = (await response.json()) as AuthUser | { message?: string };
  return (data as AuthUser).id ? (data as AuthUser) : null;
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
  console.log("Authorization header exists:", !!request.headers.get("authorization"));
  const accessToken = await getAccessToken(request);
  console.log("Token extraction succeeded:", !!accessToken);
  if (!accessToken) {
    return createErrorResponse("invalid_token");
  }

  const user = await fetchSupabaseUser(accessToken);
  if (!user || !user.id || !user.email) {
    return createErrorResponse("invalid_token");
  }

  const profile = await fetchSingleRecord<ApiProfile>("profiles", user.id, accessToken);
  if (!profile) {
    return createErrorResponse("inactive_account");
  }

  if (profile.status === "banned") {
    return createErrorResponse("banned");
  }

  if (profile.status !== "active") {
    return createErrorResponse("inactive_account");
  }

  const license = await fetchSingleRecord<ApiLicense>("licenses", user.id, accessToken);
  if (!license) {
    return createErrorResponse("no_license");
  }

  if (license.status === "banned") {
    return createErrorResponse("banned");
  }

  if (!["active", "trial"].includes(license.status)) {
    return createErrorResponse("inactive_account");
  }

  if (license.status === "trial") {
    const trialEnd = new Date(license.trial_end || "");
    if (Number.isNaN(trialEnd.getTime()) || trialEnd < new Date()) {
      return createErrorResponse("trial_expired");
    }
  }

  const serverDate = new Date().toISOString().slice(0, 10);

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
