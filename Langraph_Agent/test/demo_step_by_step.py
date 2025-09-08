#!/usr/bin/env python3
"""
Demo script showing step-by-step pipeline execution with detailed item tracking
"""

from main import ProductSearchOrchestrator
from core.user_profile import UserProfile, DietaryNeeds, BrandPreferences, LoyaltyMembership

def demo_step_by_step():
    """Run a step-by-step demo with detailed logging"""
    
    print("🛒 LANGRAPH AGENT - STEP-BY-STEP DEMO")
    print("=" * 80)
    
    # Create a custom user profile for demonstration
    custom_profile = UserProfile(
        user_id="demo_user",
        budget_limit_lkr=3000.0,  # Lower budget to show optimization
        dietary_needs=DietaryNeeds(
            organic_only=True,
            vegetarian=True
        ),
        brand_preferences=BrandPreferences(
            preferred_brands=["Prima", "Anchor"]
        ),
        loyalty_membership=LoyaltyMembership(
            memberships={"keells": "gold", "cargills": "silver"}
        )
    )
    
    # Initialize orchestrator
    orchestrator = ProductSearchOrchestrator(user_profile=custom_profile)
    
    print(f"\n🎯 USER PROFILE:")
    print(f"   User ID: {custom_profile.user_id}")
    print(f"   Budget Limit: LKR {custom_profile.budget_limit_lkr}")
    print(f"   Dietary Needs: Organic={custom_profile.dietary_needs.organic_only}, Vegetarian={custom_profile.dietary_needs.vegetarian}")
    print(f"   Preferred Brands: {custom_profile.brand_preferences.preferred_brands}")
    print(f"   Loyalty Memberships: {dict(custom_profile.loyalty_membership.memberships)}")
    
    print("\n" + "=" * 80)
    print("🚀 PROCESSING QUERY: 'I need rice, cooking oil, and some healthy snacks'")
    print("=" * 80)
    
    # Process the query
    result = orchestrator.process_query("I need rice, cooking oil, and some healthy snacks")
    
    print("\n" + "=" * 80)
    print("✅ PIPELINE EXECUTION COMPLETED!")
    print("=" * 80)
    print(f"Final Processing Stage: {result.get('processing_stage')}")
    
    # Summary statistics
    print(f"\n📊 EXECUTION SUMMARY:")
    print(f"   • Keywords Extracted: {len(result.get('keywords', []))}")
    print(f"   • Categories Processed: {len(result.get('product_data', {}))}")
    print(f"   • Items After Personalization: {sum(len(items) for items in result.get('personalized_data', {}).values())}")
    print(f"   • Final Optimized Items: {len(result.get('budget_optimized_data', {}))}")
    
    budget_summary = result.get('budget_optimization_summary', {})
    if budget_summary:
        selection_summary = budget_summary.get('selection_summary', {})
        print(f"   • Total Cost: LKR {selection_summary.get('total_cost', 0):.2f}")
        print(f"   • Budget Utilization: {selection_summary.get('budget_utilization', 0):.1f}%")
        print(f"   • Delivery Time: {selection_summary.get('estimated_delivery_time', 0):.1f} hours")

if __name__ == "__main__":
    demo_step_by_step()
