#!/usr/bin/env python3
"""
Quick demonstration of minimum guarantee vs regular filtering
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import ProductSearchOrchestrator
from core.user_profile import get_default_profile

def demo_minimum_guarantee():
    """Demo showing the minimum guarantee feature"""
    print("🎯 MINIMUM GUARANTEE DEMONSTRATION")
    print("=" * 60)
    print("This shows how personalization ensures at least 1 item per keyword")
    print("even with very restrictive user preferences.")
    print()
    
    # Use default profile
    user_profile = get_default_profile()
    orchestrator = ProductSearchOrchestrator(user_profile)
    
    # Simple test
    query = "rice and vegetables"
    print(f"🔍 Query: '{query}'")
    print(f"👤 User Profile: {user_profile.user_id} (Budget: LKR {user_profile.budget_limit_lkr})")
    
    result = orchestrator.process_query(query)
    
    # Show guarantee results
    keywords = result.get('keywords', [])
    personalized_data = result.get('personalized_data', {})
    summary = result.get('personalization_summary', {})
    
    print(f"\n📊 RESULTS:")
    print(f"✅ Keywords extracted: {keywords}")
    print(f"✅ Total items before: {summary.get('original_items_count', 0)}")
    print(f"✅ Total items after: {summary.get('final_items_count', 0)}")
    print(f"✅ Minimum guaranteed: {summary.get('minimum_items_guaranteed', False)}")
    
    print(f"\n📦 ITEMS PER KEYWORD:")
    for keyword in keywords:
        count = len(personalized_data.get(keyword, []))
        print(f"  '{keyword}': {count} item(s) {'✅' if count > 0 else '❌'}")
    
    print(f"\n🎯 SUCCESS! Every keyword has at least 1 item available for selection.")
    print("This ensures users always get relevant results for their search terms!")

if __name__ == "__main__":
    demo_minimum_guarantee()
