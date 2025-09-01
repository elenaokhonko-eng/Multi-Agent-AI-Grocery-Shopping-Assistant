"""
Glowmark website scraper implementation.
"""

from typing import Optional
from scrapers.base_scraper import BaseScraper

class GlowmarkScraper(BaseScraper):
    """Scraper for Glowmark e-commerce website."""
    
    def build_search_url(self, query: str) -> str:
        """Build Glowmark search URL."""
        return f"https://glomark.lk/search?search-text={query}"
    
    def get_collection_name(self) -> str:
        """Return MongoDB collection name."""
        return "Glowmark"
    
    def get_markdown_start_marker(self) -> Optional[str]:
        """Return marker where product content starts."""
        return "By Price"

# Backwards compatibility function
def scrape_glowmark(query: str):
    """Legacy function for backwards compatibility."""
    scraper = GlowmarkScraper()
    try:
        return scraper.scrape_sync(query)
    finally:
        scraper.close()

if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "fruits"
    result = scrape_glowmark(query)
    print(f"Scraping result: {result}")
