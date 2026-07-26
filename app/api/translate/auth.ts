import type { SupabaseClient } from "@supabase/supabase-js";


const bearerToken = (request: Request): string | null => {
  const authorization = request.headers.get("authorization");
  if (!authorization?.toLowerCase().startsWith("bearer ")) {
    return null;
  }

  const token = authorization.slice(7).trim();
  return token || null;
};


export const isTranslateRequestAuthenticated = async (
  request: Request,
  supabase: SupabaseClient,
): Promise<boolean> => {
  const accessToken = bearerToken(request);
  if (accessToken) {
    const {
      data: { user },
      error,
    } = await supabase.auth.getUser(accessToken);
    return !error && Boolean(user);
  }

  const {
    data: { session },
  } = await supabase.auth.getSession();
  return Boolean(session?.user);
};
