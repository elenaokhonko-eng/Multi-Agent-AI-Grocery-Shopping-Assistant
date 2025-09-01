"""
Demo script to showcase the full pipeline with real discount triggers
"""
import os
import sys

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config import Config
os.environ["GROQ_API_KEY"] = Config.GROQ_API_KEY

from main import ProductSearchOrchestrator
from core.user_profile import get_default_profile


def demo_full_pipeline():
    """Demo the complete pipeline with discount optimization"""
    
    print("🎯 FULL PIPELINE DEMO WITH LOYALTY OPTIMIZATION")
    print("=" * 70)
    
    # Create a user profile with higher budget to trigger more discounts
    test_profile = get_default_profile()
    test_profile.budget_limit_lkr = 15000.0  # Higher budget
    
    print(f"👤 User Profile: {test_profile.user_id}")
    print(f"💰 Budget: LKR {test_profile.budget_limit_lkr}")
    print(f"🏠 Location: {getattr(test_profile, 'location', 'Default (Colombo)')}")
    
    # Initialize orchestrator
    orchestrator = ProductSearchOrchestrator(test_profile)
    
    # Test with a comprehensive shopping list
    test_query = "I need organic rice, coconut oil, tea, coffee, and household items for my family"
    
    print(f"\n🛒 Shopping Query: '{test_query}'")
    print("-" * 70)
    
    try:
        # Process the query
        result = orchestrator.process_query(test_query)
        
        print("\n" + "=" * 70)
        print("🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        
        # Extract key metrics
        personalization_summary = result.get('personalization_summary', {})
        loyalty_summary = result.get('loyalty_summary', {})
        logistics_summary = result.get('logistics_summary', {})
        
        print(f"📊 PIPELINE METRICS:")
        print(f"  • Processing Stage: {result.get('processing_stage')}")
        print(f"  • Original Items: {personalization_summary.get('original_items_count', 0)}")
        print(f"  • Final Items: {personalization_summary.get('final_items_count', 0)}")
        print(f"  • Total Cost: LKR {personalization_summary.get('budget_summary', {}).get('total_cost', 0):.2f}")
        print(f"  • Loyalty Savings: LKR {loyalty_summary.get('total_savings', 0):.2f}")
        print(f"  • Stores Analyzed: {loyalty_summary.get('stores_analyzed', 0)}")
        
        if loyalty_summary.get('total_savings', 0) > 0:
            print(f"  • Savings Percentage: {loyalty_summary.get('savings_percentage', 0)}%")
            print(f"  • Best Store: {loyalty_summary.get('optimization_summary', {}).get('best_store_for_savings', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def demo_with_galle_location():
    """Demo with Galle location to test distance filtering"""
    
    print("\n🌴 GALLE LOCATION DEMO")
    print("=" * 70)
    
    # Create a profile with Galle location
    test_profile = get_default_profile()
    test_profile.budget_limit_lkr = 8000.0
    test_profile.location = "Galle"  # This should trigger distance filtering
    
    print(f"👤 User Profile: {test_profile.user_id}")
    print(f"💰 Budget: LKR {test_profile.budget_limit_lkr}")
    print(f"📍 Location: {test_profile.location}")
    
    # Initialize orchestrator
    orchestrator = ProductSearchOrchestrator(test_profile)
    
    # Test query
    test_query = "organic rice and coconut oil for cooking"
    
    print(f"\n🔍 Query: '{test_query}'")
    print("-" * 70)
    
    try:
        # Process the query
        result = orchestrator.process_query(test_query)
        
        print(f"\n✅ Galle location demo completed!")
        print(f"Final processing stage: {result.get('processing_stage')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Galle demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run comprehensive demos"""
    
    print("🚀 COMPREHENSIVE LOYALTY SYSTEM DEMO")
    print("=" * 80)
    
    # Demo 1: Full pipeline with higher budget
    demo1_passed = demo_full_pipeline()
    
    # Demo 2: Location-based filtering
    demo2_passed = demo_with_galle_location()
    
    # Results
    print("\n" + "=" * 80)
    print("📈 DEMO RESULTS SUMMARY")
    print("=" * 80)
    print(f"✅ Full Pipeline Demo: {'PASSED' if demo1_passed else 'FAILED'}")
    print(f"✅ Galle Location Demo: {'PASSED' if demo2_passed else 'FAILED'}")
    
    if demo1_passed and demo2_passed:
        print("\n🎉 ALL DEMOS PASSED!")
        print("💡 The Loyalty Aggregator Agent is fully integrated and working.")
        print("🔧 The system now includes:")
        print("   • Keyword extraction (fixed)")
        print("   • Personalized filtering")
        print("   • Loyalty & discount optimization")
        print("   • Location-based logistics filtering")
        print("   • Enhanced output formatting")
    else:
        print("\n⚠️  Some demos failed. Check the logs above.")


if __name__ == "__main__":
    main()
