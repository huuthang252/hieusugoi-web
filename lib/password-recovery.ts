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
  error: "expired" | "invalid" | null;
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
    return { hasRecoveryIntent: true, code: null, error: "expired" };
  }
  if (error || errorCode) {
    return { hasRecoveryIntent: true, code: null, error: "invalid" };
  }

  const code = query.get("code");
  const type = query.get("type") || hash.get("type");
  const hasRecoveryIntent =
    type === "recovery" ||
    Boolean(code) ||
    (hash.has("access_token") && hash.has("refresh_token"));
  return { hasRecoveryIntent, code, error: null };
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
