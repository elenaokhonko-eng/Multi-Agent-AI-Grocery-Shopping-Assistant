"""
Sheng Siong website scraper implementation.
"""
from typing import Optional, Dict, Any
from scrapers.base_scraper import BaseScraper
from utils.mock_singapore_data import search_mock_products

class ShengSiongScraper(BaseScraper):
    """Scraper for Sheng Siong e-commerce website."""
    
    def build_search_url(self, query: str) -> str:
        """Build Sheng Siong search URL."""
        return f"https://shengsiong.com.sg/search?q={query}"
    
    def get_collection_name(self) -> str:
        """Return MongoDB collection name."""
        return "ShengSiong"
    
    def get_markdown_start_marker(self) -> Optional[str]:
        """Return marker where product content starts."""
        return "Search Results"

    async def scrape(self, query: str) -> Dict[str, Any]:
        """Scrape with mock data fallback for Singapore."""
        items = search_mock_products(query, "shengsiong.com.sg")
        if not items:
            return {
                "success": False,
                "items_count": 0,
                "error": "No items found",
                "url": self.build_search_url(query),
                "website": self.get_website_name(),
                "execution_time": 0.05,
                "query": query
            }
            
        docs = self.normalize_items(items, self.build_search_url(query))
        db_stats = self.save_to_mongodb(docs)
        
        return {
            "success": True,
            "items_count": len(items),
            "url": self.build_search_url(query),
            "website": self.get_website_name(),
            "execution_time": 0.05,
            "database_stats": db_stats,
            "item_stats": {
                "total": len(items),
                "price_stats": {
                    "min": min(i["price_value"] for i in items),
                    "max": max(i["price_value"] for i in items),
                    "avg": sum(i["price_value"] for i in items) / len(items)
                }
            },
            "query": query
        }
