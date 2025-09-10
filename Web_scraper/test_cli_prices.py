#!/usr/bin/env python3
"""
Simple CLI test for scraping without similarity search dependencies.
"""

import asyncio
import sys
from pathlib import Path
from pymongo import MongoClient

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def test_cli_scraping(query="milo"):
    """Test CLI-style scraping and check MongoDB saving"""
    print(f"🔍 Testing CLI Scraping with query: '{query}'")
    print("=" * 50)
    
    try:
        from scrapers.glowmark_scraper import GlowmarkScraper
        from config.settings import Config
        
        # Initialize database connection
        client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=3000)
        db = client[Config.DATABASE_NAME]
        collection = db['Glowmark']
        
        # Get initial count
        initial_count = collection.count_documents({})
        print(f"📊 Initial Glowmark documents: {initial_count}")
        
        # Initialize scraper
        scraper = GlowmarkScraper()
        print(f"✅ Initialized {scraper.get_website_name()} scraper")
        
        # Perform scraping
        print(f"🔄 Scraping for '{query}'...")
        result = await scraper.scrape(query)
        
        if result["success"]:
            print(f"✅ Scraping completed!")
            print(f"   Items found: {result['items_count']}")
            print(f"   URL: {result['url']}")
            print(f"   Execution time: {result['execution_time']:.2f}s")
            
            # Check database stats
            db_stats = result.get("database_stats", {})
            if db_stats:
                print(f"   MongoDB operations:")
                print(f"     - Inserted: {db_stats.get('inserted', 0)}")
                print(f"     - Modified: {db_stats.get('modified', 0)}")
                print(f"     - Matched: {db_stats.get('matched', 0)}")
            
            # Verify documents were added
            final_count = collection.count_documents({})
            print(f"📊 Final Glowmark documents: {final_count}")
            print(f"📈 Documents added: {final_count - initial_count}")
            
            # Check for null prices
            null_price_count = collection.count_documents({"price_LKR": None})
            zero_price_count = collection.count_documents({"price_LKR": 0})
            valid_price_count = collection.count_documents({
                "price_LKR": {"$gt": 0}
            })
            
            print(f"\n💰 Price Analysis:")
            print(f"   Documents with null prices: {null_price_count}")
            print(f"   Documents with zero prices: {zero_price_count}")
            print(f"   Documents with valid prices: {valid_price_count}")
            
            # Show recent documents with price details
            print(f"\n📋 Recent documents (checking prices):")
            recent_docs = list(collection.find({
                "scraped_at": {"$gte": result.get("scraped_at", "2025-09-10")}
            }).limit(5))
            
            for i, doc in enumerate(recent_docs, 1):
                title = doc.get('title', 'Unknown')[:40]
                price = doc.get('price_LKR')
                price_str = f"LKR {price:,.2f}" if price is not None and price > 0 else f"NULL/ZERO: {price}"
                
                print(f"   {i}. {title}")
                print(f"      Price: {price_str}")
                
                # Check if this document has price issues
                if price is None:
                    print(f"      ⚠️  NULL PRICE DETECTED!")
                elif price == 0:
                    print(f"      ⚠️  ZERO PRICE DETECTED!")
            
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

async def check_existing_price_issues():
    """Check existing database for price issues"""
    print(f"\n🔍 Analyzing Existing Database for Price Issues")
    print("=" * 50)
    
    try:
        from config.settings import Config
        
        client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=3000)
        db = client[Config.DATABASE_NAME]
        collection = db['Glowmark']
        
        # Analyze price distribution
        total_docs = collection.count_documents({})
        null_prices = collection.count_documents({"price_LKR": None})
        zero_prices = collection.count_documents({"price_LKR": 0})
        valid_prices = collection.count_documents({"price_LKR": {"$gt": 0}})
        
        print(f"📊 Database Analysis:")
        print(f"   Total documents: {total_docs}")
        print(f"   NULL prices: {null_prices} ({null_prices/total_docs*100:.1f}%)")
        print(f"   Zero prices: {zero_prices} ({zero_prices/total_docs*100:.1f}%)")
        print(f"   Valid prices: {valid_prices} ({valid_prices/total_docs*100:.1f}%)")
        
        # Show examples of problematic documents
        if null_prices > 0:
            print(f"\n⚠️  Examples of NULL price documents:")
            null_docs = list(collection.find({"price_LKR": None}).limit(3))
            for i, doc in enumerate(null_docs, 1):
                print(f"   {i}. {doc.get('title', 'Unknown')}")
                print(f"      Raw data: price_LKR = {doc.get('price_LKR')}")
                print(f"      Scraped: {doc.get('scraped_at')}")
        
        if zero_prices > 0:
            print(f"\n⚠️  Examples of ZERO price documents:")
            zero_docs = list(collection.find({"price_LKR": 0}).limit(3))
            for i, doc in enumerate(zero_docs, 1):
                print(f"   {i}. {doc.get('title', 'Unknown')}")
                print(f"      Raw data: price_LKR = {doc.get('price_LKR')}")
                print(f"      Scraped: {doc.get('scraped_at')}")
        
        # Show examples of valid prices
        print(f"\n✅ Examples of VALID price documents:")
        valid_docs = list(collection.find({"price_LKR": {"$gt": 0}}).limit(3))
        for i, doc in enumerate(valid_docs, 1):
            print(f"   {i}. {doc.get('title', 'Unknown')}")
            print(f"      Price: LKR {doc.get('price_LKR', 0):,.2f}")
            print(f"      Scraped: {doc.get('scraped_at')}")
        
        client.close()
        
        return null_prices > 0 or zero_prices > 0
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False

async def main():
    """Main test function"""
    # First check existing database for issues
    has_price_issues = await check_existing_price_issues()
    
    # Then test new scraping
    scraping_success = await test_cli_scraping("milo")
    
    if has_price_issues:
        print(f"\n⚠️  PRICE ISSUES DETECTED in database!")
        print("🔧 Will analyze and fix price handling logic...")
    
    if scraping_success:
        print(f"\n✅ CLI scraping test completed")
    else:
        print(f"\n❌ CLI scraping test failed")
    
    return scraping_success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
