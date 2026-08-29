import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration settings for the web scraping application."""
    
    # API Keys and External Services
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Database Configuration
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "ecommerce_db")
    
    # Scraping Configuration
    MAX_MARKDOWN_LENGTH: int = int(os.getenv("MAX_MARKDOWN_LENGTH", "50000"))
    CRAWL_TIMEOUT: int = int(os.getenv("CRAWL_TIMEOUT", "30"))
    PRUNING_THRESHOLD: float = float(os.getenv("PRUNING_THRESHOLD", "0.48"))
    
    # Rate Limiting
    REQUEST_DELAY: float = float(os.getenv("REQUEST_DELAY", "1.0"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "data/scraper.log")
    
    # Output Configuration
    SAVE_RAW_MARKDOWN: bool = os.getenv("SAVE_RAW_MARKDOWN", "true").lower() == "true"
    SAVE_JSON_OUTPUT: bool = os.getenv("SAVE_JSON_OUTPUT", "true").lower() == "true"

class ScraperConfig:
    """Website-specific scraper configurations for Singapore."""
    
    SCRAPERS = {
        "littlefarms": {
            "name": "Little Farms",
            "base_url": "https://littlefarms.com",
            "search_path": "/search?q=",
            "collection": "LittleFarms",
            "markdown_marker": "Products",
            "rate_limit": 1.0,
        },
        "fairprice": {
            "name": "FairPrice",
            "base_url": "https://www.fairprice.com.sg",
            "search_path": "/search?query=",
            "collection": "FairPrice",
            "markdown_marker": "Search Results",
            "rate_limit": 1.5,
        },
        "shengsiong": {
            "name": "Sheng Siong",
            "base_url": "https://shengsiong.com.sg",
            "search_path": "/search?q=",
            "collection": "ShengSiong",
            "markdown_marker": "Search Results",
            "rate_limit": 1.0,
        },
        "coldstorage": {
            "name": "Cold Storage",
            "base_url": "https://coldstorage.com.sg",
            "search_path": "/search?q=",
            "collection": "ColdStorage",
            "markdown_marker": "Search Results",
            "rate_limit": 1.0,
        },
        "lazada": {
            "name": "RedMart",
            "base_url": "https://www.lazada.sg",
            "search_path": "/catalog/?q=",
            "collection": "Lazada",
            "markdown_marker": "RedMart",
            "rate_limit": 2.0,
        }
    }
