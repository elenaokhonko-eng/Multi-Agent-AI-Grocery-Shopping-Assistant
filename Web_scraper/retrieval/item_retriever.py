"""
Item retriever that combines web scraping with similarity search for optimal results.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

from retrieval.similarity_search import SimilaritySearchEngine, SearchResult
from scrapers import LittleFarmsScraper, FairPriceScraper, ShengSiongScraper, ColdStorageScraper, LazadaScraper
from config.settings import Config
from utils.helpers import setup_logging, calculate_stats, format_currency

@dataclass
class RetrievalResult:
    """Enhanced result that combines scraped and similarity search data."""
    title: str
    price_lkr: float
    currency: str
    source: str  # 'scraped' or 'similarity'
    website: str
    collection: str
    similarity_score: Optional[float] = None
    source_url: Optional[str] = None
    source_domain: Optional[str] = None
    scraped_at: Optional[str] = None
    item_id: Optional[str] = None

@dataclass
class RetrievalSummary:
    """Summary of the retrieval operation."""
    query: str
    total_results: int
    scraped_results: int
    similarity_results: int
    execution_time: float
    price_range: Optional[Dict[str, float]]
    websites_searched: List[str]
    best_match: Optional[RetrievalResult]

class ItemRetriever:
    """Advanced item retriever combining scraping and similarity search."""
    
    def __init__(self):
        """Initialize the item retriever."""
        self.logger = setup_logging(Config.LOG_LEVEL)
        
        # Initialize scrapers
        self.scrapers = {
            "littlefarms": LittleFarmsScraper(),
            "fairprice": FairPriceScraper(),
            "shengsiong": ShengSiongScraper(),
            "coldstorage": ColdStorageScraper(),
            "lazada": LazadaScraper()
        }
        
        # Initialize similarity search engine
        self.search_engine = SimilaritySearchEngine()
        
        self.logger.info("ItemRetriever initialized")

    async def scrape_fresh_data(self, query: str, sites: Optional[List[str]] = None) -> List[RetrievalResult]:
        """Scrape fresh data from e-commerce sites."""
        if sites is None:
            sites = list(self.scrapers.keys())
        
        self.logger.info(f"Scraping fresh data for '{query}' from {len(sites)} sites")
        
        # Run scrapers in parallel
        tasks = []
        for site in sites:
            if site in self.scrapers:
                scraper = self.scrapers[site]
                task = scraper.scrape(query)
                tasks.append((site, task))
        
        scraped_results = []
        
        for site, task in tasks:
            try:
                result = await task
                
                if result.get("success") and result.get("items_count", 0) > 0:
                    # Get actual items from database to build results
                    collection_name = self.scrapers[site].get_collection_name()
                    website_name = self.scrapers[site].get_website_name()
                    
                    # Query recent items from this scrape
                    from pymongo import MongoClient
                    client = MongoClient(Config.MONGO_URI)
                    db = client[Config.DATABASE_NAME]
                    collection = db[collection_name]
                    
                    # Get items from the last 5 minutes (recently scraped)
                    from datetime import datetime, timedelta
                    recent_time = datetime.utcnow() - timedelta(minutes=5)
                    
                    items = list(collection.find({
                        "scraped_at": {"$gte": recent_time}
                    }).limit(50))  # Limit to avoid too many results
                    
                    for item in items:
                        scraped_results.append(RetrievalResult(
                            title=item.get("title", ""),
                            price_lkr=item.get("price_LKR", 0.0),
                            currency=item.get("currency", "LKR"),
                            source="scraped",
                            website=website_name,
                            collection=collection_name,
                            source_url=item.get("source_url"),
                            source_domain=item.get("source_domain"),
                            scraped_at=str(item.get("scraped_at")),
                            item_id=str(item.get("_id"))
                        ))
                    
                    client.close()
                    
            except Exception as e:
                self.logger.error(f"Error scraping {site}: {e}")
        
        self.logger.info(f"Scraped {len(scraped_results)} fresh items")
        return scraped_results

    def search_similar_items(self, query: str, top_k: int = 20, min_similarity: float = 0.3) -> List[RetrievalResult]:
        """Search for similar items using semantic search."""
        self.logger.info(f"Searching similar items for '{query}'")
        
        try:
            # Ensure search engine is loaded
            if not self.search_engine.is_loaded:
                self.search_engine.load_data()
            
            # Search for similar items
            results = self.search_engine.search(query, top_k, min_similarity)
            
            # Convert to RetrievalResult format
            similarity_results = []
            for result in results:
                similarity_results.append(RetrievalResult(
                    title=result.title,
                    price_lkr=result.price_lkr or 0.0,
                    currency="LKR",
                    source="similarity",
                    website=result.website or result.collection,
                    collection=result.collection,
                    similarity_score=result.similarity_score,
                    source_domain=result.source_domain,
                    scraped_at=str(result.scraped_at) if result.scraped_at else None,
                    item_id=result.item_id
                ))
            
            self.logger.info(f"Found {len(similarity_results)} similar items")
            return similarity_results
            
        except Exception as e:
            self.logger.error(f"Error in similarity search: {e}")
            return []

    def _deduplicate_results(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """Remove duplicate results, preferring scraped over similarity results."""
        seen_titles = {}
        deduplicated = []
        
        # Sort to prioritize scraped results over similarity results
        sorted_results = sorted(results, key=lambda x: (x.source != "scraped", -x.price_lkr))
        
        for result in sorted_results:
            title_key = result.title.lower().strip()
            
            if title_key not in seen_titles:
                seen_titles[title_key] = True
                deduplicated.append(result)
            elif result.source == "scraped" and seen_titles.get(title_key):
                # Replace similarity result with scraped result
                for i, existing in enumerate(deduplicated):
                    if existing.title.lower().strip() == title_key and existing.source == "similarity":
                        deduplicated[i] = result
                        break
        
        return deduplicated

    def _rank_results(self, results: List[RetrievalResult], query: str) -> List[RetrievalResult]:
        """Rank results based on relevance, freshness, and price."""
        def calculate_score(result: RetrievalResult) -> float:
            score = 0.0
            
            # Base score from similarity (if available)
            if result.similarity_score:
                score += result.similarity_score * 0.4
            
            # Boost for exact keyword matches in title
            query_words = query.lower().split()
            title_words = result.title.lower().split()
            
            exact_matches = sum(1 for word in query_words if word in title_words)
            score += (exact_matches / len(query_words)) * 0.3
            
            # Boost for scraped vs similarity results
            if result.source == "scraped":
                score += 0.2
            
            # Small boost for reasonable prices (not too high or too low)
            if 10 <= result.price_lkr <= 100000:
                score += 0.1
            
            return score
        
        # Sort by calculated score (descending)
        ranked = sorted(results, key=calculate_score, reverse=True)
        return ranked

    async def retrieve(
        self, 
        query: str, 
        max_results: int = 20,
        include_scraping: bool = True,
        include_similarity: bool = True,
        scrape_sites: Optional[List[str]] = None,
        min_similarity: float = 0.3
    ) -> Tuple[List[RetrievalResult], RetrievalSummary]:
        """
        Retrieve items using both scraping and similarity search.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            include_scraping: Whether to include fresh scraping
            include_similarity: Whether to include similarity search
            scrape_sites: Specific sites to scrape (None for all)
            min_similarity: Minimum similarity score for similarity search
        """
        start_time = time.time()
        self.logger.info(f"Starting retrieval for query: '{query}'")
        
        all_results = []
        scraped_count = 0
        similarity_count = 0
        websites_searched = []
        
        # Fresh scraping
        if include_scraping:
            try:
                scraped_results = await self.scrape_fresh_data(query, scrape_sites)
                all_results.extend(scraped_results)
                scraped_count = len(scraped_results)
                websites_searched = scrape_sites or list(self.scrapers.keys())
            except Exception as e:
                self.logger.error(f"Error in scraping: {e}")
        
        # Similarity search
        if include_similarity:
            try:
                similarity_results = self.search_similar_items(query, max_results * 2, min_similarity)
                all_results.extend(similarity_results)
                similarity_count = len(similarity_results)
            except Exception as e:
                self.logger.error(f"Error in similarity search: {e}")
        
        # Deduplicate results
        deduplicated_results = self._deduplicate_results(all_results)
        
        # Rank results
        ranked_results = self._rank_results(deduplicated_results, query)
        
        # Limit results
        final_results = ranked_results[:max_results]
        
        # Calculate statistics
        execution_time = time.time() - start_time
        
        prices = [r.price_lkr for r in final_results if r.price_lkr > 0]
        price_range = None
        if prices:
            price_range = {
                "min": min(prices),
                "max": max(prices),
                "avg": sum(prices) / len(prices)
            }
        
        best_match = final_results[0] if final_results else None
        
        summary = RetrievalSummary(
            query=query,
            total_results=len(final_results),
            scraped_results=scraped_count,
            similarity_results=similarity_count,
            execution_time=execution_time,
            price_range=price_range,
            websites_searched=websites_searched,
            best_match=best_match
        )
        
        self.logger.info(
            f"Retrieval completed: {len(final_results)} results "
            f"({scraped_count} scraped, {similarity_count} similar) in {execution_time:.2f}s"
        )
        
        return final_results, summary

    def retrieve_sync(self, query: str, **kwargs) -> Tuple[List[RetrievalResult], RetrievalSummary]:
        """Synchronous wrapper for retrieve method."""
        return asyncio.run(self.retrieve(query, **kwargs))

    def refresh_similarity_index(self):
        """Refresh the similarity search index with latest data."""
        self.logger.info("Refreshing similarity search index...")
        self.search_engine.refresh_index()

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the retrieval system."""
        search_stats = self.search_engine.get_stats()
        
        return {
            "scrapers": {
                name: {
                    "website": scraper.get_website_name(),
                    "collection": scraper.get_collection_name()
                }
                for name, scraper in self.scrapers.items()
            },
            "similarity_search": search_stats,
            "available_features": {
                "fresh_scraping": True,
                "similarity_search": search_stats.get("loaded", False),
                "parallel_execution": True,
                "result_ranking": True
            }
        }

    def close(self):
        """Clean up resources."""
        # Close scrapers
        for scraper in self.scrapers.values():
            try:
                scraper.close()
            except Exception as e:
                self.logger.error(f"Error closing scraper: {e}")
        
        # Close search engine
        try:
            self.search_engine.close()
        except Exception as e:
            self.logger.error(f"Error closing search engine: {e}")
        
        self.logger.info("ItemRetriever closed")

# Helper functions for easy usage
async def find_best_items(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Simple function to find the best items for a query."""
    retriever = ItemRetriever()
    try:
        results, summary = await retriever.retrieve(query, max_results)
        return [asdict(result) for result in results]
    finally:
        retriever.close()

def find_best_items_sync(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Synchronous version of find_best_items."""
    return asyncio.run(find_best_items(query, max_results))

if __name__ == "__main__":
    # Example usage
    import json
    
    retriever = ItemRetriever()
    
    try:
        query = "rice"
        print(f"Searching for: '{query}'")
        
        results, summary = retriever.retrieve_sync(query, max_results=10)
        
        print(f"\nSummary:")
        print(f"  Total results: {summary.total_results}")
        print(f"  Scraped: {summary.scraped_results}")
        print(f"  Similar: {summary.similarity_results}")
        print(f"  Execution time: {summary.execution_time:.2f}s")
        
        if summary.price_range:
            print(f"  Price range: {format_currency(summary.price_range['min'])} - {format_currency(summary.price_range['max'])}")
        
        print(f"\nTop {min(5, len(results))} results:")
        for i, result in enumerate(results[:5], 1):
            print(f"{i}. {result.title}")
            print(f"   Price: {format_currency(result.price_lkr)}")
            print(f"   Source: {result.source} ({result.website})")
            if result.similarity_score:
                print(f"   Similarity: {result.similarity_score:.3f}")
            print()
        
    finally:
        retriever.close()
