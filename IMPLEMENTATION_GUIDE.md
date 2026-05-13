# Supabase Email Confirmation Flow - Implementation Guide

## Implementation Summary

The email confirmation flow has been successfully implemented for hieusugoi-web. Users must now confirm their email before accessing the download page.

---

## Files Created

### 1. `/lib/profile.ts`
- Database utility functions for profile management
- `ensureProfileExists()`: Creates profile row if it doesn't exist
- `getProfile()`: Retrieves user profile by user_id
- `isEmailConfirmed()`: Checks if user's email is confirmed
- Profile structure: `user_id`, `username`, `email`, `plan` (standard), `status` (active)

### 2. `/app/auth/callback/route.ts`
- Route handler for email confirmation callback
- Exchanges auth code for session
- Creates profile row after confirmed login
- Redirects to `/account` on success
- Handles errors with `/auth/error?message=...`

### 3. `/app/auth/error/page.tsx`
- Error page for auth failures
- Displays error message from URL params
- Wrapped with Suspense for useSearchParams compatibility
- Links back to login or home

---

## Files Modified

### 1. `app/register/page.tsx`
Changes:
- Added `username` state field
- Added username input field to form
- Updated signUp to include:
  - `options.data.username`: Stores username in user metadata
  - `options.emailRedirectTo`: Uses `window.location.origin/auth/callback`
- Updated success message to inform user about email confirmation
- Added setTimeout to delay redirect to /login

### 2. `lib/supabase-server.ts`
Changes:
- Added `setCookie` function for proper cookie management
- Added `setAll` method to cookies config for session persistence
- Enables proper session exchange in callback route

### 3. `app/download/page.tsx`
Changes:
- Imported `isEmailConfirmed` from profile utils
- Added email confirmation check before download access
- Redirects to error page if email not confirmed
- Message: "Please confirm your email to access downloads"

### 4. `app/account/page.tsx`
Changes:
- Imported profile utilities
- Calls `ensureProfileExists()` to create profile if missing
- Retrieves profile to display username
- Shows username in greeting: "You are signed in as {username}"

### 5. `app/login/page.tsx`
Changes:
- Added check for `email_confirmed_at` after login
- Shows error message if email not confirmed
- Message: "Please confirm your email before accessing your account"

---

## Production Flow

```
1. User visits https://hieusugoi.com/register
   ↓
2. User enters: username, email, password
   ↓
3. Website calls supabase.auth.signUp with:
   - email
   - password
   - options.data.username (stored in user metadata)
   - options.emailRedirectTo: "https://hieusugoi.com/auth/callback"
   ↓
4. Supabase sends confirmation email
   ↓
5. User clicks link in email (contains auth code)
   ↓
6. Browser redirects to: https://hieusugoi.com/auth/callback?code=...
   ↓
7. Route handler /auth/callback:
   - Exchanges code for session
   - Calls ensureProfileExists()
   - Creates profile row with: user_id, username, email, plan, status
   - Redirects to /account
   ↓
8. User can now access /download (email_confirmed_at is set)
```

## Local Development Flow

Same as production, but:
- Register: `http://localhost:3000/register`
- Callback: `http://localhost:3000/auth/callback`
- Download: `http://localhost:3000/download`

---

## Supabase Dashboard Configuration

### Authentication Settings

1. **Go to Authentication > Providers > Email**
   - ✓ Enable Email Provider
   - ✓ Enable Confirm email

2. **Site URL**
   - Set to: `https://hieusugoi.com`

3. **Redirect URLs** (add all four)
   - `http://localhost:3000/auth/callback`
   - `http://localhost:3000/login`
   - `https://hieusugoi.com/auth/callback`
   - `https://hieusugoi.com/login`

4. **Email Templates** (optional, but recommended)
   - Go to Authentication > Email Templates
   - Customize the confirmation email
   - Ensure {{ .ConfirmationURL }} is included in template

---

## Database Schema

### Create `profiles` Table

Run this SQL in Supabase SQL Editor:

```sql
-- Create profiles table
CREATE TABLE profiles (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  username TEXT NOT NULL,
  email TEXT NOT NULL,
  plan TEXT NOT NULL DEFAULT 'standard',
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  UNIQUE(user_id)
);

-- Create index for faster lookups
CREATE INDEX profiles_user_id_idx ON profiles(user_id);
CREATE INDEX profiles_email_idx ON profiles(email);

-- Enable Row Level Security
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read their own profile
CREATE POLICY "Users can read own profile" ON profiles
  FOR SELECT USING (auth.uid() = user_id);

-- Policy: Users can update their own profile
CREATE POLICY "Users can update own profile" ON profiles
  FOR UPDATE USING (auth.uid() = user_id);

-- Policy: Service role can insert profiles
CREATE POLICY "Service role can insert profiles" ON profiles
  FOR INSERT WITH CHECK (true);
```

### Alternative: Create Without RLS (Simpler)

If you don't need RLS initially:

```sql
CREATE TABLE profiles (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
  username TEXT NOT NULL,
  email TEXT NOT NULL,
  plan TEXT NOT NULL DEFAULT 'standard',
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX profiles_user_id_idx ON profiles(user_id);
CREATE INDEX profiles_email_idx ON profiles(email);
```

---

## Testing Locally

### Prerequisites
1. Node.js and npm installed
2. `.env.local` configured with Supabase credentials
3. Docker (if running Supabase locally) or Supabase hosted project

### Start Local Development Server

```bash
cd hieusugoi-web
npm install  # if not already done
npm run dev
```

Server runs at: `http://localhost:3000`

### Test Registration Flow

1. Open `http://localhost:3000/register`
2. Fill form:
   - Username: `testuser`
   - Email: `test@example.com` (use a real email you can access)
   - Password: `SecurePassword123!`
3. Click "Register"
4. Should see: "Account created! Check your email for a confirmation link..."
5. Redirects to `/login` after 3 seconds

### Test Email Confirmation

If using Supabase's Local Dev setup:
- Check Supabase Studio for sent emails
- Or use a service like Mailtrap or Gmail's test inbox

If using Supabase hosted:
- Check your actual email inbox
- Click the confirmation link
- Should redirect to `http://localhost:3000/auth/callback?code=...`

### After Confirmation

1. Should be redirected to `http://localhost:3000/account`
2. Should see: "Your account - You are signed in as testuser"
3. Click "Sign out"

### Test Login with Confirmed Email

1. Go to `http://localhost:3000/login`
2. Enter email and password
3. Click "Sign in"
4. Should redirect to `/account`
5. Can now access `/download`

### Test Download Access

1. Go to `http://localhost:3000/download`
2. If logged in and confirmed: Shows download page
3. If logged out: Redirects to `/login`
4. If not confirmed: Shows error "Please confirm your email to access downloads"

### Test Without Email Confirmation

1. Create new account
2. Don't click confirmation link
3. Try to login
4. Should see: "Please confirm your email before accessing your account"
5. Try to access `/download` directly
6. Should redirect with error message

---

## Testing on Production (hieusugoi.com)

### Prerequisites
1. Update redirect URLs in Supabase:
   - `https://hieusugoi.com/auth/callback`
   - `https://hieusugoi.com/login`
2. Build deployed: `npm run build && npm run start`

### Test Flow

1. Open `https://hieusugoi.com/register`
2. Create account with real email address
3. Check email for confirmation link
4. Click link - redirects to `https://hieusugoi.com/auth/callback?code=...`
5. Should be logged in and redirected to account page
6. Access `https://hieusugoi.com/download`
7. Download should work

### Monitor

- Check Supabase Dashboard > Auth > Users
  - Verify user has `email_confirmed_at` timestamp
  - Verify user_metadata contains username
- Check Supabase Dashboard > SQL Editor
  - Verify profile row exists in profiles table

---

## Verification Checklist

- [x] Register page includes username field
- [x] Username stored in user metadata (options.data.username)
- [x] emailRedirectTo uses window.location.origin for dynamic URLs
- [x] /auth/callback route created and functional
- [x] Profile row created after email confirmation
- [x] Profile includes: user_id, username, email, plan=standard, status=active
- [x] /download requires confirmed email (email_confirmed_at)
- [x] /login checks email confirmation status
- [x] /account shows username from profile
- [x] Error handling for failed auth callbacks
- [x] Suspense wrapper for useSearchParams
- [x] Build successful with no TypeScript errors
- [x] Dark glass futuristic UI maintained

---

## Troubleshooting

### "NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY must be configured"
- Check `.env.local` has both variables
- Restart dev server after changing .env

### Email not being sent
- Verify email provider is enabled in Supabase Auth settings
- Check email templates are set up
- Use Supabase Studio to check auth logs

### Callback redirect not working
- Verify redirect URLs in Supabase Auth settings include your URL
- Check browser console for errors
- Verify code parameter is in URL

### "Profile" table not found error
- Run the SQL schema creation script in Supabase SQL Editor
- Verify table exists: SELECT * FROM profiles LIMIT 1

### Can't access /download after confirmation
- Check user.email_confirmed_at in Supabase Auth
- Verify browser session cookie is set
- Try logout and login again

---

## Next Steps (Not Implemented)

- Payment/subscription system (not in scope)
- Trial expiration (not in scope)
- Email resend confirmation link
- Password reset flow
- 2FA setup
- Profile editing interface
- Admin dashboard

