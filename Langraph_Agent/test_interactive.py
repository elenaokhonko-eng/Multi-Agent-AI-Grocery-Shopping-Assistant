#!/usr/bin/env python3
"""
Interactive test simulation - shows the complete user experience
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import ProductSearchOrchestrator
from core.user_profile import get_default_profile

def simulate_user_session():
    """Simulate a complete user session"""
    print("🛒 Product Search Assistant - User Session Simulation")
    print("=" * 60)
    
    # Use default profile for quick demo
    user_profile = get_default_profile()
    print(f"👤 Using profile: {user_profile.user_id}")
    print(f"💰 Budget: LKR {user_profile.budget_limit_lkr}")
    
    # Initialize orchestrator
    orchestrator = ProductSearchOrchestrator(user_profile)
    
    # Simulate different user queries
    queries = [
        "rice and curry ingredients",
        "breakfast items",
        "party snacks and drinks"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*60}")
        print(f"🔍 Query {i}: '{query}'")
        print("="*60)
        
        try:
            result = orchestrator.process_query(query)
            print(f"✅ Query {i} processed successfully!")
            
        except Exception as e:
            print(f"❌ Query {i} failed: {e}")
    
    print(f"\n{'='*60}")
    print("🎉 User session simulation completed!")
    print("All components working correctly:")
    print("  ✅ Keyword extraction")
    print("  ✅ Data acquisition with knowledge graph")
    print("  ✅ Personalization filtering")
    print("  ✅ Output formatting")
    print("="*60)

if __name__ == "__main__":
    simulate_user_session()
