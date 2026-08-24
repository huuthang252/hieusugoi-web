import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import test from "node:test";

import {
  inspectRecoveryUrl,
  keepCurrentPassword,
  monitorRecoverySession,
  updateRecoveredPassword,
  validateNewPassword,
} from "../lib/password-recovery.ts";


test("reset route exists", () => {
  assert.equal(existsSync(new URL("../app/reset-password/page.tsx", import.meta.url)), true);
});

test("valid recovery links are recognized", () => {
  assert.deepEqual(
    inspectRecoveryUrl(
      "https://www.hieusugoi.com/reset-password#access_token=test-token&refresh_token=test-refresh&expires_in=3600&token_type=bearer&type=recovery",
    ),
    { hasRecoveryIntent: true, code: null, flow: "implicit", error: null },
  );
  assert.equal(
    inspectRecoveryUrl("https://www.hieusugoi.com/reset-password?code=unrelated-code").error,
    "invalid",
  );
});

test("invalid and expired recovery states are rejected", () => {
  assert.equal(
    inspectRecoveryUrl("https://www.hieusugoi.com/reset-password").hasRecoveryIntent,
    false,
  );
  assert.equal(
    inspectRecoveryUrl(
      "https://www.hieusugoi.com/reset-password#error=access_denied&error_code=otp_expired",
    ).error,
    "expired",
  );
  assert.equal(
    inspectRecoveryUrl(
      "https://www.hieusugoi.com/reset-password#access_token=a&refresh_token=b&type=signup",
    ).error,
    "invalid",
  );
  assert.equal(
    inspectRecoveryUrl(
      "https://www.hieusugoi.com/reset-password#access_token=a&refresh_token=b",
    ).error,
    "invalid",
  );
});

const fakeRecoveryAuth = ({ session = null, user = null, sessionPromise } = {}) => {
  let listener = () => {};
  let unsubscribed = false;
  const auth = {
    async getSession() {
      if (sessionPromise) return sessionPromise;
      return { data: { session }, error: null };
    },
    async getUser() {
      return { data: { user }, error: null };
    },
    onAuthStateChange(callback) {
      listener = callback;
      return {
        data: {
          subscription: { unsubscribe: () => { unsubscribed = true; } },
        },
      };
    },
  };
  return {
    auth,
    emit: (event) => listener(event),
    wasUnsubscribed: () => unsubscribed,
  };
};

test("valid hash recovery session enables the password form state", async () => {
  const fake = fakeRecoveryAuth({ session: { access_token: "test-token" }, user: { id: "user" } });
  let state = "checking";
  const monitor = monitorRecoverySession(fake.auth, () => { state = "ready"; });
  assert.equal(await monitor.validate(), true);
  assert.equal(state, "ready");
  monitor.stop();
});

test("PASSWORD_RECOVERY event validates and enables recovery state", async () => {
  const fake = fakeRecoveryAuth({ session: { access_token: "test-token" }, user: { id: "user" } });
  let state = "checking";
  const monitor = monitorRecoverySession(fake.auth, () => { state = "ready"; });
  fake.emit("PASSWORD_RECOVERY");
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.equal(state, "ready");
  monitor.stop();
  assert.equal(fake.wasUnsubscribed(), true);
});

test("session check remains pending while Supabase processes credentials", async () => {
  let resolveSession;
  const sessionPromise = new Promise((resolve) => { resolveSession = resolve; });
  const fake = fakeRecoveryAuth({ sessionPromise, user: { id: "user" } });
  let state = "checking";
  const monitor = monitorRecoverySession(fake.auth, () => { state = "ready"; });
  const validation = monitor.validate();
  await Promise.resolve();
  assert.equal(state, "checking");
  resolveSession({ data: { session: { access_token: "test-token" } }, error: null });
  assert.equal(await validation, true);
  assert.equal(state, "ready");
  monitor.stop();
});

test("invalid or failed sessions remain invalid", async () => {
  const missing = fakeRecoveryAuth();
  const failedUser = fakeRecoveryAuth({ session: { access_token: "test-token" } });
  assert.equal(await monitorRecoverySession(missing.auth, () => {}).validate(), false);
  assert.equal(await monitorRecoverySession(failedUser.auth, () => {}).validate(), false);
});

test("URL cleanup callback runs only after server-verified session", async () => {
  const order = [];
  const fake = fakeRecoveryAuth({ session: { access_token: "test-token" }, user: { id: "user" } });
  const originalGetUser = fake.auth.getUser;
  fake.auth.getUser = async () => {
    order.push("getUser");
    return originalGetUser();
  };
  const monitor = monitorRecoverySession(fake.auth, () => order.push("cleanup"));
  await monitor.validate();
  assert.deepEqual(order, ["getUser", "cleanup"]);
  monitor.stop();
});

test("password mismatch and minimum length are rejected", () => {
  assert.match(validateNewPassword("secret", "different"), /không khớp/);
  assert.match(validateNewPassword("short", "short"), /ít nhất 6/);
  assert.equal(validateNewPassword("secret", "secret"), null);
});

test("successful recovery updates the password and signs out temporary session", async () => {
  const calls = [];
  const auth = {
    async updateUser(attributes) {
      calls.push(["updateUser", attributes]);
      return { error: null };
    },
    async signOut() {
      calls.push(["signOut"]);
    },
  };

  assert.deepEqual(await updateRecoveredPassword(auth, "new-secret"), { status: "updated" });
  assert.deepEqual(calls, [
    ["updateUser", { password: "new-secret" }],
    ["signOut"],
  ]);
  assert.equal("signUp" in auth, false);
});

test("password update failures do not sign out or create a user", async () => {
  let signedOut = false;
  const auth = {
    async updateUser() {
      return { error: { message: "synthetic failure" } };
    },
    async signOut() {
      signedOut = true;
    },
  };

  assert.deepEqual(await updateRecoveredPassword(auth, "new-secret"), { status: "error" });
  assert.equal(signedOut, false);
  const page = readFileSync(
    new URL("../app/reset-password/page.tsx", import.meta.url),
    "utf8",
  );
  assert.doesNotMatch(page, /signUp\s*\(/);
});

test("Supabase same_password error receives dedicated UX result", async () => {
  let signedOut = false;
  const auth = {
    async updateUser() {
      return { error: { code: "same_password", message: "provider message" } };
    },
    async signOut() {
      signedOut = true;
    },
  };
  assert.deepEqual(
    await updateRecoveredPassword(auth, "existing-secret"),
    { status: "same_password" },
  );
  assert.equal(signedOut, false);
});

test("keeping current password signs out without mutating the user", async () => {
  const calls = [];
  const auth = {
    async signOut() {
      calls.push("signOut");
    },
  };
  await keepCurrentPassword(auth);
  assert.deepEqual(calls, ["signOut"]);
  assert.equal("updateUser" in auth, false);
});
