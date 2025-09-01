"""
Test script for the refactored Langraph application
"""
import sys
import os

# Add the current directory to sys.path to import main
sys.path.insert(0, os.path.dirname(__file__))

from main import ProductSearchOrchestrator

def test_application():
    """Test the application with a sample query"""
    print("🧪 Testing Refactored Langraph Application")
    print("=" * 50)
    
    # Initialize orchestrator
    orchestrator = ProductSearchOrchestrator()
    
    # Test query
    test_query = "I need milk and tea"
    print(f"Testing with query: '{test_query}'")
    
    # Process the query
    result = orchestrator.process_query(test_query)
    
    print("\n✅ Test completed successfully!")
    print(f"Final processing stage: {result.get('processing_stage')}")
    print(f"Keywords extracted: {result.get('keywords')}")
    print(f"Product data keys: {list(result.get('product_data', {}).keys())}")

if __name__ == "__main__":
    test_application()
