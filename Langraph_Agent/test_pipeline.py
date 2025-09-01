#!/usr/bin/env python3
"""
Test script for the Langraph Product Search Pipeline
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import ProductSearchOrchestrator
from core.user_profile import get_default_profile
from utils.profile_manager import print_profile_summary

def test_pipeline():
    """Test the complete pipeline with a sample query"""
    print("🧪 Testing Langraph Product Search Pipeline")
    print("=" * 60)
    
    # Create a test profile
    test_profile = get_default_profile()
    print("📋 Using test profile:")
    print(f"User ID: {test_profile.user_id}")
    print(f"Budget Limit: LKR {test_profile.budget_limit_lkr}")
    print(f"Dietary: Vegetarian={test_profile.dietary_needs.vegetarian}, Vegan={test_profile.dietary_needs.vegan}")
    print(f"Preferred Brands: {test_profile.brand_preferences.preferred_brands or 'None'}")
    
    # Initialize the orchestrator
    print("\n🚀 Initializing orchestrator...")
    orchestrator = ProductSearchOrchestrator(test_profile)
    
    # Test queries
    test_queries = [
        "I need rice and dhal for cooking",
        "Looking for healthy snacks under 500 LKR",
        "Need some fruits and vegetables"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"🔍 TEST {i}: {query}")
        print("="*60)
        
        try:
            # Process the query
            result = orchestrator.process_query(query)
            
            # Show final result
            print(f"\n✅ Test {i} completed successfully!")
            print(f"Final stage: {result.get('processing_stage')}")
            print(f"Keywords extracted: {result.get('keywords', [])}")
            print(f"Product data keys: {list(result.get('product_data', {}).keys())}")
            print(f"Personalized data keys: {list(result.get('personalized_data', {}).keys())}")
            
        except Exception as e:
            print(f"❌ Test {i} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("🏁 Pipeline testing completed!")
    print("="*60)

if __name__ == "__main__":
    test_pipeline()
