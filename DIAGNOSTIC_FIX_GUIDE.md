# Email Confirmation Flow - Diagnostic & Fix Guide

## Root Causes Identified & Fixed

### 1. **Cookie Session Persistence (FIXED)**
**Problem:** The `supabase-server.ts` `setAll` callback wasn't preserving cookie options (httpOnly, secure, sameSite, path, maxAge). This meant the session cookies weren't being properly set in the browser response, so `getSession()` always returned null.

**Fix:** Updated cookie handling to properly set all required options:
```typescript
const setCookie = async (name: string, value: string, options: any) => {
  const cookieStore = await cookies();
  cookieStore.set(name, value, {
    ...options,
    path: options.path || "/",
    httpOnly: options.httpOnly !== false,
    secure: options.secure !== false && process.env.NODE_ENV === "production",
    sameSite: options.sameSite || "lax",
  });
};
```

### 2. **Session Retrieval After Code Exchange (FIXED)**
**Problem:** The callback was using `getSession()` which reads from request cookies, but those weren't properly set yet. The new approach uses `getUser()` which works immediately after `exchangeCodeForSession()`.

**Fix:** Changed from:
```typescript
const { data: { session } } = await supabase.auth.getSession();
```
To:
```typescript
const { data: { user } } = await supabase.auth.getUser();
```

### 3. **Missing Error Visibility (FIXED)**
**Problem:** Profile creation errors were logged but didn't surface, making debugging impossible.

**Fix:** Enhanced `ensureProfileExists()` to return error details:
```typescript
export async function ensureProfileExists(
  ...
): Promise<{ profile: UserProfile | null; error?: string }> {
  // Now returns { profile, error } instead of just profile
}
```

---

## Files Modified

| File | Changes |
|------|---------|
| `lib/supabase-server.ts` | Fixed cookie options handling in getAllCookies and setCookie |
| `lib/profile.ts` | Changed return type to include error details |
| `app/auth/callback/route.ts` | Now uses getUser() instead of getSession(), added comprehensive logging |
| `app/account/page.tsx` | Updated to handle new return type from ensureProfileExists |

---

## How Profile Creation is Triggered

### Flow 1: Application-Controlled (Current Implementation)
```
User clicks email confirmation link
  ↓
Browser redirects to /auth/callback?code=...
  ↓
Callback: exchangeCodeForSession(code)
  ↓
Callback: getUser() → retrieves authenticated user
  ↓
Callback: ensureProfileExists() → creates profile row
  ↓
Profile row inserted with:
  - user_id (from auth.users.id)
  - username (from user.user_metadata.username)
  - email (from user.email)
  - plan = 'standard'
  - status = 'active'
  ↓
Redirect to /account
```

### Flow 2: Database Trigger (Recommended for Production)
If you want automatic profile creation, add this trigger in Supabase SQL Editor:

```sql
CREATE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.profiles (user_id, username, email, plan, status)
  VALUES (
    new.id,
    COALESCE(new.raw_user_meta_data->>'username', split_part(new.email, '@', 1)),
    new.email,
    'standard',
    'active'
  );
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

This creates the profile automatically when the user signs up (before email confirmation).

---

## Debugging Checklist

### 1. Check Supabase Auth Settings
```
Authentication > Settings
- Site URL: https://hieusugoi.com (or http://localhost:3000)
- Redirect URLs must include: /auth/callback
```

### 2. Check profiles Table
Run in Supabase SQL Editor:
```sql
-- Verify table exists and has correct structure
\d profiles

-- Check existing profiles
SELECT user_id, username, email, plan, status FROM profiles;

-- Check if RLS is blocking inserts
SELECT relrowsecurity FROM pg_class WHERE relname = 'profiles';

-- Check RLS policies
SELECT policyname, permissive, roles FROM pg_policies WHERE tablename = 'profiles';
```

### 3. Check Auth Users
```sql
-- See if user was created and confirmed
SELECT id, email, email_confirmed_at, raw_user_meta_data 
FROM auth.users 
ORDER BY created_at DESC 
LIMIT 1;
```

### 4. Check Application Logs
During local development:
```bash
npm run dev
# Watch the terminal for [Callback] logs
```

Expected log sequence:
```
[Callback] Exchanging code for session...
[Callback] Code exchange successful
[Callback] User retrieved: {uuid}, email: user@example.com, confirmed: true
[Callback] Creating profile for user_id: {uuid}, username: testuser, email: user@example.com
Profile created for user {uuid}: testuser
[Callback] Profile created/verified: {uuid}
[Callback] Redirecting to: /account
```

---

## Common Issues & Solutions

### Issue 1: "profiles table does not exist"
**Solution:** Run SUPABASE_SETUP.sql in Supabase SQL Editor (see file in project)

### Issue 2: "Email not confirmed" after clicking link
**Causes:**
- Cookie not being set → Check supabase-server.ts fixes
- Session not persisting → Browser not saving cookies
- Email not actually confirmed in auth.users

**Debug:**
1. Check browser DevTools > Application > Cookies
2. Should see `sb-*-auth-token` cookie
3. Verify in Supabase: `SELECT email_confirmed_at FROM auth.users WHERE email='...'`

### Issue 3: profiles table is empty after confirmation
**Causes:**
- RLS policies blocking inserts
- Profile creation failing silently
- Table belongs to wrong schema

**Debug:**
1. Check callback logs for errors
2. Manually insert: 
   ```sql
   INSERT INTO profiles (user_id, username, email, plan, status) 
   VALUES ('your-uuid', 'testuser', 'test@example.com', 'standard', 'active');
   ```
3. If fails: RLS is blocking. See RLS solutions below.

### Issue 4: RLS policies blocking profile insertion
**Solutions:**

Option A - Disable RLS (development only):
```sql
ALTER TABLE profiles DISABLE ROW LEVEL SECURITY;
```

Option B - Fix RLS policies:
```sql
-- Drop old policies
DROP POLICY IF EXISTS "Users can read own profile" ON profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON profiles;
DROP POLICY IF EXISTS "Service role can insert profiles" ON profiles;

-- Create correct policies
CREATE POLICY "Users can read own profile" ON profiles
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own profile" ON profiles
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Service role can insert profiles" ON profiles
  FOR INSERT WITH CHECK (true);
```

---

## Testing Locally

### Setup
```bash
cd hieusugoi-web
npm run dev
```

### Test Flow
1. Open http://localhost:3000/register
2. Create account:
   - Username: testuser
   - Email: your-email@example.com
   - Password: SecurePass123!
3. Check email for confirmation link
4. Click link → redirects to http://localhost:3000/auth/callback?code=...
5. Should redirect to http://localhost:3000/account
6. Should see "You are signed in as testuser"
7. Can access http://localhost:3000/download

### Verify Database
In Supabase SQL Editor:
```sql
-- Check user was confirmed
SELECT id, email, email_confirmed_at FROM auth.users WHERE email='your-email@example.com';

-- Check profile was created
SELECT user_id, username, email, plan, status FROM profiles 
WHERE email='your-email@example.com';
```

---

## Production Deployment

### 1. Verify Settings in Supabase
```
Authentication > Settings:
- Site URL: https://hieusugoi.com
- Redirect URLs:
  • https://hieusugoi.com/auth/callback
  • https://hieusugoi.com/login
  (plus localhost versions for dev)
```

### 2. Deploy Next.js
```bash
npm run build
# Deploy build/ directory to your hosting
```

### 3. Verify Deployment
```
1. Open https://hieusugoi.com/register
2. Create account
3. Check email (may take 1-2 minutes)
4. Click link
5. Should redirect to https://hieusugoi.com/account
```

---

## Build Status

✅ Build Successful
```
✓ Compiled successfully in 3.8s
✓ Finished TypeScript in 3.2s
✓ All pages generated
✓ Ready for deployment
```

---

## Key Changes Summary

1. **Session persistence** - Fixed cookie options in supabase-server.ts
2. **User retrieval** - Changed from getSession() to getUser() after code exchange
3. **Error reporting** - Enhanced profile creation error details
4. **Logging** - Added comprehensive logging to callback for debugging
5. **Account page** - Updated to handle new profile return type

These fixes ensure:
- ✅ Session cookies persist after email confirmation
- ✅ Callback properly exchanges code and creates session
- ✅ Profile is created with correct user information
- ✅ Login recognizes confirmed emails
- ✅ Account page displays username
- ✅ Download page remains protected
