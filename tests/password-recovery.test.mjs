import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import test from "node:test";

import {
  inspectRecoveryUrl,
  updateRecoveredPassword,
  validateNewPassword,
} from "../lib/password-recovery.ts";


test("reset route exists", () => {
  assert.equal(existsSync(new URL("../app/reset-password/page.tsx", import.meta.url)), true);
});

test("valid recovery links are recognized", () => {
  assert.equal(
    inspectRecoveryUrl(
      "https://www.hieusugoi.com/reset-password#access_token=a&refresh_token=b&type=recovery",
    ).hasRecoveryIntent,
    true,
  );
  assert.equal(
    inspectRecoveryUrl("https://www.hieusugoi.com/reset-password?code=pkce-code")
      .hasRecoveryIntent,
    true,
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

  assert.deepEqual(await updateRecoveredPassword(auth, "new-secret"), { ok: true });
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

  assert.deepEqual(await updateRecoveredPassword(auth, "new-secret"), { ok: false });
  assert.equal(signedOut, false);
  const page = readFileSync(
    new URL("../app/reset-password/page.tsx", import.meta.url),
    "utf8",
  );
  assert.doesNotMatch(page, /signUp\s*\(/);
});
