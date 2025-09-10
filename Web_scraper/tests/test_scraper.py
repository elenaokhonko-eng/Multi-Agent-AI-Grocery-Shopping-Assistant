#!/usr/bin/env python3
"""
Simple CLI test for web scraper functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def test_scraper(query="rice"):
    """Test a single scraper with a simple query"""
    print(f"🔍 Testing web scraper with query: '{query}'")
    
    try:
        from scrapers.glowmark_scraper import GlowmarkScraper
        
        # Initialize scraper
        scraper = GlowmarkScraper()
        print(f"✅ Initialized {scraper.get_website_name()} scraper")
        
        # Perform scraping
        print("⏳ Fetching data...")
        result = await scraper.scrape(query)
        
        if result["success"]:
            print(f"✅ Scraping successful!")
            print(f"   Items found: {result['items_count']}")
            print(f"   URL: {result['url']}")
            print(f"   Execution time: {result['execution_time']:.2f}s")
            
            if result.get("item_stats"):
                stats = result["item_stats"]
                if stats["price_range"]:
                    print(f"   Price range: LKR {stats['price_range']['min']:,.2f} - {stats['price_range']['max']:,.2f}")
            
        else:
            print(f"❌ Scraping failed: {result.get('error', 'Unknown error')}")
            
        # Clean up
        scraper.close()
        
        return result["success"]
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def main():
    """Run scraper test"""
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "rice"
    
    success = await test_scraper(query)
    
    if success:
        print("\n🎉 Web scraper is working correctly!")
    else:
        print("\n💥 Web scraper test failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
