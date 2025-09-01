"""
Simple demonstration of the complete Langraph pipeline with Logistics Agent
"""
import sys
import os

# Add the parent directory to Python path
sys.path.append('/Users/yasiru/Documents/GitHub/Tensor-Titans-SLAIC-2025-Working/Langraph_Agent')

from main import ProductSearchOrchestrator
from core.user_profile import UserProfile, DietaryNeeds, BrandPreferences, LoyaltyMembership


def demo_complete_pipeline():
    """Demonstrate the complete pipeline with all features"""
    
    print("🚀 LANGRAPH + PERSONALIZATION + LOGISTICS DEMO")
    print("="*70)
    
    # Create a user profile with location for logistics
    user_profile = UserProfile(
        user_id="demo_user",
        budget_limit_lkr=3000.0,
        location="Galle, Sri Lanka",  # Specific location for logistics
        dietary_needs=DietaryNeeds(
            organic_only=True,
            vegetarian=True
        ),
        brand_preferences=BrandPreferences(
            preferred_brands=["Prima", "Anchor"]
        ),
        loyalty_membership=LoyaltyMembership(
            memberships={"keells": "gold"}
        )
    )
    
    # Initialize orchestrator
    orchestrator = ProductSearchOrchestrator(user_profile=user_profile)
    
    # Test query
    query = "I need organic rice, coconut oil, and tea for my family"
    print(f"🔍 User Query: '{query}'")
    print(f"📍 User Location: {user_profile.location}")
    print(f"💰 Budget Limit: LKR {user_profile.budget_limit_lkr}")
    print(f"🥗 Dietary Needs: Organic only, Vegetarian")
    print(f"🏷️ Preferred Brands: {user_profile.brand_preferences.preferred_brands}")
    print("\n" + "="*70)
    
    # Process the query through the complete pipeline
    result = orchestrator.process_query(query)
    
    print(f"\n✅ Pipeline completed: {result.get('processing_stage')}")
    print("="*70)
    
    # Show key metrics
    if 'personalization_summary' in result:
        summary = result['personalization_summary']
        print(f"📊 PIPELINE METRICS:")
        print(f"   Original Items Found: {summary.get('original_items_count', 0)}")
        print(f"   Items After Personalization: {summary.get('final_items_count', 0)}")
        print(f"   Keywords Processed: {len(summary.get('keywords_processed', []))}")
        print(f"   Total Cost: LKR {summary.get('budget_summary', {}).get('total_cost', 0):.2f}")
        print(f"   Remaining Budget: LKR {summary.get('budget_summary', {}).get('remaining_budget', 0):.2f}")
    
    if 'logistics_summary' in result and not result['logistics_summary'].get('error'):
        logistics = result['logistics_summary'].get('delivery_summary', {})
        print(f"\n🚚 LOGISTICS OPTIMIZATION:")
        print(f"   Recommended Store: {logistics.get('recommended_store', 'N/A')}")
        print(f"   Distance: {logistics.get('distance_km', 0):.1f} km")
        print(f"   Delivery Charge: LKR {logistics.get('delivery_charge_lkr', 0):.2f}")
        print(f"   Estimated Delivery: {logistics.get('estimated_hours', 0):.1f} hours")
        print(f"   Total with Delivery: LKR {logistics.get('total_cost_with_delivery', 0):.2f}")
    
    print("\n🎉 DEMO COMPLETED!")
    print("="*70)


if __name__ == "__main__":
    demo_complete_pipeline()
