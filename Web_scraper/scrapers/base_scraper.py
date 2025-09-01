"""
Base scraper class with common functionality for all e-commerce websites.
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

import nest_asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from groq import Groq
from pymongo import MongoClient, UpdateOne

from config.settings import Config
from utils.helpers import (
    setup_logging, extract_json_from_response, clean_title, 
    validate_price, save_json_data, deduplicate_items, 
    calculate_stats
)

nest_asyncio.apply()

class BaseScraper(ABC):
    """Base class for all website scrapers with common functionality."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the base scraper with configuration."""
        self.config = config or {}
        self.logger = setup_logging(Config.LOG_LEVEL, Config.LOG_FILE)
        
        # API Configuration
        self.groq_api_key = Config.GROQ_API_KEY
        self.groq_model = Config.GROQ_MODEL
        
        # Database Configuration
        self.mongo_client = MongoClient(Config.MONGO_URI)
        self.db = self.mongo_client[Config.DATABASE_NAME]
        
        # Scraping Configuration
        self.max_markdown_length = Config.MAX_MARKDOWN_LENGTH
        self.request_delay = self.config.get("rate_limit", Config.REQUEST_DELAY)
        self.max_retries = Config.MAX_RETRIES
        
        # System prompt for LLM
        self.system_prompt = """You are a precise extraction assistant.
Given raw markdown from an e-commerce search page, extract a list of items with:
- title (concise, remove promo text)
- price_value (numeric, no currency symbols)
- currency ("LKR")

Return STRICT JSON only in this format:
{"items":[{"title":"Product Name","price_value":123.45,"currency":"LKR"}]}

Rules:
1. Extract only actual products with valid prices
2. Remove promotional text from titles
3. If duplicates exist, keep the lowest price per unique title
4. Return empty items array if no products found
5. No commentary or explanation"""

        # Track last request time for rate limiting
        self._last_request_time = 0
        
        self.logger.info(f"Initialized {self.__class__.__name__}")

    @abstractmethod
    def build_search_url(self, query: str) -> str:
        """Build the search URL for the specific website."""
        pass

    @abstractmethod
    def get_collection_name(self) -> str:
        """Return the MongoDB collection name for this scraper."""
        pass

    @abstractmethod
    def get_markdown_start_marker(self) -> Optional[str]:
        """Return the text marker where meaningful content starts."""
        pass

    def get_website_name(self) -> str:
        """Return the human-readable website name."""
        return self.__class__.__name__.replace("Scraper", "")

    async def _rate_limit(self):
        """Implement rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            await asyncio.sleep(sleep_time)
        
        self._last_request_time = time.time()

    async def fetch_markdown(self, url: str) -> str:
        """Fetch and convert webpage to markdown with retry logic."""
        await self._rate_limit()
        
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"Fetching markdown from {url} (attempt {attempt + 1})")
                
                async with AsyncWebCrawler(verbose=False) as crawler:
                    cfg = CrawlerRunConfig(
                        cache_mode=CacheMode.ENABLED,
                        excluded_tags=["nav", "footer", "aside", "script", "style"],
                        remove_overlay_elements=True,
                        markdown_generator=DefaultMarkdownGenerator(
                            content_filter=PruningContentFilter(
                                threshold=Config.PRUNING_THRESHOLD, 
                                threshold_type="fixed", 
                                min_word_threshold=0
                            ),
                            options={"ignore_links": True},
                        ),
                    )
                    result = await crawler.arun(url=url, config=cfg)
                    md = (result.markdown.raw_markdown or result.markdown.fit_markdown or "").strip()
                    
                    if md:
                        self.logger.debug(f"Successfully fetched markdown ({len(md)} chars)")
                        return md
                    else:
                        raise Exception("Empty markdown content")
                        
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise Exception(f"Failed to fetch markdown after {self.max_retries} attempts: {e}")

    def trim_markdown(self, markdown_text: str) -> str:
        """Trim markdown to relevant content based on website-specific markers."""
        if not markdown_text:
            return ""
            
        marker = self.get_markdown_start_marker()
        if marker:
            idx = markdown_text.find(marker)
            if idx != -1:
                markdown_text = markdown_text[idx:]
                self.logger.debug(f"Trimmed markdown at marker '{marker}'")
        
        return markdown_text

    async def get_llm_response(self, markdown_text: str) -> str:
        """Get structured data from LLM with error handling."""
        try:
            client = Groq(api_key=self.groq_api_key)
            
            # Truncate content to fit model limits
            user_content = markdown_text[:self.max_markdown_length]
            
            self.logger.debug(f"Sending {len(user_content)} characters to LLM")
            
            stream = client.chat.completions.create(
                model=self.groq_model,
                temperature=0,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_content}
                ],
                stream=True,
                top_p=1
            )

            buf = []
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    buf.append(content)
            
            response = "".join(buf).strip()
            self.logger.debug(f"LLM response length: {len(response)} characters")
            
            return response
            
        except Exception as e:
            self.logger.error(f"LLM request failed: {e}")
            raise

    def parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse and validate LLM response."""
        try:
            # Extract JSON from response
            json_str = extract_json_from_response(response)
            
            # Parse JSON
            data = json.loads(json_str)
            items = data.get("items", [])
            
            if not isinstance(items, list):
                self.logger.warning("LLM response items is not a list")
                return []
            
            # Validate and clean items
            valid_items = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                    
                title = clean_title(item.get("title", ""))
                price = validate_price(item.get("price_value") or item.get("price_LKR"))
                currency = item.get("currency", "LKR")
                
                if title and price is not None:
                    valid_items.append({
                        "title": title,
                        "price_value": price,
                        "currency": currency
                    })
            
            # Remove duplicates
            valid_items = deduplicate_items(valid_items)
            
            self.logger.info(f"Parsed {len(valid_items)} valid items from LLM response")
            return valid_items
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
            self.logger.debug(f"Raw response: {response[:500]}...")
            return []
        except Exception as e:
            self.logger.error(f"Error parsing LLM response: {e}")
            return []

    def normalize_items(self, items: List[Dict], url: str) -> List[Dict]:
        """Normalize extracted items and add metadata."""
        source_domain = urlparse(url).netloc or url
        now_utc = datetime.utcnow()
        
        docs = []
        for item in items:
            title = item.get("title", "")
            price_val = item.get("price_value")
            currency = item.get("currency", "LKR")
            
            doc = {
                "title": title,
                "price_LKR": price_val,
                "currency": currency,
                "source_url": url,
                "source_domain": source_domain,
                "website": self.get_website_name(),
                "scraped_at": now_utc,
                "last_updated": now_utc,
            }
            docs.append(doc)
        
        return docs

    def save_to_mongodb(self, docs: List[Dict]) -> Dict[str, int]:
        """Save documents to MongoDB with upsert logic."""
        if not docs:
            self.logger.info("No documents to save to MongoDB")
            return {"inserted": 0, "matched": 0, "modified": 0}

        collection = self.db[self.get_collection_name()]
        
        try:
            # Use upsert to avoid duplicates
            ops = [
                UpdateOne(
                    {
                        "title": doc["title"], 
                        "source_domain": doc["source_domain"]
                    },
                    {
                        "$set": doc,
                        "$setOnInsert": {"created_at": doc["scraped_at"]}
                    },
                    upsert=True,
                )
                for doc in docs
            ]
            
            result = collection.bulk_write(ops, ordered=False)
            
            stats = {
                "inserted": result.upserted_count,
                "matched": result.matched_count,
                "modified": result.modified_count
            }
            
            self.logger.info(
                f"MongoDB update: {stats['inserted']} inserted, "
                f"{stats['matched']} matched, {stats['modified']} modified"
            )
            
            return stats
            
        except Exception as e:
            self.logger.error(f"MongoDB save error: {e}")
            return {"inserted": 0, "matched": 0, "modified": 0, "error": str(e)}

    def save_raw_data(self, query: str, markdown: str, items: List[Dict], url: str):
        """Save raw data for debugging and analysis."""
        if not (Config.SAVE_RAW_MARKDOWN or Config.SAVE_JSON_OUTPUT):
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        website = self.get_website_name().lower()
        
        data_dir = Path("data") / website / timestamp
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Save query info
        query_info = {
            "query": query,
            "url": url,
            "website": website,
            "timestamp": timestamp,
            "items_count": len(items),
            "stats": calculate_stats(items)
        }
        
        save_json_data(query_info, data_dir / "query_info.json")
        
        # Save raw markdown if enabled
        if Config.SAVE_RAW_MARKDOWN:
            with open(data_dir / "raw_markdown.md", "w", encoding="utf-8") as f:
                f.write(markdown)
        
        # Save extracted items if enabled
        if Config.SAVE_JSON_OUTPUT:
            save_json_data(items, data_dir / "extracted_items.json")
        
        self.logger.debug(f"Saved raw data to {data_dir}")

    async def scrape(self, query: str) -> Dict[str, Any]:
        """Main scraping method with comprehensive error handling."""
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting scrape for query: '{query}' on {self.get_website_name()}")
            
            # Build URL and fetch content
            url = self.build_search_url(query)
            self.logger.debug(f"Search URL: {url}")
            
            # Fetch and process markdown
            markdown_text = await self.fetch_markdown(url)
            if not markdown_text:
                raise Exception("No content fetched from website")
            
            markdown_text = self.trim_markdown(markdown_text)
            self.logger.info(f"Processed markdown length: {len(markdown_text):,} characters")
            
            # Get LLM response and parse items
            llm_response = await self.get_llm_response(markdown_text)
            items = self.parse_llm_response(llm_response)
            
            if not items:
                self.logger.warning("No items extracted from LLM response")
                return {
                    "success": False,
                    "items_count": 0,
                    "error": "No items found",
                    "url": url,
                    "execution_time": time.time() - start_time
                }
            
            # Normalize and save to database
            docs = self.normalize_items(items, url)
            db_stats = self.save_to_mongodb(docs)
            
            # Save raw data for debugging
            self.save_raw_data(query, markdown_text, items, url)
            
            # Calculate final statistics
            stats = calculate_stats(items)
            execution_time = time.time() - start_time
            
            result = {
                "success": True,
                "items_count": len(items),
                "url": url,
                "website": self.get_website_name(),
                "execution_time": execution_time,
                "database_stats": db_stats,
                "item_stats": stats,
                "query": query
            }
            
            self.logger.info(
                f"Scraping completed: {len(items)} items in {execution_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            self.logger.error(f"Scraping failed: {error_msg}")
            
            return {
                "success": False,
                "items_count": 0,
                "error": error_msg,
                "url": getattr(self, '_current_url', ''),
                "website": self.get_website_name(),
                "execution_time": execution_time,
                "query": query
            }

    def scrape_sync(self, query: str) -> Dict[str, Any]:
        """Synchronous wrapper for async scrape method."""
        return asyncio.run(self.scrape(query))

    def close(self):
        """Clean up resources."""
        if hasattr(self, 'mongo_client'):
            self.mongo_client.close()
            self.logger.debug("Closed MongoDB connection")
