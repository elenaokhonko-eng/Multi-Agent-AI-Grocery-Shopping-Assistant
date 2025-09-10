import { UserProfile, DEFAULT_USER_PROFILE } from "@/types/user-profile";

const STORAGE_KEY = "user_profile";

/**
 * Load user profile from localStorage, fallback to default profile
 */
export function loadUserProfile(): UserProfile {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored) as UserProfile;
      // Merge with default profile to ensure all fields exist
      return {
        ...DEFAULT_USER_PROFILE,
        ...parsed,
        dietary_needs: {
          ...DEFAULT_USER_PROFILE.dietary_needs,
          ...parsed.dietary_needs,
        },
        brand_preferences: {
          ...DEFAULT_USER_PROFILE.brand_preferences,
          ...parsed.brand_preferences,
        },
        household_inventory: {
          ...DEFAULT_USER_PROFILE.household_inventory,
          ...parsed.household_inventory,
        },
        loyalty_membership: {
          ...DEFAULT_USER_PROFILE.loyalty_membership,
          ...parsed.loyalty_membership,
        },
        delivery_preferences: {
          ...DEFAULT_USER_PROFILE.delivery_preferences,
          ...parsed.delivery_preferences,
        },
      };
    }
  } catch (error) {
    console.warn("Failed to load user profile from localStorage:", error);
  }
  
  return DEFAULT_USER_PROFILE;
}

/**
 * Save user profile to localStorage
 */
export function saveUserProfile(profile: UserProfile): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(profile));
  } catch (error) {
    console.error("Failed to save user profile to localStorage:", error);
    throw new Error("Failed to save profile");
  }
}

/**
 * Clear user profile from localStorage
 */
export function clearUserProfile(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.error("Failed to clear user profile from localStorage:", error);
  }
}

/**
 * Export user profile as JSON string for backup
 */
export function exportUserProfile(profile: UserProfile): string {
  return JSON.stringify(profile, null, 2);
}

/**
 * Import user profile from JSON string
 */
export function importUserProfile(jsonString: string): UserProfile {
  try {
    const parsed = JSON.parse(jsonString) as UserProfile;
    // Validate and merge with default profile
    return {
      ...DEFAULT_USER_PROFILE,
      ...parsed,
      dietary_needs: {
        ...DEFAULT_USER_PROFILE.dietary_needs,
        ...parsed.dietary_needs,
      },
      brand_preferences: {
        ...DEFAULT_USER_PROFILE.brand_preferences,
        ...parsed.brand_preferences,
      },
      household_inventory: {
        ...DEFAULT_USER_PROFILE.household_inventory,
        ...parsed.household_inventory,
      },
      loyalty_membership: {
        ...DEFAULT_USER_PROFILE.loyalty_membership,
        ...parsed.loyalty_membership,
      },
      delivery_preferences: {
        ...DEFAULT_USER_PROFILE.delivery_preferences,
        ...parsed.delivery_preferences,
      },
    };
  } catch (error) {
    console.error("Failed to import user profile:", error);
    throw new Error("Invalid profile data");
  }
}
