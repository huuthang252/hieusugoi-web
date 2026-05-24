import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import { createServerClient } from "@/lib/supabase-server";

const VERSION_MAP: Record<string, { downloadUrl: string; fileName: string }> = {
  "2.1.2": {
    downloadUrl:
      "https://github.com/huuthang252/hieusugoi-web/releases/download/v2.1.2/Hieusugoi_Setup_v2.1.2.exe",
    fileName: "Hieusugoi_Setup_v2.1.2.exe",
  },
};

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const version = searchParams.get("version");

  if (!version || !VERSION_MAP[version]) {
    return NextResponse.json(
      { error: "Invalid or missing version" },
      { status: 400 }
    );
  }

  // Check login via cookie-based server client
  const supabase = createServerClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session?.user) {
    return NextResponse.redirect(`${origin}/login`);
  }

  const { downloadUrl, fileName } = VERSION_MAP[version];

  // Insert log — failure must not crash the route
  try {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

    if (!supabaseUrl || !serviceRoleKey) {
      console.error("[download] Missing Supabase env vars — log skipped");
    } else {
      const adminClient = createClient(supabaseUrl, serviceRoleKey, {
        auth: { persistSession: false },
      });

      const ip =
        request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ??
        request.headers.get("x-real-ip") ??
        null;

      const { error } = await adminClient.from("download_logs").insert({
        user_id: session.user.id,
        email: session.user.email ?? null,
        version,
        file_name: fileName,
        download_url: downloadUrl,
        ip_address: ip,
        user_agent: request.headers.get("user-agent") ?? null,
      });

      if (error) {
        console.error("[download] Insert log failed:", error.message);
      }
    }
  } catch (err) {
    console.error("[download] Unexpected logging error:", err);
  }

  return NextResponse.redirect(downloadUrl);
}
