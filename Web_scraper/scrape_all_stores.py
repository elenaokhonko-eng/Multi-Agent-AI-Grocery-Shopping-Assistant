#!/usr/bin/env python3
"""
Universal scraper for all three stores: Glowmark, Kapruka, and OnlineKade.
Usage: python scrape_all_stores.py <keyword>
Example: python scrape_all_stores.py "rice"
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, Any, List
from pymongo import MongoClient

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from scrapers.glowmark_scraper import GlowmarkScraper
from scrapers.kapruka_scraper import KaprukaScraper
from scrapers.onlinekade_scraper import OnlineKadeScraper
from config.settings import Config

class MultiStoreScraper:
    """Scraper that handles all three stores."""
    
    def __init__(self):
        """Initialize the multi-store scraper."""
        self.scrapers = {
            "glowmark": GlowmarkScraper(),
            "kapruka": KaprukaScraper(),
            "onlinekade": OnlineKadeScraper()
        }
        
        # Database connection
        self.client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=3000)
        self.db = self.client[Config.DATABASE_NAME]
        
        self.results = {}
        
    async def scrape_single_store(self, store_name: str, scraper, query: str) -> Dict[str, Any]:
        """Scrape a single store."""
        print(f"🔄 Scraping {store_name.upper()}...")
        start_time = time.time()
        
        try:
            # Get initial document count
            collection_name = scraper.get_collection_name()
            initial_count = self.db[collection_name].count_documents({})
            
            # Perform scraping
            result = await scraper.scrape(query)
            
            # Calculate final stats
            final_count = self.db[collection_name].count_documents({})
            execution_time = time.time() - start_time
            
            if result["success"]:
                # Analyze prices in the collection
                null_prices = self.db[collection_name].count_documents({"price_LKR": None})
                valid_prices = self.db[collection_name].count_documents({"price_LKR": {"$gt": 0}})
                
                store_result = {
                    "success": True,
                    "store": store_name,
                    "items_found": result.get("items_count", 0),
                    "url": result.get("url", ""),
                    "execution_time": execution_time,
                    "database_stats": result.get("database_stats", {}),
                    "collection": collection_name,
                    "initial_count": initial_count,
                    "final_count": final_count,
                    "documents_added": final_count - initial_count,
                    "price_analysis": {
                        "null_prices": null_prices,
                        "valid_prices": valid_prices,
                        "total": final_count
                    }
                }
                
                print(f"✅ {store_name.upper()} completed!")
                print(f"   Items found: {result.get('items_count', 0)}")
                print(f"   Execution time: {execution_time:.2f}s")
                
                db_stats = result.get("database_stats", {})
                if db_stats:
                    print(f"   MongoDB: {db_stats.get('inserted', 0)} inserted, {db_stats.get('modified', 0)} modified")
                
                return store_result
                
            else:
                print(f"❌ {store_name.upper()} failed: {result.get('error', 'Unknown error')}")
                return {
                    "success": False,
                    "store": store_name,
                    "error": result.get("error", "Unknown error"),
                    "execution_time": execution_time
                }
                
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ {store_name.upper()} error: {str(e)}")
            return {
                "success": False,
                "store": store_name,
                "error": str(e),
                "execution_time": execution_time
            }
    
    async def scrape_all_stores(self, query: str, parallel: bool = True) -> Dict[str, Any]:
        """Scrape all stores either in parallel or sequentially."""
        print(f"🚀 Starting multi-store scraping for query: '{query}'")
        print("=" * 60)
        
        overall_start = time.time()
        
        if parallel:
            print("🔄 Running scrapers in PARALLEL...")
            # Run all scrapers in parallel
            tasks = [
                self.scrape_single_store(name, scraper, query)
                for name, scraper in self.scrapers.items()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, Exception):
                    print(f"❌ Exception occurred: {result}")
                else:
                    self.results[result["store"]] = result
        else:
            print("🔄 Running scrapers SEQUENTIALLY...")
            # Run scrapers one by one
            for name, scraper in self.scrapers.items():
                result = await self.scrape_single_store(name, scraper, query)
                self.results[name] = result
                
                # Add delay between stores
                if name != list(self.scrapers.keys())[-1]:  # Not the last one
                    print(f"⏳ Waiting 2 seconds before next store...")
                    await asyncio.sleep(2)
        
        overall_time = time.time() - overall_start
        
        # Generate summary
        summary = self.generate_summary(query, overall_time)
        
        return summary
    
    def generate_summary(self, query: str, total_time: float) -> Dict[str, Any]:
        """Generate a comprehensive summary of the scraping results."""
        print("\n" + "=" * 60)
        print("📊 SCRAPING SUMMARY")
        print("=" * 60)
        
        successful_stores = [r for r in self.results.values() if r.get("success")]
        failed_stores = [r for r in self.results.values() if not r.get("success")]
        
        total_items = sum(r.get("items_found", 0) for r in successful_stores)
        total_documents_added = sum(r.get("documents_added", 0) for r in successful_stores)
        
        # Price analysis across all stores
        total_null_prices = sum(r.get("price_analysis", {}).get("null_prices", 0) for r in successful_stores)
        total_valid_prices = sum(r.get("price_analysis", {}).get("valid_prices", 0) for r in successful_stores)
        total_docs = sum(r.get("price_analysis", {}).get("total", 0) for r in successful_stores)
        
        print(f"🔍 Query: '{query}'")
        print(f"⏱️  Total execution time: {total_time:.2f}s")
        print(f"✅ Successful stores: {len(successful_stores)}/3")
        print(f"❌ Failed stores: {len(failed_stores)}/3")
        print(f"📦 Total items found: {total_items}")
        print(f"📁 Total documents added to DB: {total_documents_added}")
        
        print(f"\n💰 Overall Price Analysis:")
        if total_docs > 0:
            print(f"   Total documents in DB: {total_docs}")
            print(f"   Valid prices: {total_valid_prices} ({total_valid_prices/total_docs*100:.1f}%)")
            print(f"   NULL prices: {total_null_prices} ({total_null_prices/total_docs*100:.1f}%)")
        else:
            print(f"   No documents found")
        
        print(f"\n📋 Store-by-Store Results:")
        for store_name in ["glowmark", "kapruka", "onlinekade"]:
            result = self.results.get(store_name, {})
            if result.get("success"):
                items = result.get("items_found", 0)
                time_taken = result.get("execution_time", 0)
                collection = result.get("collection", "Unknown")
                added = result.get("documents_added", 0)
                
                print(f"   ✅ {store_name.upper()}: {items} items in {time_taken:.2f}s → {collection} (+{added} docs)")
                
                # Price breakdown for this store
                pa = result.get("price_analysis", {})
                valid = pa.get("valid_prices", 0)
                null = pa.get("null_prices", 0)
                total_store = pa.get("total", 0)
                if total_store > 0:
                    print(f"      💰 Prices: {valid} valid, {null} null ({valid/total_store*100:.1f}% valid)")
            else:
                error = result.get("error", "Unknown error")
                time_taken = result.get("execution_time", 0)
                print(f"   ❌ {store_name.upper()}: FAILED in {time_taken:.2f}s - {error}")
        
        # Show some sample results
        self.show_sample_results()
        
        summary = {
            "query": query,
            "total_execution_time": total_time,
            "successful_stores": len(successful_stores),
            "failed_stores": len(failed_stores),
            "total_items_found": total_items,
            "total_documents_added": total_documents_added,
            "price_analysis": {
                "total_documents": total_docs,
                "valid_prices": total_valid_prices,
                "null_prices": total_null_prices,
                "valid_percentage": (total_valid_prices/total_docs*100) if total_docs > 0 else 0
            },
            "store_results": self.results
        }
        
        return summary
    
    def show_sample_results(self):
        """Show sample results from each successful store."""
        print(f"\n🔍 Sample Results:")
        
        for store_name in ["glowmark", "kapruka", "onlinekade"]:
            result = self.results.get(store_name, {})
            if result.get("success"):
                collection_name = result.get("collection")
                if collection_name:
                    try:
                        # Get 2 recent documents with valid prices
                        sample_docs = list(self.db[collection_name].find({
                            "price_LKR": {"$gt": 0}
                        }).sort([("scraped_at", -1)]).limit(2))
                        
                        if sample_docs:
                            print(f"   📦 {store_name.upper()} samples:")
                            for i, doc in enumerate(sample_docs, 1):
                                title = doc.get('title', 'Unknown')[:50] + "..."
                                price = doc.get('price_LKR', 0)
                                print(f"      {i}. {title}")
                                print(f"         Price: LKR {price:,.2f}")
                        else:
                            print(f"   📦 {store_name.upper()}: No samples with valid prices")
                    except Exception as e:
                        print(f"   📦 {store_name.upper()}: Error getting samples - {e}")
    
    def close(self):
        """Clean up resources."""
        for scraper in self.scrapers.values():
            try:
                scraper.close()
            except:
                pass
        
        try:
            self.client.close()
        except:
            pass

async def main():
    """Main function to handle command line arguments and run scraping."""
    if len(sys.argv) != 2:
        print("Usage: python scrape_all_stores.py <keyword>")
        print("Example: python scrape_all_stores.py 'rice'")
        sys.exit(1)
    
    keyword = sys.argv[1]
    
    if not keyword.strip():
        print("❌ Keyword cannot be empty")
        sys.exit(1)
    
    # Initialize multi-store scraper
    multi_scraper = MultiStoreScraper()
    
    try:
        # Run scraping (parallel by default, change to False for sequential)
        summary = await multi_scraper.scrape_all_stores(keyword, parallel=True)
        
        # Final status
        successful = summary["successful_stores"]
        total_items = summary["total_items_found"]
        
        print(f"\n🎯 FINAL RESULT:")
        if successful == 3:
            print(f"✅ ALL STORES SUCCESSFUL! Found {total_items} total items")
            exit_code = 0
        elif successful > 0:
            print(f"⚠️  PARTIAL SUCCESS: {successful}/3 stores completed, {total_items} total items")
            exit_code = 0
        else:
            print(f"❌ ALL STORES FAILED")
            exit_code = 1
        
        print(f"💾 Data saved to MongoDB database: {Config.DATABASE_NAME}")
        
        return exit_code
        
    except KeyboardInterrupt:
        print(f"\n⚠️  Scraping interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Clean up
        multi_scraper.close()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
