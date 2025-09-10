import { UserProfile, DEFAULT_USER_PROFILE } from "@/types/user-profile";

const STORAGE_KEY = "user_profile";
const API_BASE_URL = "http://localhost:3001/api/profile";

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
 * Load user profile from backend API
 */
export async function loadUserProfileFromBackend(userId: string = "default_user"): Promise<UserProfile> {
  try {
    const response = await fetch(`${API_BASE_URL}/user/${userId}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const profile = await response.json();
    
    // Also save to localStorage as backup
    localStorage.setItem(STORAGE_KEY, JSON.stringify(profile));
    
    return profile;
  } catch (error) {
    console.warn("Failed to load user profile from backend, falling back to localStorage:", error);
    return loadUserProfile();
  }
}

/**
 * Save user profile to localStorage and backend
 */
export async function saveUserProfile(profile: UserProfile): Promise<void> {
  try {
    // Save to localStorage first (immediate)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(profile));
    
    // Then save to backend (for pipeline usage)
    const response = await fetch(`${API_BASE_URL}/user/${profile.user_id}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(profile),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    console.log("Profile saved to backend:", result);
  } catch (error) {
    console.error("Failed to save user profile to backend:", error);
    // Don't throw error here - localStorage save already succeeded
    // This ensures the UI doesn't break if backend is down
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
