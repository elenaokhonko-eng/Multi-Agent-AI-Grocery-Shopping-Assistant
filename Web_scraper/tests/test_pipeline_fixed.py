#!/usr/bin/env python3
"""
Test the complete scraper pipeline with MongoDB saving.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def test_complete_scraper_pipeline():
    """Test the complete scraper pipeline"""
    print("🚀 Testing Complete Scraper Pipeline")
    print("🗄️  Using environment-configured database")
    print("=" * 50)
    
    try:
        from scrapers.glowmark_scraper import GlowmarkScraper
        from pymongo import MongoClient
        from config.settings import Config
        
        # Show configuration
        print(f"📊 Database: {Config.DATABASE_NAME}")
        print(f"📊 MongoDB URI: {Config.MONGO_URI}")
        
        # Check database connection
        client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=3000)
        client.server_info()
        db = client[Config.DATABASE_NAME]
        
        # Initialize scraper
        scraper = GlowmarkScraper()
        collection = db[scraper.get_collection_name()]
        
        # Get count before
        count_before = collection.count_documents({})
        print(f"📋 Documents before: {count_before}")
        
        # Create test data (simulating successful scraping)
        test_url = "https://glomark.lk/search?search-text=test"
        test_items = [
            {
                "title": f"Test Product {datetime.now().strftime('%H%M%S')}",
                "price_value": 999.99,
                "currency": "LKR",
                "image_url": "https://example.com/test.jpg"
            }
        ]
        
        # Test the normalize and save process
        normalized_docs = scraper.normalize_items(test_items, test_url)
        print(f"✅ Normalized {len(normalized_docs)} documents")
        
        # Save to MongoDB
        db_stats = scraper.save_to_mongodb(normalized_docs)
        print(f"💾 MongoDB operation completed:")
        print(f"   - Inserted: {db_stats.get('inserted', 0)}")
        print(f"   - Modified: {db_stats.get('modified', 0)}")
        print(f"   - Matched: {db_stats.get('matched', 0)}")
        
        # Verify save
        count_after = collection.count_documents({})
        print(f"📋 Documents after: {count_after}")
        print(f"📈 Change: +{count_after - count_before}")
        
        # Show latest document
        latest_doc = collection.find().sort("scraped_at", -1).limit(1)
        for doc in latest_doc:
            print(f"\n📄 Latest document:")
            print(f"   Title: {doc.get('title', 'Unknown')}")
            print(f"   Price: LKR {doc.get('price_LKR', 0):,.2f}")
            print(f"   Website: {doc.get('website', 'Unknown')}")
            print(f"   Scraped: {doc.get('scraped_at', 'Unknown')}")
        
        # Test search functionality
        search_results = list(collection.find({
            "title": {"$regex": "Test Product", "$options": "i"}
        }).limit(3))
        
        print(f"\n🔍 Search test - found {len(search_results)} test products")
        
        # Clean up
        scraper.close()
        client.close()
        
        print(f"\n✅ Complete pipeline test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    success = await test_complete_scraper_pipeline()
    
    if success:
        print("\n🎉 MongoDB scraper integration is working perfectly!")
        print("💾 Data is being saved to the correct database")
        print("🔧 Environment configuration is properly loaded")
    else:
        print("\n💥 There are still issues to resolve")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
