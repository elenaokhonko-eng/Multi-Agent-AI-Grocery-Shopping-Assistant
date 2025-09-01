"""
Test script to demonstrate substitute product functionality
"""
import os
from core.config import Config
os.environ["GROQ_API_KEY"] = Config.GROQ_API_KEY

from main import ProductSearchOrchestrator


def test_substitute_scenario():
    """Test substitute product scenarios"""
    print("🧪 Testing Knowledge Graph Substitute Feature")
    print("=" * 60)
    
    orchestrator = ProductSearchOrchestrator()
    
    # Test scenarios
    test_cases = [
        "I need Milo drink",
        "Looking for rice varieties", 
        "Want to buy dairy products"
    ]
    
    for i, query in enumerate(test_cases, 1):
        print(f"\n🧪 TEST {i}: {query}")
        print("-" * 40)
        result = orchestrator.process_query(query)
        print(f"✅ Processing stage: {result.get('processing_stage')}")


if __name__ == "__main__":
    test_substitute_scenario()
