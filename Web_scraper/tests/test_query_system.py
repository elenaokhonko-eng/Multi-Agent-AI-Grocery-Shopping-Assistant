#!/usr/bin/env python3
"""
Test script for the complete query management system.
"""

import time
import requests
import json
import asyncio
from utils.query_manager import QueryManager
from utils.query_executor import QueryExecutor

def test_query_manager():
    """Test the query manager functionality."""
    print("🧪 Testing Query Manager...")
    
    query_manager = QueryManager()
    
    # Test saving queries
    result1 = query_manager.save_query("laptop computers", "test")
    print(f"✅ Save query 1: {result1}")
    
    result2 = query_manager.save_query("laptop computer", "test")  # Similar query
    print(f"✅ Save query 2 (similar): {result2}")
    
    result3 = query_manager.save_query("mobile phones", "test")  # Different query
    print(f"✅ Save query 3: {result3}")
    
    # Test getting queries
    pending = query_manager.get_pending_queries()
    print(f"✅ Pending queries: {len(pending)}")
    
    all_queries = query_manager.get_all_queries()
    print(f"✅ Total queries: {len(all_queries)}")
    
    print("Query Manager tests completed!\n")

def test_api_endpoints():
    """Test the Flask API endpoints."""
    print("🌐 Testing API Endpoints...")
    
    base_url = "http://localhost:5000"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Health check: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test search endpoint (should save query)
    try:
        response = requests.get(f"{base_url}/search?query=laptop&top_k=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Search endpoint: {data.get('query_saved', 'No save info')}")
        else:
            print(f"❌ Search endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Search endpoint error: {e}")
    
    # Test query stats endpoint
    try:
        response = requests.get(f"{base_url}/query-stats")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Query stats: {data.get('total_queries', 0)} total queries")
        else:
            print(f"❌ Query stats failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Query stats error: {e}")
    
    # Test queries list endpoint
    try:
        response = requests.get(f"{base_url}/queries?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Queries list: {len(data.get('queries', []))} queries returned")
        else:
            print(f"❌ Queries list failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Queries list error: {e}")
    
    print("API endpoint tests completed!\n")

async def test_query_executor():
    """Test the query executor functionality."""
    print("⚙️ Testing Query Executor...")
    
    # Create some test queries first
    query_manager = QueryManager()
    
    test_queries = [
        "smartphone android",
        "bluetooth headphones",
        "gaming mouse"
    ]
    
    for query in test_queries:
        result = query_manager.save_query(query, "test")
        print(f"✅ Saved test query '{query}': {result}")
    
    # Test executor for a short period
    executor = QueryExecutor(
        batch_size=2,
        interval_seconds=10  # Short interval for testing
    )
    
    print("Running executor for 30 seconds...")
    
    try:
        # Run executor in background
        executor_task = asyncio.create_task(executor.run())
        
        # Wait for 30 seconds
        await asyncio.sleep(30)
        
        # Stop executor
        executor.stop()
        
        # Wait for graceful shutdown
        try:
            await asyncio.wait_for(executor_task, timeout=5)
        except asyncio.TimeoutError:
            print("⚠️ Executor didn't stop gracefully")
        
        # Get stats
        stats = executor.get_statistics()
        print(f"✅ Executor stats: {stats}")
        
    except Exception as e:
        print(f"❌ Executor test error: {e}")
    
    print("Query Executor tests completed!\n")

def main():
    """Run all tests."""
    print("🚀 Starting Query Management System Tests\n")
    
    # Test 1: Query Manager
    test_query_manager()
    
    # Test 2: API Endpoints
    print("📝 Note: Make sure the Flask app is running on localhost:5000 for API tests")
    user_input = input("Press Enter to test API endpoints (or 's' to skip): ")
    if user_input.lower() != 's':
        test_api_endpoints()
    else:
        print("Skipping API endpoint tests.\n")
    
    # Test 3: Query Executor
    print("📝 Note: Query executor test will run for 30 seconds")
    user_input = input("Press Enter to test query executor (or 's' to skip): ")
    if user_input.lower() != 's':
        asyncio.run(test_query_executor())
    else:
        print("Skipping Query Executor tests.\n")
    
    print("🎉 All tests completed!")

if __name__ == "__main__":
    main()
