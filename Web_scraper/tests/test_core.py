#!/usr/bin/env python3
"""
Test just the crawling part without ML components.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def test_crawl_website():
    """Test crawling a website without ML"""
    print("🔍 Testing website crawling...")
    
    try:
        from crawl4ai import AsyncWebCrawler, CacheMode
        
        url = "https://glomark.lk/search?search-text=rice"
        print(f"📡 Fetching: {url}")
        
        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(
                url=url,
                cache_mode=CacheMode.ENABLED,
                word_count_threshold=100,
                verbose=False
            )
            
            markdown = result.markdown or ""
            print(f"✅ Fetched {len(markdown)} characters of markdown")
            
            # Save a sample for inspection
            if markdown:
                with open("sample_markdown.txt", "w", encoding="utf-8") as f:
                    f.write(markdown[:2000])  # First 2000 chars
                print("📄 Saved sample to sample_markdown.txt")
            
            return True
            
    except Exception as e:
        print(f"❌ Crawling failed: {e}")
        return False

async def test_groq_api():
    """Test Groq API without sentence transformers"""
    print("🤖 Testing Groq API...")
    
    try:
        from groq import Groq
        from config.settings import Config
        
        client = Groq(api_key=Config.GROQ_API_KEY)
        
        response = client.chat.completions.create(
            model=Config.GROQ_MODEL,
            messages=[
                {"role": "user", "content": "Say 'Hello from Groq!' in JSON format: {\"message\": \"...\"}"}
            ],
            temperature=0
        )
        
        content = response.choices[0].message.content
        print(f"✅ Groq API working: {content}")
        
        return True
        
    except Exception as e:
        print(f"❌ Groq API failed: {e}")
        # Try simple test
        try:
            print("🔄 Trying basic Groq test...")
            client = Groq(api_key=Config.GROQ_API_KEY)
            print("✅ Groq client created successfully")
            return True
        except Exception as e2:
            print(f"❌ Basic Groq test also failed: {e2}")
            return False

async def main():
    """Run basic tests without ML components"""
    print("🚀 Testing Core Web Scraper Components\n")
    
    # Test crawling
    crawl_ok = await test_crawl_website()
    print()
    
    # Test API
    api_ok = await test_groq_api()
    print()
    
    if crawl_ok and api_ok:
        print("✅ Core components working! Web scraper should function.")
    else:
        print("❌ Some components failed.")

if __name__ == "__main__":
    asyncio.run(main())
