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
    
    # Application Settings
    MAX_RESULTS_PER_KEYWORD = 10
    DEBUG_MODE = True
    
    # Web_scraper Integration
    WEB_SCRAPER_PATH = "../Web_scraper"
