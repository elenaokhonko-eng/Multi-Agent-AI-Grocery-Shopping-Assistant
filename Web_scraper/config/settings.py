import os
from typing import Optional

class Config:
    """Configuration settings for the web scraping application."""
    
    # API Keys and External Services
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "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")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL")

    # Database Configuration
    MONGO_URI: str = os.getenv("MONGO_URI")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME")
    
    # Scraping Configuration
    MAX_MARKDOWN_LENGTH: int = int(os.getenv("MAX_MARKDOWN_LENGTH"))
    CRAWL_TIMEOUT: int = int(os.getenv("CRAWL_TIMEOUT"))
    PRUNING_THRESHOLD: float = float(os.getenv("PRUNING_THRESHOLD"))
    
    # Rate Limiting
    REQUEST_DELAY: float = float(os.getenv("REQUEST_DELAY"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES"))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL")
    LOG_FILE: str = os.getenv("LOG_FILE")
    
    # Output Configuration
    SAVE_RAW_MARKDOWN: bool = os.getenv("SAVE_RAW_MARKDOWN").lower() == "true"
    SAVE_JSON_OUTPUT: bool = os.getenv("SAVE_JSON_OUTPUT").lower() == "true"

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
            "collection": "Kapuruka",
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
