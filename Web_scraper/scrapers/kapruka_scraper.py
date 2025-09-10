"""
Kapruka website scraper implementation.
"""

from typing import Optional
from scrapers.base_scraper import BaseScraper

class KaprukaScraper(BaseScraper):
    """Scraper for Kapruka e-commerce website."""
    
    def build_search_url(self, query: str) -> str:
        """Build Kapruka search URL."""
        return f"https://www.kapruka.com/srilanka_online_search.jsp?d={query}"
    
    def get_collection_name(self) -> str:
        """Return MongoDB collection name."""
        return "Kapruka"  # Keeping original spelling from your code
    
    def get_markdown_start_marker(self) -> Optional[str]:
        """Return marker where product content starts."""
        return "in Kapruka"

# Backwards compatibility function
def scrape_kapruka(query: str):
    """Legacy function for backwards compatibility."""
    scraper = KaprukaScraper()
    try:
        return scraper.scrape_sync(query)
    finally:
        scraper.close()

if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "fruits"
    result = scrape_kapruka(query)
    print(f"Scraping result: {result}")
