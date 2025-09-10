#!/usr/bin/env python3
"""Test script to check normalize_items method and price mapping."""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from scrapers.kapruka_scraper import KaprukaScraper
from utils.helpers import setup_logging
import json

def test_normalize_items():
    """Test the normalize_items method with sample data."""
    # Initialize scraper with empty config dict
    scraper = KaprukaScraper({})
    
    # Sample data with different price formats
    sample_data = [
        {
            'title': 'Test Product 1',
            'price_value': 1500.0,
            'description': 'Test description 1',
            'image_url': 'test1.jpg'
        },
        {
            'title': 'Test Product 2',
            'price_value': '2500.50',
            'description': 'Test description 2',
            'image_url': 'test2.jpg'
        },
        {
            'title': 'Test Product 3',
            'price_value': None,
            'description': 'Test description 3',
            'image_url': 'test3.jpg'
        },
        {
            'title': 'Test Product 4',
            'description': 'Test description 4 (no price_value)',
            'image_url': 'test4.jpg'
        }
    ]
    
    print("Original sample data:")
    print(json.dumps(sample_data, indent=2))
    print("\n" + "="*50 + "\n")
    
    # Normalize the data
    normalized = scraper.normalize_items(sample_data, 'test.com')
    
    print("Normalized data:")
    for i, item in enumerate(normalized, 1):
        print(f"Item {i}:")
        print(f"  Title: {item.get('title')}")
        print(f"  Price LKR: {item.get('price_LKR')} (type: {type(item.get('price_LKR'))})")
        print(f"  Price Value: {item.get('price_value')} (type: {type(item.get('price_value'))})")
        print(f"  Source Domain: {item.get('source_domain')}")
        print("---")

if __name__ == "__main__":
    test_normalize_items()
