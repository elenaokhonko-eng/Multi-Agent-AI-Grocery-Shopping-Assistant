"""
Test script for the complete Langraph pipeline with Logistics Agent
"""
import sys
import os

# Add the parent directory to Python path
sys.path.append('/Users/yasiru/Documents/GitHub/Tensor-Titans-SLAIC-2025-Working/Langraph_Agent')

from main import ProductSearchOrchestrator
from core.user_profile import UserProfile
from utils.location_utils import parse_user_location


def test_basic_query():
    """Test basic query without personalization"""
    print("🔍 TESTING: Basic Query - 'I need organic rice and coconut oil'")
    print("="*80)
    
    orchestrator = ProductSearchOrchestrator()
    result = orchestrator.process_query("I need organic rice and coconut oil")
    
    print(f"\n✅ Processing completed: {result.get('processing_stage')}")
    return result


def test_personalized_query():
    """Test query with personalized user profile"""
    print("\n🔍 TESTING: Personalized Query with Budget Constraints")
    print("="*80)
    
    # Create a custom user profile using the proper nested structure
    from core.user_profile import UserProfile, DietaryNeeds, BrandPreferences, LoyaltyMembership
    
    custom_profile = UserProfile(
        user_id="test_user_budget",
        budget_limit_lkr=2000.0,  # Low budget
        dietary_needs=DietaryNeeds(
            organic_only=True,
            gluten_free=True
        ),
        brand_preferences=BrandPreferences(
            preferred_brands=["Prima"]
        ),
        loyalty_membership=LoyaltyMembership(
            memberships={"keells": "gold"}
        )
    )
    
    orchestrator = ProductSearchOrchestrator(user_profile=custom_profile)
    result = orchestrator.process_query("I want to buy rice, oil, and some snacks")
    
    print(f"\n✅ Personalized processing completed: {result.get('processing_stage')}")
    return result


def test_logistics_with_location():
    """Test logistics optimization with specific location"""
    print("\n🔍 TESTING: Logistics Optimization with Specific Location")
    print("="*80)
    
    from core.user_profile import UserProfile, DietaryNeeds, BrandPreferences, LoyaltyMembership, DeliveryPreferences
    
    # Create profile with specific location preferences
    custom_profile = UserProfile(
        user_id="test_user_galle",
        budget_limit_lkr=5000.0,
        location="Galle, Sri Lanka",  # Specific location for logistics
        dietary_needs=DietaryNeeds(organic_only=True),
        brand_preferences=BrandPreferences(
            preferred_brands=["Prima", "Anchor"]
        ),
        loyalty_membership=LoyaltyMembership(
            memberships={"keells": "silver"}
        ),
        delivery_preferences=DeliveryPreferences(
            max_delivery_time_hours=6,
            max_delivery_radius_km=15
        )
    )
    
    orchestrator = ProductSearchOrchestrator(user_profile=custom_profile)
    result = orchestrator.process_query("I need rice, coconut oil, and tea leaves for my family")
    
    print(f"\n✅ Logistics optimization completed: {result.get('processing_stage')}")
    return result


def test_multi_keyword_logistics():
    """Test logistics with multiple product categories"""
    print("\n🔍 TESTING: Multi-Category Logistics Optimization")
    print("="*80)
    
    from core.user_profile import UserProfile, DietaryNeeds, BrandPreferences, LoyaltyMembership
    
    # Create profile in Colombo (should have many delivery options)
    custom_profile = UserProfile(
        user_id="test_user_colombo",
        budget_limit_lkr=8000.0,
        location="Colombo, Sri Lanka",  # Colombo location
        dietary_needs=DietaryNeeds(
            organic_only=True,
            vegetarian=True
        ),
        brand_preferences=BrandPreferences(
            preferred_brands=["Prima", "Anchor", "MD"]
        ),
        loyalty_membership=LoyaltyMembership(
            memberships={"keells": "platinum", "cargills": "gold"}
        )
    )
    
    orchestrator = ProductSearchOrchestrator(user_profile=custom_profile)
    result = orchestrator.process_query("I need rice, cooking oil, spices, tea, and some healthy snacks")
    
    print(f"\n✅ Multi-category logistics completed: {result.get('processing_stage')}")
    return result


def test_coordinate_based_location():
    """Test with coordinate-based location input"""
    print("\n🔍 TESTING: Coordinate-Based Location")
    print("="*80)
    
    from core.user_profile import UserProfile, DietaryNeeds, BrandPreferences, LoyaltyMembership
    
    # Test with coordinates
    location = parse_user_location("7.2906, 80.6337")  # Kandy coordinates
    print(f"📍 Parsed location: {location.city if location else 'Failed to parse'}")
    
    if location:
        custom_profile = UserProfile(
            user_id="test_user_coords",
            budget_limit_lkr=3000.0,
            location="7.2906, 80.6337",  # Kandy coordinates
            dietary_needs=DietaryNeeds(organic_only=True),
            brand_preferences=BrandPreferences(
                preferred_brands=["Prima"]
            ),
            loyalty_membership=LoyaltyMembership(
                memberships={"keells": "silver"}
            )
        )
        
        orchestrator = ProductSearchOrchestrator(user_profile=custom_profile)
        result = orchestrator.process_query("I want organic rice and oil")
        
        print(f"\n✅ Coordinate-based logistics completed: {result.get('processing_stage')}")
        return result
    else:
        print("❌ Failed to parse coordinates")
        return None


def run_all_tests():
    """Run all test scenarios"""
    print("🚀 STARTING COMPLETE LANGRAPH + LOGISTICS PIPELINE TESTS")
    print("="*80)
    
    try:
        # Test 1: Basic functionality
        test_basic_query()
        
        # Test 2: Personalization
        test_personalized_query()
        
        # Test 3: Logistics with location
        test_logistics_with_location()
        
        # Test 4: Multi-category logistics
        test_multi_keyword_logistics()
        
        # Test 5: Coordinate-based location
        test_coordinate_based_location()
        
        print("\n" + "="*80)
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
