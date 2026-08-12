"""
Configuration settings for the Langraph application
"""
import os


class Config:
    """Application configuration"""
    
    # LLM API Configuration
    OLLAMA_BASE_URL = "http://localhost:11434"
    OLLAMA_MODEL = "llama3.1:8b"
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    GROQ_MODEL = OLLAMA_MODEL # fallback for older config references
    GROQ_TEMPERATURE = 0
    LANGSMITH_API_KEY = "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"
    # Application Settings
    MAX_RESULTS_PER_KEYWORD = 10
    DEBUG_MODE = True
    
    # Web_scraper Integration
    WEB_SCRAPER_PATH = "../Web_scraper"
