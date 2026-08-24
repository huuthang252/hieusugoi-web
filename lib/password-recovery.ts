export const MIN_PASSWORD_LENGTH = 6;

type RecoveryAuth = {
  updateUser: (attributes: { password: string }) => Promise<{
    error: { message?: string } | null;
  }>;
  signOut: () => Promise<unknown>;
};

export type RecoveryLinkState = {
  hasRecoveryIntent: boolean;
  code: string | null;
  flow: "implicit" | "pkce" | null;
  error: "expired" | "invalid" | null;
};

type RecoverySessionAuth = {
  getSession: () => Promise<{
    data: { session: unknown | null };
    error: unknown | null;
  }>;
  getUser: () => Promise<{
    data: { user: unknown | null };
    error: unknown | null;
  }>;
  onAuthStateChange: (
    callback: (event: string) => void,
  ) => { data: { subscription: { unsubscribe: () => void } } };
};

export function inspectRecoveryUrl(url: string): RecoveryLinkState {
  const parsed = new URL(url);
  const query = parsed.searchParams;
  const hash = new URLSearchParams(parsed.hash.replace(/^#/, ""));
  const errorCode = query.get("error_code") || hash.get("error_code");
  const errorDescription = (
    query.get("error_description") ||
    hash.get("error_description") ||
    ""
  ).toLowerCase();
  const error = query.get("error") || hash.get("error");

  if (errorCode?.includes("expired") || errorDescription.includes("expired")) {
    return { hasRecoveryIntent: true, code: null, flow: null, error: "expired" };
  }
  if (error || errorCode) {
    return { hasRecoveryIntent: true, code: null, flow: null, error: "invalid" };
  }

  const code = query.get("code");
  const type = query.get("type") || hash.get("type");
  const hasHashCredentials = hash.has("access_token") && hash.has("refresh_token");
  if (type && type !== "recovery") {
    return { hasRecoveryIntent: true, code: null, flow: null, error: "invalid" };
  }
  if (type === "recovery" && hasHashCredentials) {
    return { hasRecoveryIntent: true, code: null, flow: "implicit", error: null };
  }
  if (type === "recovery" || hasHashCredentials || code) {
    return { hasRecoveryIntent: true, code: null, flow: null, error: "invalid" };
  }
  return { hasRecoveryIntent: false, code: null, flow: null, error: null };
}

export function monitorRecoverySession(
  auth: RecoverySessionAuth,
  onValid: () => void,
) {
  let active = true;

  const validate = async () => {
    const { data: sessionData, error: sessionError } = await auth.getSession();
    if (!active || sessionError || !sessionData.session) return false;
    const { data: userData, error: userError } = await auth.getUser();
    if (!active || userError || !userData.user) return false;
    onValid();
    return true;
  };

  const { data } = auth.onAuthStateChange((event) => {
    if (event === "PASSWORD_RECOVERY") {
      void validate();
    }
  });

  return {
    validate,
    stop: () => {
      active = false;
      data.subscription.unsubscribe();
    },
  };
}

export function validateNewPassword(password: string, confirmation: string): string | null {
  if (!password) {
    return "Vui lòng nhập mật khẩu mới.";
  }
  if (password.length < MIN_PASSWORD_LENGTH) {
    return `Mật khẩu phải có ít nhất ${MIN_PASSWORD_LENGTH} ký tự.`;
  }
  if (password !== confirmation) {
    return "Mật khẩu xác nhận không khớp.";
  }
  return null;
}

export async function updateRecoveredPassword(
  auth: RecoveryAuth,
  password: string,
): Promise<{ ok: true } | { ok: false }> {
  const { error } = await auth.updateUser({ password });
  if (error) {
    return { ok: false };
  }

  // A recovery link creates a temporary browser session. The product flow returns
  // to Desktop, so do not leave the website automatically signed in.
  await auth.signOut();
  return { ok: true };
}
