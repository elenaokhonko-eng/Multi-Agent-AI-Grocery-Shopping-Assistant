"""
Personalization Agent with LLM-based filtering and customization tools
"""
import json
from typing import List, Dict, Any, Tuple
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from core.user_profile import UserProfile, get_default_profile
from core.profile_store import UserProfileStore
from core.feedback import PreferenceStore as PrefsStore
from core.profile_sync import augment_profile_from_learned

@tool
def filter_by_budget(items: List[Dict[str, Any]], budget_limit: float) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Filter items based on budget constraints and optimize selection.
    
    Args:
        items: List of product items with price information
        budget_limit: Maximum budget in LKR
        
    Returns:
        Tuple of (filtered_items, budget_summary)
    """
    print(f"[TOOL] Budget Filter - Processing {len(items)} items with budget limit: LKR {budget_limit}")
    
    # Sort items by price (ascending) for budget optimization
    sorted_items = sorted(items, key=lambda x: x.get('price_lkr', 0))
    
    selected_items = []
    total_cost = 0.0
    
    for item in sorted_items:
        item_price = item.get('price_lkr', 0)
        if total_cost + item_price <= budget_limit:
            selected_items.append(item)
            total_cost += item_price
        else:
            break
    
    budget_summary = {
        "total_cost": total_cost,
        "budget_limit": budget_limit,
        "remaining_budget": budget_limit - total_cost,
        "items_selected": len(selected_items),
        "items_excluded": len(items) - len(selected_items)
    }
    
    print(f"[TOOL] Budget Filter - Selected {len(selected_items)} items, Total: LKR {total_cost:.2f}")
    return selected_items, budget_summary


@tool
def filter_by_dietary_needs(items: List[Dict[str, Any]], dietary_restrictions: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Filter items based on dietary needs and restrictions.
    
    Args:
        items: List of product items
        dietary_restrictions: Dictionary of dietary requirements
        
    Returns:
        List of filtered items
    """
    print(f"[TOOL] Dietary Filter - Processing {len(items)} items with restrictions: {dietary_restrictions}")
    
    filtered_items = []
    
    for item in items:
        title = item.get('title', '').lower()
        
        # Check vegetarian restrictions
        if dietary_restrictions.get('vegetarian', False):
            if any(meat in title for meat in ['chicken', 'beef', 'pork', 'fish', 'meat']):
                continue
        
        # Check vegan restrictions
        if dietary_restrictions.get('vegan', False):
            if any(animal_product in title for animal_product in ['milk', 'cheese', 'butter', 'egg', 'honey']):
                continue
        
        # Check dairy-free restrictions
        if dietary_restrictions.get('dairy_free', False):
            if any(dairy in title for dairy in ['milk', 'cheese', 'butter', 'cream', 'yogurt']):
                continue
        
        # Check gluten-free restrictions
        if dietary_restrictions.get('gluten_free', False):
            if any(gluten in title for gluten in ['wheat', 'bread', 'pasta', 'flour']):
                continue
        
        # Check allergies
        allergies = dietary_restrictions.get('allergies', [])
        if any(allergen.lower() in title for allergen in allergies):
            continue
        
        filtered_items.append(item)
    
    print(f"[TOOL] Dietary Filter - {len(filtered_items)} items passed dietary restrictions")
    return filtered_items


@tool
def filter_by_brand_preferences(items: List[Dict[str, Any]], brand_prefs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Filter and prioritize items based on brand preferences.
    
    Args:
        items: List of product items
        brand_prefs: Dictionary of brand preferences
        
    Returns:
        List of filtered and prioritized items
    """
    print(f"[TOOL] Brand Filter - Processing {len(items)} items with preferences: {brand_prefs}")
    
    preferred_brands = [brand.lower() for brand in brand_prefs.get('preferred_brands', [])]
    disliked_brands = [brand.lower() for brand in brand_prefs.get('disliked_brands', [])]
    
    # Filter out disliked brands
    filtered_items = []
    for item in items:
        title = item.get('title', '').lower()
        if not any(disliked_brand in title for disliked_brand in disliked_brands):
            filtered_items.append(item)
    
    # Prioritize preferred brands
    preferred_items = []
    other_items = []
    
    for item in filtered_items:
        title = item.get('title', '').lower()
        if any(preferred_brand in title for preferred_brand in preferred_brands):
            preferred_items.append(item)
        else:
            other_items.append(item)
    
    # Return preferred brands first
    result = preferred_items + other_items
    
    print(f"[TOOL] Brand Filter - {len(preferred_items)} preferred brand items, {len(other_items)} other items")
    return result


@tool
def filter_by_inventory(items: List[Dict[str, Any]], inventory: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Filter items based on current household inventory to avoid duplicates.
    
    Args:
        items: List of product items
        inventory: Dictionary of current inventory
        
    Returns:
        List of filtered items
    """
    print(f"[TOOL] Inventory Filter - Processing {len(items)} items against inventory")
    
    current_items = inventory.get('current_items', {})
    low_stock_threshold = inventory.get('low_stock_threshold', 2)
    
    filtered_items = []
    
    for item in items:
        title = item.get('title', '').lower()
        
        # Check if item is already in sufficient stock
        needs_item = True
        for inv_item, quantity in current_items.items():
            if inv_item.lower() in title:
                if quantity > low_stock_threshold:
                    needs_item = False
                    break
        
        if needs_item:
            filtered_items.append(item)
    
    print(f"[TOOL] Inventory Filter - {len(filtered_items)} items needed (not in sufficient stock)")
    return filtered_items


@tool
def prioritize_by_loyalty(items: List[Dict[str, Any]], loyalty_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Prioritize items based on loyalty memberships and preferred stores.
    
    Args:
        items: List of product items
        loyalty_info: Dictionary of loyalty information
        
    Returns:
        List of prioritized items
    """
    print(f"[TOOL] Loyalty Prioritizer - Processing {len(items)} items with loyalty info")
    
    preferred_stores = [store.lower() for store in loyalty_info.get('preferred_stores', [])]
    memberships = {k.lower(): v for k, v in loyalty_info.get('memberships', {}).items()}
    
    # Categorize items by store priority
    high_priority = []  # Preferred stores with membership
    medium_priority = []  # Preferred stores without membership
    low_priority = []  # Other stores
    
    for item in items:
        website = item.get('website', '').lower()
        collection = item.get('collection', '').lower()
        
        # Check if item is from preferred store with membership
        if any(store in website or store in collection for store in preferred_stores):
            if any(store in memberships for store in preferred_stores if store in website or store in collection):
                high_priority.append(item)
            else:
                medium_priority.append(item)
        else:
            low_priority.append(item)
    
    result = high_priority + medium_priority + low_priority
    
    print(f"[TOOL] Loyalty Prioritizer - {len(high_priority)} high priority, {len(medium_priority)} medium, {len(low_priority)} low")
    return result



class PersonalizationAgent:
    def __init__(self, llm: ChatOllama, user_profile: UserProfile = None,
                 profile_store: UserProfileStore = None,
                 prefs_store: PrefsStore = None):
        self.llm = ChatOllama(base_url=Config.OLLAMA_BASE_URL, model="llama-3.3-70b-versatile", temperature=0.1)
        self.profile_store = profile_store or UserProfileStore(".profiles")
        self.prefs_store   = prefs_store   or PrefsStore(".prefs")
        self.user_profile  = user_profile or get_default_profile()

        self.tools = [
            filter_by_budget,
            filter_by_dietary_needs,
            filter_by_brand_preferences,
            filter_by_inventory,
            prioritize_by_loyalty
        ]
        self.llm_with_tools = self.llm.bind_tools(self.tools)

    def _refresh_profile_from_feedback(self):
        # 1) load persisted profile (if any external edits were made)
        prof = self.profile_store.load(self.user_profile.user_id)
        # 2) load learned preferences
        learned = self.prefs_store.load(self.user_profile.user_id)
        # 3) project learned -> profile fields (brands, stores, delivery)
        prof = augment_profile_from_learned(prof, learned, allow_overwrite=False)
        # 4) save & set active
        self.profile_store.save(prof)
        self.user_profile = prof

    def personalize_items(self, items: List[Dict[str, Any]]):
        # NEW: refresh profile before every run
        self._refresh_profile_from_feedback()

        print(f"[AGENT] Personalization Agent processing {len(items)} items for user: {self.user_profile.user_id}")
        # ... your existing pipeline below (dietary -> brand -> inventory -> loyalty -> budget)
        # unchanged code …
        """
        Personalize items based on user profile using LLM and tools
        
        Args:
            items: List of product items to personalize
            
        Returns:
            Tuple of (personalized_items, personalization_summary)
        """
        print(f"[AGENT] Personalization Agent processing {len(items)} items for user: {self.user_profile.user_id}")
        
        # Create personalization prompt
        prompt = f"""
        You are a Personalization Agent. Personalize the given product items based on the user profile.
        
        User Profile:
        - Budget Limit: LKR {self.user_profile.budget_limit_lkr}
        - Dietary Needs: {self.user_profile.dietary_needs.__dict__}
        - Brand Preferences: {self.user_profile.brand_preferences.__dict__}
        - Household Inventory: {self.user_profile.household_inventory.__dict__}
        - Loyalty Memberships: {self.user_profile.loyalty_membership.__dict__}
        
        Items to personalize: {len(items)} products
        
        Please use the available tools to:
        1. Filter by dietary restrictions
        2. Filter by brand preferences
        3. Check against household inventory
        4. Prioritize by loyalty memberships
        5. Finally, apply budget constraints
        
        Apply the filters in the most logical order and return the final personalized selection.
        """
        
        try:
            current_items = items.copy()
            personalization_steps = []
            
            # Step 1: Filter by dietary needs
            if any([
                self.user_profile.dietary_needs.vegetarian,
                self.user_profile.dietary_needs.vegan,
                self.user_profile.dietary_needs.dairy_free,
                self.user_profile.dietary_needs.gluten_free,
                len(self.user_profile.dietary_needs.allergies) > 0
            ]):
                current_items = filter_by_dietary_needs.invoke({
                    "items": current_items,
                    "dietary_restrictions": self.user_profile.dietary_needs.__dict__
                })
                personalization_steps.append(f"Dietary filter: {len(current_items)} items remaining")
            
            # Step 2: Filter by brand preferences
            if (len(self.user_profile.brand_preferences.preferred_brands) > 0 or 
                len(self.user_profile.brand_preferences.disliked_brands) > 0):
                current_items = filter_by_brand_preferences.invoke({
                    "items": current_items,
                    "brand_prefs": self.user_profile.brand_preferences.__dict__
                })
                personalization_steps.append(f"Brand filter: {len(current_items)} items remaining")
            
            # Step 3: Filter by inventory
            if len(self.user_profile.household_inventory.current_items) > 0:
                current_items = filter_by_inventory.invoke({
                    "items": current_items,
                    "inventory": self.user_profile.household_inventory.__dict__
                })
                personalization_steps.append(f"Inventory filter: {len(current_items)} items remaining")
            
            # Step 4: Prioritize by loyalty
            if len(self.user_profile.loyalty_membership.preferred_stores) > 0:
                current_items = prioritize_by_loyalty.invoke({
                    "items": current_items,
                    "loyalty_info": self.user_profile.loyalty_membership.__dict__
                })
                personalization_steps.append(f"Loyalty prioritization applied")
            
            # Step 5: Apply budget constraints
            final_items, budget_summary = filter_by_budget.invoke({
                "items": current_items,
                "budget_limit": self.user_profile.budget_limit_lkr
            })
            personalization_steps.append(f"Budget filter: {len(final_items)} items within budget")
            
            personalization_summary = {
                "original_items_count": len(items),
                "final_items_count": len(final_items),
                "personalization_steps": personalization_steps,
                "budget_summary": budget_summary,
                "user_profile_applied": self.user_profile.user_id
            }
            
            print(f"[AGENT] Personalization completed: {len(items)} → {len(final_items)} items")
            return final_items, personalization_summary
            
        except Exception as e:
            print(f"[AGENT] Error in personalization: {e}")
            # Fallback: just apply budget filter
            final_items, budget_summary = filter_by_budget.invoke({
                "items": items,
                "budget_limit": self.user_profile.budget_limit_lkr
            })
            
            personalization_summary = {
                "original_items_count": len(items),
                "final_items_count": len(final_items),
                "personalization_steps": ["Error occurred, applied budget filter only"],
                "budget_summary": budget_summary,
                "error": str(e)
            }
            
            return final_items, personalization_summary
    
    def update_user_profile(self, new_profile: UserProfile):
        """Update the user profile"""
        self.user_profile = new_profile
        print(f"[AGENT] User profile updated for: {self.user_profile.user_id}")
    
    def get_personalization_summary(self) -> Dict[str, Any]:
        """Get a summary of current personalization settings"""
        return {
            "user_id": self.user_profile.user_id,
            "budget_limit": self.user_profile.budget_limit_lkr,
            "dietary_restrictions_active": any([
                self.user_profile.dietary_needs.vegetarian,
                self.user_profile.dietary_needs.vegan,
                self.user_profile.dietary_needs.dairy_free,
                self.user_profile.dietary_needs.gluten_free,
                len(self.user_profile.dietary_needs.allergies) > 0
            ]),
            "brand_preferences_count": len(self.user_profile.brand_preferences.preferred_brands),
            "disliked_brands_count": len(self.user_profile.brand_preferences.disliked_brands),
            "inventory_items_count": len(self.user_profile.household_inventory.current_items),
            "loyalty_stores_count": len(self.user_profile.loyalty_membership.preferred_stores)
        }
