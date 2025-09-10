#!/usr/bin/env python3
"""
Simple test script to verify the web scraper basic functionality.
"""

import sys
import asyncio
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def test_crawl4ai():
    """Test basic crawl4ai functionality"""
    print("Testing crawl4ai...")
    try:
        from crawl4ai import AsyncWebCrawler, CacheMode
        
        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(
                url="https://httpbin.org/html",
                cache_mode=CacheMode.ENABLED,
                word_count_threshold=10,
                verbose=False
            )
            
            print(f"✅ crawl4ai working: {len(result.markdown)} chars fetched")
            return True
            
    except Exception as e:
        print(f"❌ crawl4ai failed: {e}")
        return False

def test_imports():
    """Test all required imports"""
    print("Testing imports...")
    
    try:
        # Test basic imports
        from config.settings import Config
        print("✅ Config imported")
        
        # Test scraper imports
        from scrapers.base_scraper import BaseScraper
        print("✅ BaseScraper imported")
        
        # Test Groq
        from groq import Groq
        print("✅ Groq imported")
        
        # Test MongoDB
        from pymongo import MongoClient
        print("✅ MongoDB imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

async def test_basic_scraper():
    """Test basic scraper functionality"""
    print("Testing basic scraper...")
    
    try:
        from scrapers.glowmark_scraper import GlowmarkScraper
        
        scraper = GlowmarkScraper()
        print(f"✅ Scraper initialized: {scraper.get_website_name()}")
        
        # Test URL building
        url = scraper.build_search_url("rice")
        print(f"✅ URL built: {url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Scraper test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Web Scraper Tests\n")
    
    # Test imports
    if not test_imports():
        return
    
    print()
    
    # Test crawl4ai
    if not await test_crawl4ai():
        return
    
    print()
    
    # Test basic scraper
    if not await test_basic_scraper():
        return
    
    print("\n✅ All tests passed! Web scraper is ready.")

if __name__ == "__main__":
    asyncio.run(main())
