#!/usr/bin/env python3
"""
Test MongoDB functionality with mock data (bypass LLM issues).
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def test_mongodb_with_mock_data():
    """Test MongoDB functionality with mock data"""
    print("🔍 Testing MongoDB Integration with Mock Data")
    print("=" * 50)
    
    try:
        # Import required modules
        from pymongo import MongoClient
        from config.settings import Config
        from scrapers.glowmark_scraper import GlowmarkScraper
        
        # Check MongoDB connection
        print("📡 Checking MongoDB connection...")
        client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=3000)
        client.server_info()
        db = client[Config.DATABASE_NAME]
        print(f"✅ Connected to MongoDB: {Config.DATABASE_NAME}")
        
        # Create scraper instance
        scraper = GlowmarkScraper()
        collection = db[scraper.get_collection_name()]
        
        print(f"✅ Using collection: {scraper.get_collection_name()}")
        
        # Create mock extracted items (simulating what would come from LLM)
        mock_items = [
            {
                "title": "Premium Basmati Rice 5kg",
                "price_value": 1250.00,
                "currency": "LKR",
                "image_url": "https://example.com/rice1.jpg"
            },
            {
                "title": "Red Raw Rice 1kg",
                "price_value": 285.50,
                "currency": "LKR", 
                "image_url": "https://example.com/rice2.jpg"
            },
            {
                "title": "Samba Rice White 2kg",
                "price_value": 750.00,
                "currency": "LKR",
                "image_url": None
            }
        ]
        
        print(f"📦 Created {len(mock_items)} mock items")
        
        # Test the normalize_items method
        url = "https://glomark.lk/search?search-text=rice"
        normalized_docs = scraper.normalize_items(mock_items, url)
        
        print("✅ Items normalized successfully")
        for i, doc in enumerate(normalized_docs, 1):
            print(f"   {i}. {doc['title']} - LKR {doc['price_LKR']:,.2f}")
        
        # Test saving to MongoDB
        print("\n💾 Testing MongoDB save...")
        db_stats = scraper.save_to_mongodb(normalized_docs)
        
        print("✅ Data saved to MongoDB!")
        print(f"   Inserted: {db_stats.get('inserted', 0)}")
        print(f"   Modified: {db_stats.get('modified', 0)}")
        print(f"   Matched: {db_stats.get('matched', 0)}")
        
        # Verify data in database
        print("\n🔍 Verifying data in database...")
        total_docs = collection.count_documents({})
        print(f"   Total documents: {total_docs}")
        
        # Find recent documents
        recent_docs = list(collection.find({
            "website": "Glowmark"
        }).limit(5).sort("scraped_at", -1))
        
        print(f"   Recent Glowmark items:")
        for i, doc in enumerate(recent_docs, 1):
            print(f"     {i}. {doc.get('title', 'Unknown')}")
            print(f"        Price: LKR {doc.get('price_LKR', 0):,.2f}")
            print(f"        Scraped: {doc.get('scraped_at')}")
        
        # Test search functionality
        print("\n🔎 Testing database search...")
        rice_items = list(collection.find({
            "title": {"$regex": "rice", "$options": "i"}
        }).limit(3))
        
        print(f"   Found {len(rice_items)} items containing 'rice':")
        for item in rice_items:
            print(f"   - {item.get('title', 'Unknown')} - LKR {item.get('price_LKR', 0):,.2f}")
        
        # Test update functionality (simulate re-scraping same item)
        print("\n🔄 Testing upsert functionality...")
        duplicate_item = [{
            "title": "Premium Basmati Rice 5kg",  # Same title as first item
            "price_value": 1299.00,  # Different price
            "currency": "LKR",
            "image_url": "https://example.com/rice1_updated.jpg"
        }]
        
        normalized_duplicate = scraper.normalize_items(duplicate_item, url)
        update_stats = scraper.save_to_mongodb(normalized_duplicate)
        
        print("✅ Upsert test completed!")
        print(f"   Updated: {update_stats.get('modified', 0)}")
        print(f"   Matched: {update_stats.get('matched', 0)}")
        
        # Clean up
        scraper.close()
        client.close()
        
        print(f"\n🎉 MongoDB integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_all_collections():
    """Test all scraper collections"""
    print("\n" + "=" * 50)
    print("🗄️  Testing All Collections")
    print("=" * 50)
    
    from pymongo import MongoClient
    from config.settings import Config
    
    try:
        client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=3000)
        db = client[Config.DATABASE_NAME]
        
        # List all collections
        collections = db.list_collection_names()
        print(f"📋 Available collections: {collections}")
        
        # Show stats for each collection
        for coll_name in collections:
            collection = db[coll_name]
            count = collection.count_documents({})
            print(f"   {coll_name}: {count} documents")
            
            if count > 0:
                # Show a sample document
                sample = collection.find_one()
                print(f"     Sample: {sample.get('title', 'No title')[:30]}...")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Collection test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 MongoDB Integration Test (Mock Data)")
    print("🗄️  Testing database operations without LLM dependencies")
    print()
    
    # Test MongoDB with mock data
    mock_test = await test_mongodb_with_mock_data()
    
    if mock_test:
        # Test collections overview
        await test_all_collections()
        print(f"\n✅ All MongoDB tests passed!")
        return True
    else:
        print(f"\n💥 MongoDB tests failed!")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
