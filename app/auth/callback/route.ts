import { NextRequest, NextResponse } from "next/server";
import { createServerClient } from "@/lib/supabase-server";
import { ensureProfileExists, ensureLicenseExists } from "@/lib/profile";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const code = searchParams.get("code");
  const accessToken = searchParams.get("access_token");
  const refreshToken = searchParams.get("refresh_token");
  const next = searchParams.get("next") || "/account";

  if (!code && !accessToken) {
    console.error("[Callback] No authorization code or access token received");
    return NextResponse.redirect(
      new URL("/auth/error?message=No authorization code received", request.url)
    );
  }

  try {
    const supabase = createServerClient();

    let freshUser = null;

    if (code) {
      // Step 1: Exchange code for session
      console.log("[Callback] Exchanging code for session...");
      const { error: exchangeError, data } = await supabase.auth.exchangeCodeForSession(code);

      if (exchangeError) {
        console.error("[Callback] Exchange error:", exchangeError);
        return NextResponse.redirect(
          new URL(
            `/auth/error?message=${encodeURIComponent(exchangeError.message)}`,
            request.url
          )
        );
      }

      console.log("[Callback] Code exchange successful");
      freshUser = data?.session?.user || null;
    } else if (accessToken) {
      // Step 1b: Some confirmation callbacks return direct tokens
      console.log("[Callback] Setting session from access token...");
      const { data, error: setSessionError } = await supabase.auth.setSession({
        access_token: accessToken,
        refresh_token: refreshToken || "",
      });

      if (setSessionError) {
        console.error("[Callback] Set session error:", setSessionError);
        return NextResponse.redirect(
          new URL(
            `/auth/error?message=${encodeURIComponent(setSessionError.message)}`,
            request.url
          )
        );
      }

      console.log("[Callback] Session set from token successfully");
      freshUser = data?.session?.user || null;
    }

    if (!freshUser) {
      // Fallback: read user from the newly established session
      const {
        data: { user: fallbackUser },
        error: userError,
      } = await supabase.auth.getUser();

      if (userError) {
        console.error("[Callback] Fallback getUser error:", userError);
      }

      freshUser = fallbackUser || null;
    }

    if (!freshUser) {
      console.error("[Callback] Failed to retrieve user after session exchange");
      return NextResponse.redirect(
        new URL(
          `/auth/error?message=${encodeURIComponent("Failed to retrieve user information")}`,
          request.url
        )
      );
    }

    console.log(`[Callback] User retrieved: ${freshUser.id}, email: ${freshUser.email}, confirmed: ${!!freshUser.email_confirmed_at}`);

    // Step 2: Create profile if it doesn't exist
    const username = freshUser.user_metadata?.username;
    const email = freshUser.email || "";

    console.log(`[Callback] Ensuring profile for user_id: ${freshUser.id}, username: ${username}, email: ${email}`);
    const { profile, error: profileError } = await ensureProfileExists(
      supabase,
      freshUser.id,
      email,
      username
    );

    if (profileError) {
      console.error(`[Callback] Profile creation error: ${profileError}`);
    }

    if (profile) {
      console.log(`[Callback] Profile created/verified: ${profile.user_id}`);

      const { license, error: licenseError } = await ensureLicenseExists(
        supabase,
        freshUser.id
      );

      if (licenseError) {
        console.error(`[Callback] License creation error: ${licenseError}`);
      }

      if (license) {
        console.log(`[Callback] License created/verified for user: ${license.user_id}`);
      }
    }

    // Step 3: Redirect to next page
    console.log(`[Callback] Redirecting to: ${next}`);
    return NextResponse.redirect(new URL(next, request.url));
  } catch (error) {
    console.error("[Callback] Unexpected error:", error);
    return NextResponse.redirect(
      new URL(
        `/auth/error?message=${encodeURIComponent("An error occurred during authentication")}`,
        request.url
      )
    );
  }
}
