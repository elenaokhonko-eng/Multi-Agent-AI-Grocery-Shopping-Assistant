"""
OnlineKade website scraper implementation.
"""

from typing import Optional
from scrapers.base_scraper import BaseScraper

class OnlineKadeScraper(BaseScraper):
    """Scraper for OnlineKade e-commerce website."""
    
    def build_search_url(self, query: str) -> str:
        """Build OnlineKade search URL."""
        return f"https://onlinekade.lk/?s={query}&post_type=product&dgwt_wcas=1"
    
    def get_collection_name(self) -> str:
        """Return MongoDB collection name."""
        return "OnlineKade"
    
    def get_markdown_start_marker(self) -> Optional[str]:
        """Return marker where product content starts."""
        return "Products"

# Backwards compatibility function
def scrape_onlinekade(query: str):
    """Legacy function for backwards compatibility."""
    scraper = OnlineKadeScraper()
    try:
        return scraper.scrape_sync(query)
    finally:
        scraper.close()

if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "fruits"
    result = scrape_onlinekade(query)
    print(f"Scraping result: {result}")
