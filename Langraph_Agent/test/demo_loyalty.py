"""
Demo script to test the Loyalty Aggregator Agent integration
"""
import os
import sys

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config import Config
os.environ["GROQ_API_KEY"] = Config.GROQ_API_KEY

from main import ProductSearchOrchestrator
from core.user_profile import get_default_profile


def test_loyalty_optimization():
    """Test the loyalty aggregator agent functionality"""
    
    print("🧪 Testing Loyalty Aggregator Agent Integration")
    print("=" * 60)
    
    # Create a test profile
    test_profile = get_default_profile()
    print(f"📋 Using test profile: {test_profile.user_id}")
    print(f"💰 Budget: LKR {test_profile.budget_limit_lkr}")
    
    # Initialize orchestrator
    orchestrator = ProductSearchOrchestrator(test_profile)
    
    # Test query with multiple products
    test_query = "I need organic rice, coconut oil, and vitamin supplements"
    
    print(f"\n🔍 Test Query: '{test_query}'")
    print("-" * 60)
    
    try:
        # Process the query
        result = orchestrator.process_query(test_query)
        
        print("\n✅ Test completed successfully!")
        print(f"Final processing stage: {result.get('processing_stage')}")
        
        # Print loyalty optimization summary
        loyalty_summary = result.get('loyalty_summary', {})
        if loyalty_summary and not loyalty_summary.get('error'):
            print(f"\n💳 LOYALTY OPTIMIZATION RESULTS:")
            print(f"Total Savings: LKR {loyalty_summary.get('total_savings', 0):.2f}")
            print(f"Savings Percentage: {loyalty_summary.get('savings_percentage', 0)}%")
            print(f"Stores Analyzed: {loyalty_summary.get('stores_analyzed', 0)}")
            
            optimization_summary = loyalty_summary.get('optimization_summary', {})
            if optimization_summary:
                print(f"Best Store for Savings: {optimization_summary.get('best_store_for_savings', 'N/A')}")
                print(f"Total Loyalty Points: {optimization_summary.get('total_loyalty_points', 0)}")
                print(f"Recommended Action: {optimization_summary.get('recommended_action', 'N/A')}")
        else:
            print(f"\n⚠️ Loyalty optimization error: {loyalty_summary.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_loyalty_data_availability():
    """Test that loyalty data is properly loaded"""
    
    print("\n🧪 Testing Loyalty Data Availability")
    print("=" * 60)
    
    try:
        from data.loyalty_programs import LOYALTY_PROGRAMS, BANK_DISCOUNTS, ACTIVE_PROMOTIONS
        
        print(f"✅ Loyalty Programs Loaded: {len(LOYALTY_PROGRAMS)} programs")
        for store, program in LOYALTY_PROGRAMS.items():
            print(f"  • {program.program_name} ({store})")
        
        print(f"\n✅ Bank Discounts Loaded: {len(BANK_DISCOUNTS)} discounts")
        for discount in BANK_DISCOUNTS:
            print(f"  • {discount.bank_name} {discount.card_type}: {discount.discount_percentage}%")
        
        print(f"\n✅ Active Promotions Loaded: {len(ACTIVE_PROMOTIONS)} promotions")
        for promo in ACTIVE_PROMOTIONS:
            print(f"  • {promo.store_name}: {promo.title}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to load loyalty data: {e}")
        return False


def test_loyalty_agent_standalone():
    """Test the loyalty agent in isolation"""
    
    print("\n🧪 Testing Loyalty Agent Standalone")
    print("=" * 60)
    
    try:
        from langchain_ollama import ChatOllama
        from agents.loyalty_aggregator_agent import LoyaltyAggregatorAgent
        
        # Initialize agent
        llm = ChatOllama(base_url=Config.OLLAMA_BASE_URL, model="llama-3.3-70b-versatile", temperature=0.1)
        loyalty_agent = LoyaltyAggregatorAgent(llm)
        
        # Create test items
        test_items = [
            {
                "title": "Organic Rice 1kg",
                "price_lkr": 450,
                "website": "keells.com",
                "collection": "keells"
            },
            {
                "title": "Coconut Oil 500ml",
                "price_lkr": 280,
                "website": "cargills.com", 
                "collection": "cargills"
            },
            {
                "title": "Vitamin D Supplements",
                "price_lkr": 1200,
                "website": "arpico.com",
                "collection": "arpico"
            }
        ]
        
        print(f"📦 Test items: {len(test_items)} products")
        for item in test_items:
            print(f"  • {item['title']}: LKR {item['price_lkr']} from {item['website']}")
        
        # Test optimization
        optimized_items, loyalty_summary = loyalty_agent.optimize_loyalty_benefits(test_items)
        
        print(f"\n✅ Optimization completed!")
        print(f"Total Savings: LKR {loyalty_summary.get('total_savings', 0):.2f}")
        print(f"Savings Percentage: {loyalty_summary.get('savings_percentage', 0)}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Standalone test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all loyalty integration tests"""
    
    print("🚀 Starting Loyalty Aggregator Agent Tests")
    print("=" * 70)
    
    # Test 1: Data availability
    test1_passed = test_loyalty_data_availability()
    
    # Test 2: Standalone agent
    test2_passed = test_loyalty_agent_standalone()
    
    # Test 3: Full integration
    test3_passed = test_loyalty_optimization()
    
    # Results summary
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    print(f"✅ Data Availability Test: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"✅ Standalone Agent Test: {'PASSED' if test2_passed else 'FAILED'}")
    print(f"✅ Full Integration Test: {'PASSED' if test3_passed else 'FAILED'}")
    
    all_passed = test1_passed and test2_passed and test3_passed
    print(f"\n🎯 Overall Result: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 Loyalty Aggregator Agent successfully integrated!")
        print("💡 The system can now optimize discounts and loyalty benefits.")
    else:
        print("\n🔧 Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    main()
