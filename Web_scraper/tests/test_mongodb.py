#!/usr/bin/env python3
"""
Test MongoDB functionality with the web scraper.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def test_mongodb_scraper():
    """Test scraper with MongoDB integration"""
    print("🔍 Testing Web Scraper with MongoDB Integration")
    print("=" * 50)
    
    try:
        # Import the scraper
        from scrapers.glowmark_scraper import GlowmarkScraper
        from pymongo import MongoClient
        from config.settings import Config
        
        # Check MongoDB connection first
        print("📡 Checking MongoDB connection...")
        client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=3000)
        client.server_info()
        db = client[Config.DATABASE_NAME]
        print(f"✅ Connected to MongoDB: {Config.DATABASE_NAME}")
        
        # Initialize scraper
        scraper = GlowmarkScraper()
        print(f"✅ Initialized {scraper.get_website_name()} scraper")
        
        # Test query
        query = "rice"
        print(f"\n🔍 Scraping for '{query}'...")
        
        # Perform scraping with MongoDB save
        result = await scraper.scrape(query)
        
        if result["success"]:
            print(f"\n✅ Scraping completed successfully!")
            print(f"   Items found: {result['items_count']}")
            print(f"   URL: {result['url']}")
            print(f"   Execution time: {result['execution_time']:.2f}s")
            
            # Check database stats
            db_stats = result.get("database_stats", {})
            if db_stats:
                print(f"   MongoDB stats:")
                print(f"     - Inserted: {db_stats.get('inserted', 0)}")
                print(f"     - Updated: {db_stats.get('modified', 0)}")
                print(f"     - Matched: {db_stats.get('matched', 0)}")
            
            # Verify data in MongoDB
            collection_name = scraper.get_collection_name()
            collection = db[collection_name]
            
            # Count total documents
            total_docs = collection.count_documents({})
            print(f"   Total documents in {collection_name}: {total_docs}")
            
            # Show recent documents
            recent_docs = list(collection.find({
                "scraped_at": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)}
            }).limit(5).sort("scraped_at", -1))
            
            print(f"\n📋 Recent items in database:")
            for i, doc in enumerate(recent_docs, 1):
                print(f"   {i}. {doc.get('title', 'Unknown')[:50]}")
                print(f"      Price: LKR {doc.get('price_LKR', 0):,.2f}")
                print(f"      Source: {doc.get('website', 'Unknown')}")
                print(f"      Scraped: {doc.get('scraped_at', 'Unknown')}")
                print()
            
            # Test search in database
            print("🔍 Testing database search...")
            search_results = list(collection.find({
                "title": {"$regex": "rice", "$options": "i"}
            }).limit(3))
            
            print(f"   Found {len(search_results)} items matching 'rice':")
            for item in search_results:
                print(f"   - {item.get('title', 'Unknown')[:40]} - LKR {item.get('price_LKR', 0):,.2f}")
            
        else:
            print(f"❌ Scraping failed: {result.get('error', 'Unknown error')}")
            return False
        
        # Clean up
        scraper.close()
        client.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_multiple_sites():
    """Test scraping multiple sites and saving to MongoDB"""
    print("\n" + "=" * 50)
    print("🌐 Testing Multiple Sites MongoDB Integration")
    print("=" * 50)
    
    sites = [
        ("glowmark", "GlowmarkScraper"),
        ("kapruka", "KaprukaScraper"),
        ("onlinekade", "OnlineKadeScraper")
    ]
    
    results = {}
    
    for site_name, scraper_class_name in sites:
        try:
            print(f"\n📡 Testing {site_name}...")
            
            # Dynamic import
            from scrapers import glowmark_scraper, kapruka_scraper, onlinekade_scraper
            
            if site_name == "glowmark":
                scraper_class = glowmark_scraper.GlowmarkScraper
            elif site_name == "kapruka":
                scraper_class = kapruka_scraper.KaprukaScraper
            else:
                scraper_class = onlinekade_scraper.OnlineKadeScraper
            
            scraper = scraper_class()
            result = await scraper.scrape("rice")
            
            results[site_name] = result
            
            if result["success"]:
                print(f"✅ {site_name}: {result['items_count']} items in {result['execution_time']:.2f}s")
                db_stats = result.get("database_stats", {})
                if db_stats:
                    print(f"   MongoDB: {db_stats.get('inserted', 0)} new, {db_stats.get('modified', 0)} updated")
            else:
                print(f"❌ {site_name}: {result.get('error', 'Failed')}")
            
            scraper.close()
            
        except Exception as e:
            print(f"❌ {site_name}: Error - {e}")
            results[site_name] = {"success": False, "error": str(e)}
    
    # Summary
    print(f"\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    successful = sum(1 for r in results.values() if r.get("success"))
    total_items = sum(r.get("items_count", 0) for r in results.values())
    
    print(f"Sites tested: {len(sites)}")
    print(f"Successful: {successful}")
    print(f"Total items scraped: {total_items}")
    
    return successful > 0

async def main():
    """Main test function"""
    print("🚀 MongoDB Web Scraper Integration Test")
    print("🗄️  Testing database connectivity and data persistence")
    print()
    
    # Test single site first
    single_test = await test_mongodb_scraper()
    
    if single_test:
        # Test multiple sites
        multi_test = await test_multiple_sites()
        
        if multi_test:
            print(f"\n🎉 All tests passed! MongoDB integration is working.")
        else:
            print(f"\n⚠️  Single site works, but multiple sites had issues.")
    else:
        print(f"\n💥 MongoDB integration test failed!")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
