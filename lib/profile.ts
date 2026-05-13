import { SupabaseClient } from "@supabase/supabase-js";

export interface UserProfile {
  id: string;
  user_id: string;
  username: string;
  email: string;
  plan: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface UserLicense {
  id: string;
  user_id: string;
  plan: string;
  status: string;
  trial_start: string;
  trial_end: string;
  license_key: string;
  max_devices: number;
  created_at: string;
  updated_at: string;
}

/**
 * Ensures a user profile exists in the database.
 * Creates one if it doesn't already exist.
 */
export async function ensureProfileExists(
  supabase: SupabaseClient,
  userId: string,
  email: string,
  username?: string
): Promise<{ profile: UserProfile | null; error?: string }> {
  try {
    // Check if profile already exists
    const { data: existingProfile, error: fetchError } = await supabase
      .from("profiles")
      .select("*")
      .eq("user_id", userId)
      .single();

    if (existingProfile) {
      return { profile: existingProfile as UserProfile };
    }

    // Profile doesn't exist, create one
    const displayName = username || email.split("@")[0];
    const { data: newProfile, error: createError } = await supabase
      .from("profiles")
      .insert({
        user_id: userId,
        username: displayName,
        email,
        plan: "standard",
        status: "active",
      })
      .select()
      .single();

    if (createError) {
      const errorMsg = `Failed to create profile: ${createError.message} (Code: ${createError.code})`;
      console.error(errorMsg);
      return { profile: null, error: errorMsg };
    }

    console.log(`Profile created for user ${userId}: ${displayName}`);
    return { profile: newProfile as UserProfile };
  } catch (error) {
    const errorMsg = `Error in ensureProfileExists: ${error instanceof Error ? error.message : String(error)}`;
    console.error(errorMsg);
    return { profile: null, error: errorMsg };
  }
}

/**
 * Ensures a license record exists for the user.
 * Creates one if missing and avoids duplicate rows.
 */
export async function ensureLicenseExists(
  supabase: SupabaseClient,
  userId: string
): Promise<{ license: UserLicense | null; error?: string }> {
  try {
    const { data: existingLicense, error: fetchError } = await supabase
      .from("licenses")
      .select("*")
      .eq("user_id", userId)
      .single();

    if (existingLicense) {
      return { license: existingLicense as UserLicense };
    }

    if (fetchError && fetchError.code !== "PGRST116") {
      const errorMsg = `Failed to fetch license: ${fetchError.message} (Code: ${fetchError.code})`;
      console.error(errorMsg);
      return { license: null, error: errorMsg };
    }

    const { data: newLicense, error: createError } = await supabase
      .from("licenses")
      .insert({
        user_id: userId,
      })
      .select()
      .single();

    if (createError) {
      if (createError.code === "23505") {
        const { data: existingAfterRetry } = await supabase
          .from("licenses")
          .select("*")
          .eq("user_id", userId)
          .single();
        if (existingAfterRetry) {
          return { license: existingAfterRetry as UserLicense };
        }
      }

      const errorMsg = `Failed to create license: ${createError.message} (Code: ${createError.code})`;
      console.error(errorMsg);
      return { license: null, error: errorMsg };
    }

    console.log(`License created for user ${userId}`);
    return { license: newLicense as UserLicense };
  } catch (error) {
    const errorMsg = `Error in ensureLicenseExists: ${error instanceof Error ? error.message : String(error)}`;
    console.error(errorMsg);
    return { license: null, error: errorMsg };
  }
}

/**
 * Gets a license by user ID.
 */
export async function getLicense(
  supabase: SupabaseClient,
  userId: string
): Promise<UserLicense | null> {
  try {
    const { data, error } = await supabase
      .from("licenses")
      .select("*")
      .eq("user_id", userId)
      .single();

    if (error && error.code !== "PGRST116") {
      console.error("Error fetching license:", error);
      return null;
    }

    return data as UserLicense;
  } catch (error) {
    console.error("Error in getLicense:", error);
    return null;
  }
}

/**
 * Gets a user profile by user ID.
 */
export async function getProfile(
  supabase: SupabaseClient,
  userId: string
): Promise<UserProfile | null> {
  try {
    const { data, error } = await supabase
      .from("profiles")
      .select("*")
      .eq("user_id", userId)
      .single();

    if (error && error.code !== "PGRST116") {
      // PGRST116 = no rows found (not an error)
      console.error("Error fetching profile:", error);
      return null;
    }

    return data as UserProfile;
  } catch (error) {
    console.error("Error in getProfile:", error);
    return null;
  }
}

/**
 * Checks if a user's email has been confirmed.
 */
export async function isEmailConfirmed(user: any): Promise<boolean> {
  // In Supabase, confirmed emails have email_confirmed_at set
  return user?.email_confirmed_at != null;
}
