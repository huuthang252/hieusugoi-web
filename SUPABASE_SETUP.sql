-- Supabase SQL Setup for Email Confirmation Flow

-- ============================================
-- OPTION A: Create profiles table without RLS (Simpler, for development)
-- ============================================

CREATE TABLE IF NOT EXISTS profiles (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
  username TEXT NOT NULL,
  email TEXT NOT NULL,
  plan TEXT NOT NULL DEFAULT 'standard',
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Ensure pgcrypto is available for license key generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE INDEX IF NOT EXISTS profiles_user_id_idx ON profiles(user_id);
CREATE INDEX IF NOT EXISTS profiles_email_idx ON profiles(email);

CREATE TABLE IF NOT EXISTS licenses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
  plan TEXT NOT NULL DEFAULT 'standard',
  status TEXT NOT NULL DEFAULT 'trial',
  trial_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  trial_end TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '14 days'),
  license_key TEXT NOT NULL UNIQUE DEFAULT gen_random_uuid()::text,
  max_devices INT NOT NULL DEFAULT 1,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS licenses_user_id_idx ON licenses(user_id);

-- Test: Make sure table is accessible
SELECT COUNT(*) as profile_count FROM profiles;

-- ============================================
-- OPTION B: Create profiles table with RLS (Production)
-- ============================================

-- Run the above table creation first, then:

-- Enable RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own profile
CREATE POLICY "Users can view own profile"
  ON profiles FOR SELECT
  USING (auth.uid() = user_id);

-- Policy: Users can update their own profile
CREATE POLICY "Users can update own profile"
  ON profiles FOR UPDATE
  USING (auth.uid() = user_id);

-- Policy: Service role can insert (needed for profile creation)
CREATE POLICY "Service role can insert profiles"
  ON profiles FOR INSERT
  WITH CHECK (true);

-- ============================================
-- OPTION C: Create AUTO-INSERT trigger (Recommended)
-- ============================================

-- This creates a profile automatically when a user signs up
-- Skip if you prefer manual/application-controlled creation

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

-- Create trigger (drop existing first)
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================
-- Verify Setup
-- ============================================

-- Check profiles table exists
SELECT EXISTS(SELECT FROM information_schema.tables WHERE table_name = 'profiles') as table_exists;

-- Check profiles structure
\d profiles

-- Check if RLS is enabled
SELECT relname, relrowsecurity FROM pg_class WHERE relname = 'profiles';

-- Check RLS policies
SELECT tablename, policyname, permissive, roles, qual, with_check 
FROM pg_policies 
WHERE tablename = 'profiles';

-- Check existing profiles
SELECT user_id, username, email, plan, status FROM profiles LIMIT 10;

-- Check auth users
SELECT id, email, email_confirmed_at, raw_user_meta_data FROM auth.users LIMIT 10;

-- ============================================
-- Download Logs Table
-- ============================================

CREATE TABLE IF NOT EXISTS download_logs (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  email TEXT,
  version TEXT NOT NULL,
  file_name TEXT,
  download_url TEXT,
  downloaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ip_address TEXT,
  user_agent TEXT
);

-- Only service role can insert/select (no user-facing RLS needed)
ALTER TABLE download_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access on download_logs"
  ON download_logs
  USING (false)
  WITH CHECK (false);

CREATE INDEX IF NOT EXISTS download_logs_user_id_idx ON download_logs(user_id);
CREATE INDEX IF NOT EXISTS download_logs_downloaded_at_idx ON download_logs(downloaded_at DESC);

-- ============================================
-- Troubleshooting Queries
-- ============================================

-- If RLS is blocking inserts:
-- ALTER TABLE profiles DISABLE ROW LEVEL SECURITY;

-- If you need to drop and recreate:
-- DROP TRIGGER on_auth_user_created ON auth.users;
-- DROP FUNCTION handle_new_user();
-- DROP TABLE profiles;

-- Clear all profiles (DANGEROUS!)
-- DELETE FROM profiles;

-- Test insert from application
-- INSERT INTO profiles (user_id, username, email, plan, status) VALUES (
--   'your-user-uuid',
--   'testuser',
--   'test@example.com',
--   'standard',
--   'active'
-- );
