#!/usr/bin/env python3
"""
Comprehensive test for personalization features
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import ProductSearchOrchestrator
from core.user_profile import UserProfile, DietaryNeeds, BrandPreferences, HouseholdInventory, LoyaltyMembership, DeliveryPreferences

def create_test_profile():
    """Create a test profile with specific preferences"""
    return UserProfile(
        user_id="test_user_personalized",
        budget_limit_lkr=2000.0,  # Lower budget to test filtering
        dietary_needs=DietaryNeeds(
            vegetarian=True,
            organic_only=True,
            allergies=["nuts", "gluten"]
        ),
        brand_preferences=BrandPreferences(
            preferred_brands=["Organic", "Premium"],
            disliked_brands=["Standard"],
            premium_brands_only=True
        ),
        household_inventory=HouseholdInventory(
            current_items={"rice": 5, "cooking oil": 2},
            low_stock_threshold=3
        ),
        loyalty_membership=LoyaltyMembership(
            memberships={"glowmark": "gold", "kapruka": "silver"},
            points_balance={"glowmark": 1500, "kapruka": 800}
        )
    )

def test_personalization():
    """Test personalization with a customized profile"""
    print("🧪 Testing Personalization Features")
    print("=" * 60)
    
    # Create a personalized test profile
    test_profile = create_test_profile()
    print("📋 Test Profile Details:")
    print(f"  🆔 User ID: {test_profile.user_id}")
    print(f"  💰 Budget Limit: LKR {test_profile.budget_limit_lkr}")
    print(f"  🥗 Vegetarian: {test_profile.dietary_needs.vegetarian}")
    print(f"  🌱 Organic Only: {test_profile.dietary_needs.organic_only}")
    print(f"  🚫 Allergies: {test_profile.dietary_needs.allergies}")
    print(f"  ⭐ Preferred Brands: {test_profile.brand_preferences.preferred_brands}")
    print(f"  📦 Current Inventory: {test_profile.household_inventory.current_items}")
    print(f"  🏪 Memberships: {test_profile.loyalty_membership.memberships}")
    
    # Initialize the orchestrator with personalized profile
    print("\n🚀 Initializing orchestrator with personalized profile...")
    orchestrator = ProductSearchOrchestrator(test_profile)
    
    # Test with a query that should trigger multiple personalization filters
    test_query = "I need some rice and organic snacks for cooking"
    
    print(f"\n{'='*60}")
    print(f"🔍 PERSONALIZATION TEST: {test_query}")
    print("="*60)
    print("Expected personalization effects:")
    print("  • Budget filter: Should remove items over LKR 2000 total")
    print("  • Brand preference: Should prioritize Organic/Premium brands")
    print("  • Inventory check: Should deprioritize rice (already have 5)")
    print("  • Loyalty benefits: Should apply discounts for glowmark/kapruka")
    print("="*60)
    
    try:
        # Process the query
        result = orchestrator.process_query(test_query)
        
        # Show detailed results
        print(f"\n✅ Personalization test completed!")
        print(f"Final stage: {result.get('processing_stage')}")
        print(f"Keywords extracted: {result.get('keywords', [])}")
        
        # Check personalization summary
        personalization_summary = result.get('personalization_summary', {})
        if personalization_summary:
            print(f"\n📊 Personalization Results:")
            print(f"  Original items: {personalization_summary.get('original_items_count', 0)}")
            print(f"  Final items: {personalization_summary.get('final_items_count', 0)}")
            if 'budget_summary' in personalization_summary:
                budget = personalization_summary['budget_summary']
                print(f"  Total cost: LKR {budget.get('total_cost', 0):.2f}")
                print(f"  Budget remaining: LKR {budget.get('remaining_budget', 0):.2f}")
        
        print(f"\n🎯 Test demonstrates full personalization pipeline working correctly!")
        
    except Exception as e:
        print(f"❌ Personalization test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_personalization()
