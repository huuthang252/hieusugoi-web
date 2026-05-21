import { cookies } from "next/headers";
import { createServerClient as createServerClientBase } from "@supabase/auth-helpers-nextjs";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

const getAllCookies = async () => {
  const cookieStore = await cookies();
  return cookieStore.getAll().map((cookie) => ({
    name: cookie.name,
    value: cookie.value,
    options: {
      maxAge: cookie.value ? undefined : 0,
      path: "/",
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax" as const,
    },
  }));
};

const setCookie = async (name: string, value: string, options: any) => {
  try {
    const cookieStore = await cookies();
    cookieStore.set(name, value, {
      ...options,
      path: options.path || "/",
      httpOnly: options.httpOnly !== false,
      secure: options.secure !== false && process.env.NODE_ENV === "production",
      sameSite: options.sameSite || "lax",
    });
  } catch {
    // Cookies can only be modified in a Server Action or Route Handler.
    // Ignore when called from a Server Component — reads still work fine.
  }
};

export const createServerClient = () => {
  if (!supabaseUrl || !supabaseKey) {
    throw new Error("NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY must be set.");
  }

  return createServerClientBase(supabaseUrl, supabaseKey, {
    cookies: {
      getAll: getAllCookies,
      setAll: async (cookies_list: any[]) => {
        try {
          for (const cookie of cookies_list) {
            await setCookie(cookie.name, cookie.value, cookie.options || {});
          }
        } catch {
          // Same guard — ignore when not in a Server Action or Route Handler.
        }
      },
    },
  });
};
