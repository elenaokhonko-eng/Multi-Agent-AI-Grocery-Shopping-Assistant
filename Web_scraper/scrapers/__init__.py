"""
Scrapers package for different e-commerce websites.
"""

from .glowmark_scraper import GlowmarkScraper, scrape_glowmark
from .kapruka_scraper import KaprukaScraper, scrape_kapruka
from .onlinekade_scraper import OnlineKadeScraper, scrape_onlinekade
from .base_scraper import BaseScraper

__all__ = [
    'BaseScraper',
    'GlowmarkScraper', 'scrape_glowmark',
    'KaprukaScraper', 'scrape_kapruka', 
    'OnlineKadeScraper', 'scrape_onlinekade'
]
