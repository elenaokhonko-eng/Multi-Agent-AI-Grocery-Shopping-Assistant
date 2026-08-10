"""
Scrapers package for Singapore e-grocery websites.
"""

from .littlefarms_scraper import LittleFarmsScraper
from .fairprice_scraper import FairPriceScraper
from .shengsiong_scraper import ShengSiongScraper
from .coldstorage_scraper import ColdStorageScraper
from .lazada_scraper import LazadaScraper
from .base_scraper import BaseScraper

__all__ = [
    'BaseScraper',
    'LittleFarmsScraper',
    'FairPriceScraper',
    'ShengSiongScraper',
    'ColdStorageScraper',
    'LazadaScraper'
]
