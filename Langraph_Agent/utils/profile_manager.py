"""
User Profile Management Utility
"""
import os
import json
from typing import List, Dict, Any
from core.user_profile import UserProfile, create_sample_profiles, get_default_profile


class UserProfileManager:
    """Manages user profiles and configurations"""
    
    def __init__(self, profiles_dir: str = "user_profiles"):
        self.profiles_dir = profiles_dir
        self.ensure_profiles_directory()
        self.initialize_sample_profiles()
    
    def ensure_profiles_directory(self):
        """Ensure profiles directory exists"""
        if not os.path.exists(self.profiles_dir):
            os.makedirs(self.profiles_dir)
    
    def initialize_sample_profiles(self):
        """Initialize sample profiles if they don't exist"""
        sample_profiles = create_sample_profiles()
        
        for profile in sample_profiles:
            profile_path = os.path.join(self.profiles_dir, f"{profile.user_id}.json")
            if not os.path.exists(profile_path):
                profile.save_to_file(profile_path)
                print(f"Created sample profile: {profile.user_id}")
    
    def list_profiles(self) -> List[str]:
        """List all available user profiles"""
        profiles = []
        for filename in os.listdir(self.profiles_dir):
            if filename.endswith('.json'):
                user_id = filename[:-5]  # Remove .json extension
                profiles.append(user_id)
        return profiles
    
    def load_profile(self, user_id: str) -> UserProfile:
        """Load a specific user profile"""
        profile_path = os.path.join(self.profiles_dir, f"{user_id}.json")
        if os.path.exists(profile_path):
            return UserProfile.load_from_file(profile_path)
        else:
            print(f"Profile {user_id} not found, creating default")
            return self.create_profile(user_id)
    
    def save_profile(self, profile: UserProfile):
        """Save a user profile"""
        profile_path = os.path.join(self.profiles_dir, f"{profile.user_id}.json")
        profile.save_to_file(profile_path)
        print(f"Saved profile: {profile.user_id}")
    
    def create_profile(self, user_id: str) -> UserProfile:
        """Create a new user profile"""
        profile = UserProfile(user_id=user_id)
        self.save_profile(profile)
        return profile
    
    def delete_profile(self, user_id: str) -> bool:
        """Delete a user profile"""
        profile_path = os.path.join(self.profiles_dir, f"{user_id}.json")
        if os.path.exists(profile_path):
            os.remove(profile_path)
            print(f"Deleted profile: {user_id}")
            return True
        return False
    
    def update_profile_budget(self, user_id: str, new_budget: float):
        """Update budget for a user profile"""
        profile = self.load_profile(user_id)
        profile.budget_limit_lkr = new_budget
        self.save_profile(profile)
        print(f"Updated budget for {user_id}: LKR {new_budget}")
    
    def add_dietary_restriction(self, user_id: str, restriction: str, value: bool = True):
        """Add a dietary restriction to user profile"""
        profile = self.load_profile(user_id)
        if hasattr(profile.dietary_needs, restriction):
            setattr(profile.dietary_needs, restriction, value)
            self.save_profile(profile)
            print(f"Updated {restriction} = {value} for {user_id}")
    
    def add_allergy(self, user_id: str, allergy: str):
        """Add an allergy to user profile"""
        profile = self.load_profile(user_id)
        if allergy not in profile.dietary_needs.allergies:
            profile.dietary_needs.allergies.append(allergy)
            self.save_profile(profile)
            print(f"Added allergy '{allergy}' for {user_id}")
    
    def add_preferred_brand(self, user_id: str, brand: str):
        """Add a preferred brand to user profile"""
        profile = self.load_profile(user_id)
        if brand not in profile.brand_preferences.preferred_brands:
            profile.brand_preferences.preferred_brands.append(brand)
            self.save_profile(profile)
            print(f"Added preferred brand '{brand}' for {user_id}")
    
    def add_disliked_brand(self, user_id: str, brand: str):
        """Add a disliked brand to user profile"""
        profile = self.load_profile(user_id)
        if brand not in profile.brand_preferences.disliked_brands:
            profile.brand_preferences.disliked_brands.append(brand)
            self.save_profile(profile)
            print(f"Added disliked brand '{brand}' for {user_id}")
    
    def update_inventory(self, user_id: str, item: str, quantity: int):
        """Update inventory item quantity"""
        profile = self.load_profile(user_id)
        profile.household_inventory.current_items[item] = quantity
        self.save_profile(profile)
        print(f"Updated inventory for {user_id}: {item} = {quantity}")
    
    def add_loyalty_membership(self, user_id: str, store: str, level: str):
        """Add loyalty membership"""
        profile = self.load_profile(user_id)
        profile.loyalty_membership.memberships[store] = level
        if store not in profile.loyalty_membership.preferred_stores:
            profile.loyalty_membership.preferred_stores.append(store)
        self.save_profile(profile)
        print(f"Added loyalty membership for {user_id}: {store} = {level}")
    
    def get_profile_summary(self, user_id: str) -> Dict[str, Any]:
        """Get a summary of user profile"""
        profile = self.load_profile(user_id)
        return {
            "user_id": profile.user_id,
            "budget_limit": profile.budget_limit_lkr,
            "dietary_restrictions": {
                "vegetarian": profile.dietary_needs.vegetarian,
                "vegan": profile.dietary_needs.vegan,
                "dairy_free": profile.dietary_needs.dairy_free,
                "gluten_free": profile.dietary_needs.gluten_free,
                "allergies": profile.dietary_needs.allergies
            },
            "brand_preferences": {
                "preferred": profile.brand_preferences.preferred_brands,
                "disliked": profile.brand_preferences.disliked_brands
            },
            "inventory_items": list(profile.household_inventory.current_items.keys()),
            "loyalty_stores": profile.loyalty_membership.preferred_stores
        }


# Interactive profile customization functions
def interactive_profile_setup(user_id: str = "interactive_user") -> UserProfile:
    """Interactive setup for user profile"""
    manager = UserProfileManager()
    
    print(f"\n🛠️  Setting up profile for: {user_id}")
    print("=" * 50)
    
    # Budget setup
    try:
        budget = float(input("Enter your budget limit (LKR): ") or "5000")
    except ValueError:
        budget = 5000.0
    
    # Dietary needs
    print("\n🥗 Dietary Restrictions (y/n):")
    vegetarian = input("Vegetarian? ").lower().startswith('y')
    vegan = input("Vegan? ").lower().startswith('y')
    dairy_free = input("Dairy-free? ").lower().startswith('y')
    gluten_free = input("Gluten-free? ").lower().startswith('y')
    
    allergies_input = input("Any allergies? (comma-separated): ").strip()
    allergies = [a.strip() for a in allergies_input.split(',') if a.strip()] if allergies_input else []
    
    # Brand preferences
    print("\n🏷️  Brand Preferences:")
    preferred_input = input("Preferred brands (comma-separated): ").strip()
    preferred_brands = [b.strip() for b in preferred_input.split(',') if b.strip()] if preferred_input else []
    
    disliked_input = input("Disliked brands (comma-separated): ").strip()
    disliked_brands = [b.strip() for b in disliked_input.split(',') if b.strip()] if disliked_input else []
    
    # Create and save profile
    from core.user_profile import UserProfile, DietaryNeeds, BrandPreferences
    
    profile = UserProfile(
        user_id=user_id,
        budget_limit_lkr=budget,
        dietary_needs=DietaryNeeds(
            vegetarian=vegetarian,
            vegan=vegan,
            dairy_free=dairy_free,
            gluten_free=gluten_free,
            allergies=allergies
        ),
        brand_preferences=BrandPreferences(
            preferred_brands=preferred_brands,
            disliked_brands=disliked_brands
        )
    )
    
    manager.save_profile(profile)
    print(f"\n✅ Profile created successfully for {user_id}!")
    
    return profile


def print_profile_summary(user_id: str):
    """Print a formatted profile summary"""
    manager = UserProfileManager()
    summary = manager.get_profile_summary(user_id)
    
    print(f"\n👤 Profile Summary: {summary['user_id']}")
    print("=" * 40)
    print(f"💰 Budget Limit: LKR {summary['budget_limit']}")
    
    print(f"\n🥗 Dietary Restrictions:")
    for restriction, value in summary['dietary_restrictions'].items():
        if restriction == 'allergies':
            if value:
                print(f"   Allergies: {', '.join(value)}")
        elif value:
            print(f"   {restriction.replace('_', ' ').title()}: ✓")
    
    print(f"\n🏷️  Brand Preferences:")
    if summary['brand_preferences']['preferred']:
        print(f"   Preferred: {', '.join(summary['brand_preferences']['preferred'])}")
    if summary['brand_preferences']['disliked']:
        print(f"   Disliked: {', '.join(summary['brand_preferences']['disliked'])}")
    
    if summary['inventory_items']:
        print(f"\n📦 Inventory Items: {', '.join(summary['inventory_items'])}")
    
    if summary['loyalty_stores']:
        print(f"\n🏪 Loyalty Stores: {', '.join(summary['loyalty_stores'])}")


if __name__ == "__main__":
    # Demo usage
    manager = UserProfileManager()
    print("Available profiles:", manager.list_profiles())
    
    # Print sample profile summaries
    for profile_id in manager.list_profiles():
        print_profile_summary(profile_id)
