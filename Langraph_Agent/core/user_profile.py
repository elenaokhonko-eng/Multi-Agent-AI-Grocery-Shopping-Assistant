"""
User Profile Configuration
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import os


@dataclass
class DeliveryPreferences:
    """User delivery preferences"""
    max_delivery_time_hours: int = 24
    max_delivery_radius_km: int = 10
    preferred_time_slots: List[str] = None
    avoid_weekends: bool = False
    
    def __post_init__(self):
        if self.preferred_time_slots is None:
            self.preferred_time_slots = ["09:00-12:00", "14:00-18:00"]


@dataclass
class DietaryNeeds:
    """User dietary requirements and restrictions"""
    vegetarian: bool = False
    vegan: bool = False
    gluten_free: bool = False
    dairy_free: bool = False
    organic_only: bool = False
    low_sodium: bool = False
    sugar_free: bool = False
    halal: bool = False
    kosher: bool = False
    allergies: List[str] = None
    
    def __post_init__(self):
        if self.allergies is None:
            self.allergies = []


@dataclass
class BrandPreferences:
    """User brand preferences and dislikes"""
    preferred_brands: List[str] = None
    disliked_brands: List[str] = None
    premium_brands_only: bool = False
    local_brands_priority: bool = False
    
    def __post_init__(self):
        if self.preferred_brands is None:
            self.preferred_brands = []
        if self.disliked_brands is None:
            self.disliked_brands = []


@dataclass
class HouseholdInventory:
    """Current household inventory to avoid duplicates"""
    current_items: Dict[str, int] = None  # item_name: quantity
    expiry_dates: Dict[str, str] = None   # item_name: expiry_date
    low_stock_threshold: int = 2
    
    def __post_init__(self):
        if self.current_items is None:
            self.current_items = {}
        if self.expiry_dates is None:
            self.expiry_dates = {}


@dataclass
class LoyaltyMembership:
    """User loyalty program memberships"""
    memberships: Dict[str, str] = None  # store_name: membership_level
    points_balance: Dict[str, int] = None  # store_name: points
    preferred_stores: List[str] = None
    
    def __post_init__(self):
        if self.memberships is None:
            self.memberships = {}
        if self.points_balance is None:
            self.points_balance = {}
        if self.preferred_stores is None:
            self.preferred_stores = []


@dataclass
class UserProfile:
    """Complete user profile with all preferences"""
    user_id: str
    budget_limit_lkr: float = 1000.0
    location: str = "Singapore"  # Default location
    dietary_needs: DietaryNeeds = None
    brand_preferences: BrandPreferences = None
    household_inventory: HouseholdInventory = None
    loyalty_membership: LoyaltyMembership = None
    delivery_preferences: DeliveryPreferences = None
    
    def __post_init__(self):
        if self.dietary_needs is None:
            self.dietary_needs = DietaryNeeds()
        if self.brand_preferences is None:
            self.brand_preferences = BrandPreferences()
        if self.household_inventory is None:
            self.household_inventory = HouseholdInventory()
        if self.loyalty_membership is None:
            self.loyalty_membership = LoyaltyMembership()
        if self.delivery_preferences is None:
            self.delivery_preferences = DeliveryPreferences()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """Create profile from dictionary"""
        # Handle nested dataclasses
        if 'dietary_needs' in data and isinstance(data['dietary_needs'], dict):
            data['dietary_needs'] = DietaryNeeds(**data['dietary_needs'])
        if 'brand_preferences' in data and isinstance(data['brand_preferences'], dict):
            data['brand_preferences'] = BrandPreferences(**data['brand_preferences'])
        if 'household_inventory' in data and isinstance(data['household_inventory'], dict):
            data['household_inventory'] = HouseholdInventory(**data['household_inventory'])
        if 'loyalty_membership' in data and isinstance(data['loyalty_membership'], dict):
            data['loyalty_membership'] = LoyaltyMembership(**data['loyalty_membership'])
        if 'delivery_preferences' in data and isinstance(data['delivery_preferences'], dict):
            data['delivery_preferences'] = DeliveryPreferences(**data['delivery_preferences'])
        
        return cls(**data)
    
    def save_to_file(self, filepath: str):
        """Save profile to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'UserProfile':
        """Load profile from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


# Sample user profiles for testing
def create_sample_profiles():
    """Create sample user profiles"""
    
    # Sample Profile 1: Health-conscious user
    profile1 = UserProfile(
        user_id="user_001",
        budget_limit_lkr=3000.0,
        dietary_needs=DietaryNeeds(
            vegetarian=True,
            organic_only=True,
            allergies=["nuts", "shellfish"]
        ),
        brand_preferences=BrandPreferences(
            preferred_brands=["Nestle", "Anchor", "Maliban"],
            disliked_brands=["Generic Brand"],
            premium_brands_only=True
        ),
        household_inventory=HouseholdInventory(
            current_items={"milk": 2, "bread": 1},
            low_stock_threshold=1
        ),
        loyalty_membership=LoyaltyMembership(
            memberships={"kapruka": "gold", "glowmark": "silver"},
            preferred_stores=["kapruka", "glowmark"]
        )
    )
    
    # Sample Profile 2: Budget-conscious family
    profile2 = UserProfile(
        user_id="user_002",
        budget_limit_lkr=1500.0,
        dietary_needs=DietaryNeeds(
            dairy_free=True,
            allergies=["gluten"]
        ),
        brand_preferences=BrandPreferences(
            preferred_brands=["Milo", "Nestomalt"],
            local_brands_priority=True
        ),
        household_inventory=HouseholdInventory(
            current_items={"rice": 5, "tea": 3},
            low_stock_threshold=2
        ),
        loyalty_membership=LoyaltyMembership(
            memberships={"onlinekade": "bronze"},
            preferred_stores=["onlinekade"]
        )
    )
    
    return [profile1, profile2]


# Default configuration paths
DEFAULT_PROFILES_DIR = "user_profiles"
DEFAULT_PROFILE_PATH = os.path.join(DEFAULT_PROFILES_DIR, "default_user.json")


def ensure_profiles_directory():
    """Ensure user profiles directory exists"""
    if not os.path.exists(DEFAULT_PROFILES_DIR):
        os.makedirs(DEFAULT_PROFILES_DIR)


def get_default_profile() -> UserProfile:
    """Get or create default user profile"""
    ensure_profiles_directory()
    
    if os.path.exists(DEFAULT_PROFILE_PATH):
        return UserProfile.load_from_file(DEFAULT_PROFILE_PATH)
    else:
        # Create default profile
        default_profile = UserProfile(user_id="default_user")
        default_profile.save_to_file(DEFAULT_PROFILE_PATH)
        return default_profile
