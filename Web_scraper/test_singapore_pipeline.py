"""
End-to-end verification script for Singapore e-grocery multi-agent adaptation.
"""
import os
import sys
import asyncio
from pathlib import Path
from unittest.mock import MagicMock

# Stub out crawl4ai so we don't need Playwright during testing
sys.modules['crawl4ai'] = MagicMock()
sys.modules['crawl4ai.async_webcrawler'] = MagicMock()

# Add paths to sys.path
repo_root = Path("c:/Users/dance/OneDrive/Documents/Grocery Shopping Assistant/Multi-Agent-AI-Grocery-Shopping-Assistant")
sys.path.insert(0, str(repo_root / "Langraph_Agent"))
sys.path.insert(0, str(repo_root / "Web_scraper"))

async def test_singapore_scrapers():
    print("🚀 --- TEST 1: SINGAPORE SCRAPERS & MOCK FALLBACKS --- 🚀")
    from scrapers.littlefarms_scraper import LittleFarmsScraper
    from scrapers.fairprice_scraper import FairPriceScraper
    from scrapers.shengsiong_scraper import ShengSiongScraper
    from scrapers.coldstorage_scraper import ColdStorageScraper
    from scrapers.lazada_scraper import LazadaScraper
    
    scrapers_dict = {
        "Little Farms": LittleFarmsScraper(),
        "FairPrice": FairPriceScraper(),
        "Sheng Siong": ShengSiongScraper(),
        "Cold Storage": ColdStorageScraper(),
        "Lazada RedMart": LazadaScraper()
    }
    
    test_queries = ["lemons", "mineral water", "sockeye salmon"]
    
    for name, scraper in scrapers_dict.items():
        print(f"\n🏪 Testing Scraper: {name} ({scraper.get_collection_name()})")
        for query in test_queries:
            # Sockeye salmon should only return results for Little Farms
            if query == "sockeye salmon" and name != "Little Farms":
                continue
            
            res = await scraper.scrape(query)
            print(f"   🔍 Query: '{query}' -> Success: {res.get('success')}, Items Count: {res.get('items_count')}")
            if res.get("success") and res.get("items_count") > 0:
                print(f"      • Sample item url: {res['url']}")
                if "item_stats" in res:
                    print(f"      • Price range: SGD {res['item_stats']['price_stats']['min']} - SGD {res['item_stats']['price_stats']['max']}")

async def test_langgraph_pipeline():
    print("\n🚀 --- TEST 2: LANGGRAPH MULTI-STORE OPTIMIZATION --- 🚀")
    from main import ProductSearchOrchestrator
    from core.user_profile import UserProfile
    
    # Create test user profile in Singapore
    profile = UserProfile(
        user_id="test_sg_user",
        budget_limit_lkr=1000.0,
        location="Singapore"
    )
    
    orchestrator = ProductSearchOrchestrator(profile)
    
    # Test query for weekly grocery comparison
    test_query = "compare my weekly grocery cart"
    print(f"Query: '{test_query}'")
    
    result = orchestrator.process_query(test_query)
    
    print("\n✅ Optimization Complete!")
    print(f"Optimization Method: {result.get('optimization_method')}")
    print(f"Total Cost: SGD {result.get('total_cost')}")
    
    summary = result.get("budget_optimization_summary", {})
    comparisons = summary.get("single_store_comparisons", {})
    
    if comparisons:
        print("\n📊 SIDE-BY-SIDE SINGLE-STORE CART COMPARISONS:")
        print("-" * 80)
        print(f"{'Store Name':<20} | {'Subtotal (SGD)':<15} | {'Delivery Fee':<12} | {'Split Salmon':<12} | {'Total Cost (SGD)':<15}")
        print("-" * 80)
        
        for store_domain, detail in comparisons.get("stores", {}).items():
            split_active = "Yes" if detail["split_order"]["active"] else "No"
            split_info = f"${detail['split_order']['subtotal'] + detail['split_order']['delivery_fee']}" if detail["split_order"]["active"] else "$0.00"
            
            total = detail["total_cost"]
            
            print(f"{detail['name']:<20} | ${detail['subtotal']:<14.2f} | ${detail['delivery_fee']:<11.2f} | {split_info:<12} | ${total:<14.2f}")
        print("-" * 80)
        print(f"🏆 Recommended Store: {comparisons.get('best_store')} (Cheapest total cost)")
    else:
        print("❌ No single-store comparisons found in summary")

async def main():
    await test_singapore_scrapers()
    await test_langgraph_pipeline()

if __name__ == "__main__":
    asyncio.run(main())
