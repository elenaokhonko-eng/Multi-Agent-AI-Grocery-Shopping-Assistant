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
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb+srv://yasirunipunbasnayake2_db_user:hFIS1XVxBmbaC5Ro@techtitans0.c5azljc.mongodb.net/")
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
    """Website-specific scraper configurations."""
    
    SCRAPERS = {
        "glowmark": {
            "name": "Glowmark",
            "base_url": "https://glomark.lk",
            "search_path": "/search?search-text=",
            "collection": "Glowmark",
            "markdown_marker": "By Price",
            "rate_limit": 1.0,
        },
        "kapruka": {
            "name": "Kapruka", 
            "base_url": "https://www.kapruka.com",
            "search_path": "/srilanka_online_search.jsp?d=",
            "collection": "Kapruka",
            "markdown_marker": "in Kapruka",
            "rate_limit": 1.0,
        },
        "onlinekade": {
            "name": "OnlineKade",
            "base_url": "https://onlinekade.lk",
            "search_path": "/?s={}&post_type=product&dgwt_wcas=1",
            "collection": "OnlineKade", 
            "markdown_marker": "Products",
            "rate_limit": 1.0,
        }
    }
