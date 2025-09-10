"""
Configuration settings for the Langraph application
"""
import os


class Config:
    """Application configuration"""
    
    # Groq API Configuration
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
    GROQ_MODEL = "llama-3.3-70b-versatile"
    GROQ_TEMPERATURE = 0
    LANGSMITH_API_KEY = "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"
    # Application Settings
    MAX_RESULTS_PER_KEYWORD = 10
    DEBUG_MODE = True
    
    # Web_scraper Integration
    WEB_SCRAPER_PATH = "../Web_scraper"
