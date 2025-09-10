#!/usr/bin/env python3
"""
Simple web scraper demo without ML components.
"""

import asyncio
import json
import re
import sys
from pathlib import Path
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

class SimpleWebScraper:
    """Simple web scraper without ML dependencies"""
    
    def __init__(self):
        self.website_name = "Glowmark"
        self.base_url = "https://glomark.lk"
        
    def build_search_url(self, query: str) -> str:
        """Build search URL"""
        return f"{self.base_url}/search?search-text={query}"
    
    async def fetch_markdown(self, url: str) -> str:
        """Fetch webpage as markdown"""
        from crawl4ai import AsyncWebCrawler, CacheMode
        
        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(
                url=url,
                cache_mode=CacheMode.ENABLED,
                word_count_threshold=100,
                verbose=False
            )
            return result.markdown or ""
    
    def extract_products_simple(self, markdown: str) -> list:
        """Simple regex-based product extraction"""
        products = []
        
        # Look for patterns like: price, title, etc.
        # This is a simplified approach
        lines = markdown.split('\n')
        
        current_product = {}
        for line in lines:
            line = line.strip()
            
            # Look for price patterns (LKR, Rs, numbers)
            price_match = re.search(r'(?:LKR|Rs\.?|රු)\s*([0-9,]+\.?\d*)', line, re.IGNORECASE)
            if price_match:
                try:
                    price_str = price_match.group(1).replace(',', '')
                    price = float(price_str)
                    current_product['price'] = price
                    current_product['line'] = line
                except:
                    pass
            
            # If we have a price and this looks like a product title
            if current_product.get('price') and len(line) > 10 and len(line) < 100:
                # Simple heuristics for product titles
                if any(word in line.lower() for word in ['rice', 'dal', 'oil', 'flour', 'kg', 'g', 'ml', 'liter']):
                    current_product['title'] = line
                    products.append(current_product.copy())
                    current_product = {}
        
        return products[:10]  # Return first 10 products found
    
    async def scrape(self, query: str) -> dict:
        """Main scraping method"""
        start_time = datetime.now()
        
        try:
            print(f"🔍 Searching for '{query}' on {self.website_name}")
            
            # Build URL
            url = self.build_search_url(query)
            print(f"📡 URL: {url}")
            
            # Fetch content
            markdown = await self.fetch_markdown(url)
            print(f"📄 Fetched {len(markdown)} characters")
            
            # Extract products
            products = self.extract_products_simple(markdown)
            print(f"🛍️  Found {len(products)} products")
            
            # Display results
            for i, product in enumerate(products, 1):
                title = product.get('title', 'Unknown product')[:50]
                price = product.get('price', 0)
                print(f"  {i}. {title} - LKR {price:,.2f}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "products": products,
                "count": len(products),
                "url": url,
                "execution_time": execution_time
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            print(f"❌ Error: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time
            }

async def main():
    """Main function"""
    query = sys.argv[1] if len(sys.argv) > 1 else "rice"
    
    print("🚀 Simple Web Scraper Demo")
    print("=" * 40)
    
    scraper = SimpleWebScraper()
    result = await scraper.scrape(query)
    
    print("\n" + "=" * 40)
    print(f"⏱️  Execution time: {result['execution_time']:.2f} seconds")
    
    if result["success"]:
        print("✅ Scraping completed successfully!")
        
        # Save results
        output_file = f"scraping_results_{query}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"💾 Results saved to {output_file}")
    else:
        print("❌ Scraping failed!")

if __name__ == "__main__":
    asyncio.run(main())
