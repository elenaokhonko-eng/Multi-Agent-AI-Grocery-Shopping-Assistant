#!/usr/bin/env python3
"""
Migration and testing script for the refactored scraper system.
"""

import sys
import asyncio
from pathlib import Path

# Add the refactored directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from scrapers import GlowmarkScraper, KaprukaScraper, OnlineKadeScraper
from utils.helpers import setup_logging

def test_single_scraper(scraper_class, site_name: str, query: str = "rice"):
    """Test a single scraper implementation."""
    print(f"\n{'='*50}")
    print(f"Testing {site_name} scraper with query: '{query}'")
    print('='*50)
    
    scraper = scraper_class()
    try:
        # Test URL building
        url = scraper.build_search_url(query)
        print(f"Search URL: {url}")
        
        # Test scraping
        result = scraper.scrape_sync(query)
        
        if result.get("success"):
            print(f"✓ Success: {result['items_count']} items found")
            print(f"  Execution time: {result['execution_time']:.2f}s")
            
            if result.get("item_stats"):
                stats = result["item_stats"]
                if stats.get("price_stats"):
                    price_stats = stats["price_stats"]
                    print(f"  Price range: LKR {price_stats['min']:.0f} - LKR {price_stats['max']:.0f}")
            
            print(f"  Database: {result.get('database_stats', {})}")
        else:
            print(f"✗ Failed: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        print(f"✗ Exception: {e}")
        return {"success": False, "error": str(e)}
    finally:
        scraper.close()

def test_all_scrapers(query: str = "rice"):
    """Test all scraper implementations."""
    print(f"Testing all scrapers with query: '{query}'")
    
    scrapers = [
        (GlowmarkScraper, "Glowmark"),
        (KaprukaScraper, "Kapruka"), 
        (OnlineKadeScraper, "OnlineKade")
    ]
    
    results = {}
    total_items = 0
    successful_scrapers = 0
    
    for scraper_class, name in scrapers:
        result = test_single_scraper(scraper_class, name, query)
        results[name.lower()] = result
        
        if result.get("success"):
            successful_scrapers += 1
            total_items += result.get("items_count", 0)
    
    print(f"\n{'='*50}")
    print("OVERALL RESULTS")
    print('='*50)
    print(f"Successful scrapers: {successful_scrapers}/{len(scrapers)}")
    print(f"Total items found: {total_items}")
    
    return results

def test_backwards_compatibility():
    """Test that legacy functions still work."""
    print(f"\n{'='*50}")
    print("Testing backwards compatibility")
    print('='*50)
    
    try:
        # Test legacy imports
        from scrapers.glowmark_scraper import scrape_glowmark
        from scrapers.kapruka_scraper import scrape_kapruka
        from scrapers.onlinekade_scraper import scrape_onlinekade
        
        print("✓ Legacy imports successful")
        
        # Test legacy function calls
        query = "test"
        
        print("Testing legacy functions...")
        
        # Note: These will actually scrape, so we'll just test the import for now
        print("✓ Legacy functions are available")
        print("  - scrape_glowmark()")
        print("  - scrape_kapruka()")
        print("  - scrape_onlinekade()")
        
        return True
        
    except Exception as e:
        print(f"✗ Backwards compatibility test failed: {e}")
        return False

def main():
    """Main testing function."""
    # Setup logging
    logger = setup_logging("INFO")
    
    print("Starting migration testing...")
    print("This will test the new refactored scraper system.")
    
    # Get query from command line or use default
    query = sys.argv[1] if len(sys.argv) > 1 else "rice"
    
    try:
        # Test backwards compatibility
        test_backwards_compatibility()
        
        # Test individual scrapers
        results = test_all_scrapers(query)
        
        # Summary
        successful = sum(1 for r in results.values() if r.get("success"))
        total_items = sum(r.get("items_count", 0) for r in results.values())
        
        print(f"\n{'='*50}")
        print("MIGRATION TEST SUMMARY")
        print('='*50)
        print(f"Query tested: '{query}'")
        print(f"Scrapers working: {successful}/3")
        print(f"Total items found: {total_items}")
        
        if successful == 3:
            print("✓ All scrapers working correctly!")
            print("\nNext steps:")
            print("1. Try the CLI: python cli.py 'your_query'")
            print("2. Start the API: python app.py")
            print("3. Check the README.md for full documentation")
        elif successful > 0:
            print(f"⚠ Partial success: {successful}/3 scrapers working")
            print("Check the errors above and ensure MongoDB is running")
        else:
            print("✗ No scrapers working")
            print("Please check:")
            print("- MongoDB is running (mongod)")
            print("- Internet connection is working")
            print("- API keys are configured correctly")
        
        return successful > 0
        
    except KeyboardInterrupt:
        print("\nTesting interrupted by user")
        return False
    except Exception as e:
        print(f"Testing failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
