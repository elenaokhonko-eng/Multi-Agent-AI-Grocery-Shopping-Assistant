export type UserProfile = {
  user_id: string;
  budget_limit_lkr: number;
  location?: string;

  dietary_needs: {
    vegetarian: boolean;
    vegan: boolean;
    gluten_free: boolean;
    dairy_free: boolean;
    organic_only: boolean;
    low_sodium: boolean;
    sugar_free: boolean;
    halal: boolean;
    kosher: boolean;
    allergies: string[];   // free text tags
  };

  brand_preferences: {
    preferred_brands: string[];
    disliked_brands: string[];
    premium_brands_only: boolean;
    local_brands_priority: boolean;
  };

  household_inventory: {
    current_items: Record<string, number>;
    expiry_dates: Record<string, string>;  // ISO date per sku/name
    low_stock_threshold: number;
  };

  loyalty_membership: {
    memberships: Record<string, string>;   // store -> member id
    points_balance: Record<string, number>;
    preferred_stores: string[];
  };

  delivery_preferences: {
    max_delivery_time_hours: number;
    max_delivery_radius_km: number;
    preferred_time_slots: string[];        // "09:00-12:00", ...
    avoid_weekends: boolean;
  };
};

export const DEFAULT_USER_PROFILE: UserProfile = {
  user_id: "default_user",
  budget_limit_lkr: 1000,
  location: "Singapore",
  dietary_needs: {
    vegetarian: false,
    vegan: false,
    gluten_free: false,
    dairy_free: false,
    organic_only: false,
    low_sodium: false,
    sugar_free: false,
    halal: false,
    kosher: false,
    allergies: []
  },
  brand_preferences: {
    preferred_brands: [],
    disliked_brands: [],
    premium_brands_only: false,
    local_brands_priority: false
  },
  household_inventory: {
    current_items: {},
    expiry_dates: {},
    low_stock_threshold: 2
  },
  loyalty_membership: {
    memberships: {},
    points_balance: {},
    preferred_stores: []
  },
  delivery_preferences: {
    max_delivery_time_hours: 24,
    max_delivery_radius_km: 10,
    preferred_time_slots: ["09:00-12:00", "14:00-18:00"],
    avoid_weekends: false
  }
};
