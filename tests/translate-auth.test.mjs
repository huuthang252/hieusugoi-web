import assert from "node:assert/strict";
import test from "node:test";

import { isTranslateRequestAuthenticated } from "../app/api/translate/auth.ts";


const fakeSupabase = ({ bearerUser = null, cookieUser = null } = {}) => {
  const calls = { getUser: [], getSession: 0 };
  return {
    calls,
    client: {
      auth: {
        async getUser(token) {
          calls.getUser.push(token);
          return { data: { user: bearerUser }, error: null };
        },
        async getSession() {
          calls.getSession += 1;
          return {
            data: { session: cookieUser ? { user: cookieUser } : null },
            error: null,
          };
        },
      },
    },
  };
};


test("accepts a valid bearer token without using cookie auth", async () => {
  const supabase = fakeSupabase({ bearerUser: { id: "desktop-user" } });
  const request = new Request("https://www.hieusugoi.com/api/translate", {
    method: "POST",
    headers: { Authorization: "Bearer synthetic-access-token" },
  });

  assert.equal(
    await isTranslateRequestAuthenticated(request, supabase.client),
    true,
  );
  assert.deepEqual(supabase.calls.getUser, ["synthetic-access-token"]);
  assert.equal(supabase.calls.getSession, 0);
});


test("preserves browser-cookie authentication when bearer token is absent", async () => {
  const supabase = fakeSupabase({ cookieUser: { id: "web-user" } });
  const request = new Request("https://www.hieusugoi.com/api/translate", {
    method: "POST",
  });

  assert.equal(
    await isTranslateRequestAuthenticated(request, supabase.client),
    true,
  );
  assert.deepEqual(supabase.calls.getUser, []);
  assert.equal(supabase.calls.getSession, 1);
});


test("rejects a request when bearer and cookie authentication both fail", async () => {
  const supabase = fakeSupabase();
  const request = new Request("https://www.hieusugoi.com/api/translate", {
    method: "POST",
  });

  assert.equal(
    await isTranslateRequestAuthenticated(request, supabase.client),
    false,
  );
  assert.deepEqual(supabase.calls.getUser, []);
  assert.equal(supabase.calls.getSession, 1);
});
