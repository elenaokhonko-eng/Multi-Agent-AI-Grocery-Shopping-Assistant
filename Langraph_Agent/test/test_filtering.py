#!/usr/bin/env python3
"""
Test script for the new logistics filtering functionality
"""
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import ProductSearchOrchestrator
from core.user_profile import UserProfile, DietaryNeeds, BrandPreferences

def test_logistics_filtering():
    """Test the logistics filtering functionality"""
    print("🧪 TESTING LOGISTICS FILTERING")
    print("=" * 60)
    
    # Create a user profile with Galle location (should filter distant stores)
    test_profile = UserProfile(
        user_id="filtering_test_user",
        budget_limit_lkr=2000.0,
        location="Galle, Sri Lanka",  # Southern city - should filter out distant stores
        dietary_needs=DietaryNeeds(
            vegetarian=True,
            organic_only=True
        ),
        brand_preferences=BrandPreferences(
            preferred_brands=['Prima', 'Anchor']
        )
    )
    
    # Initialize orchestrator with 25km threshold for demo
    orchestrator = ProductSearchOrchestrator(test_profile)
    
    # Temporarily override the distance threshold in logistics agent filtering
    original_filter = orchestrator.logistics_agent.filter_by_distance
    
    def filter_with_25km_threshold(user_location, personalized_data, max_distance_km=25.0):
        """Override to use 25km threshold"""
        return original_filter(user_location, personalized_data, 25.0)
    
    orchestrator.logistics_agent.filter_by_distance = filter_with_25km_threshold
    
    # Test query for multiple categories
    test_query = "I need rice, coconut oil, and tea for my family"
    
    print(f"🔍 User Query: '{test_query}'")
    print(f"📍 User Location: {test_profile.location}")
    print(f"💰 Budget Limit: LKR {test_profile.budget_limit_lkr}")
    print(f"📏 Distance Threshold: 25km (for demo)")
    print()
    
    # Process the query
    print("🚀 Processing with Logistics Filtering...")
    print("=" * 60)
    
    result = orchestrator.process_query(test_query)
    
    # Display results
    print("\n✅ Processing Complete!")
    print("=" * 60)
    
    # Show filtering statistics
    logistics_summary = result.get("logistics_filtering_summary", {})
    if logistics_summary and not logistics_summary.get("error"):
        print("\n📊 FILTERING STATISTICS:")
        print(f"   Items Before: {logistics_summary.get('items_before_filtering', 0)}")
        print(f"   Items After: {logistics_summary.get('items_after_filtering', 0)}")
        print(f"   Items Removed: {logistics_summary.get('items_removed', 0)}")
        print(f"   Distance Threshold: {logistics_summary.get('distance_threshold_km', 25)}km")
        print(f"   Categories Filtered: {logistics_summary.get('categories_filtered', 0)}")
        print(f"   Single-Item Categories: {logistics_summary.get('single_item_categories_kept', 0)}")
    
    # Show final stage
    print(f"\n🏁 Final Stage: {result.get('processing_stage', 'Unknown')}")
    
    return result

if __name__ == "__main__":
    test_logistics_filtering()
