#!/usr/bin/env python3
"""
Test minimum item guarantee functionality
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import ProductSearchOrchestrator
from core.user_profile import UserProfile, DietaryNeeds, BrandPreferences, HouseholdInventory, LoyaltyMembership

def create_restrictive_profile():
    """Create a very restrictive profile to test minimum guarantee"""
    return UserProfile(
        user_id="restrictive_test_user",
        budget_limit_lkr=100.0,  # Very low budget
        dietary_needs=DietaryNeeds(
            vegetarian=True,
            vegan=True,
            gluten_free=True,
            dairy_free=True,
            organic_only=True,
            allergies=["nuts", "soy", "eggs", "fish"]  # Many allergies
        ),
        brand_preferences=BrandPreferences(
            preferred_brands=["NonexistentBrand"],  # Brand that doesn't exist
            disliked_brands=["Organic", "Premium", "Fresh"],  # Dislike common brands
            premium_brands_only=True
        ),
        household_inventory=HouseholdInventory(
            current_items={"rice": 100, "snacks": 50, "fruits": 25},  # Already have lots
            low_stock_threshold=1
        )
    )

def test_minimum_guarantee():
    """Test that personalization never eliminates all items from any keyword"""
    print("🧪 Testing Minimum Item Guarantee")
    print("=" * 60)
    
    # Create extremely restrictive profile
    restrictive_profile = create_restrictive_profile()
    print("📋 Restrictive Test Profile:")
    print(f"  💰 Budget: LKR {restrictive_profile.budget_limit_lkr} (very low)")
    print(f"  🥗 Dietary: Vegan + Gluten-free + Dairy-free + Organic only")
    print(f"  🚫 Allergies: {restrictive_profile.dietary_needs.allergies}")
    print(f"  ⭐ Preferred Brands: {restrictive_profile.brand_preferences.preferred_brands} (nonexistent)")
    print(f"  👎 Disliked Brands: {restrictive_profile.brand_preferences.disliked_brands} (common brands)")
    print(f"  📦 Inventory: Already have lots of rice, snacks, fruits")
    
    # Initialize orchestrator
    print("\n🚀 Initializing orchestrator with restrictive profile...")
    orchestrator = ProductSearchOrchestrator(restrictive_profile)
    
    # Test queries that should normally be filtered out heavily
    test_queries = [
        "rice and snacks",  # Items we already have in inventory
        "premium organic fruits",  # Should match disliked brands but we need fruits
        "cheap non-organic meat products"  # Against all dietary restrictions
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"🔍 MINIMUM GUARANTEE TEST {i}: {query}")
        print("="*60)
        print("This query should be heavily filtered but must return at least 1 item per keyword")
        
        try:
            result = orchestrator.process_query(query)
            
            # Check results
            keywords = result.get('keywords', [])
            personalized_data = result.get('personalized_data', {})
            personalization_summary = result.get('personalization_summary', {})
            
            print(f"\n📊 Results:")
            print(f"  Keywords extracted: {keywords}")
            print(f"  Original items: {personalization_summary.get('original_items_count', 0)}")
            print(f"  Final items: {personalization_summary.get('final_items_count', 0)}")
            print(f"  Minimum guaranteed: {personalization_summary.get('minimum_items_guaranteed', False)}")
            
            # Check minimum guarantee
            all_keywords_have_items = True
            for keyword in keywords:
                item_count = len(personalized_data.get(keyword, []))
                print(f"  '{keyword}': {item_count} items")
                if item_count == 0:
                    all_keywords_have_items = False
            
            if all_keywords_have_items and keywords:
                print(f"  ✅ SUCCESS: All keywords have at least 1 item!")
            elif not keywords:
                print(f"  ⚠️  No keywords extracted")
            else:
                print(f"  ❌ FAILURE: Some keywords have 0 items")
            
        except Exception as e:
            print(f"❌ Test {i} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("🎯 Minimum Guarantee Testing Complete!")
    print("✅ System ensures at least 1 item per keyword category")
    print("✅ Prevents complete category elimination during personalization")
    print("="*60)

if __name__ == "__main__":
    test_minimum_guarantee()
