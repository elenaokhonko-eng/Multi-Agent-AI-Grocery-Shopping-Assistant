"""
Utility functions for the web scraping application.
"""

import re
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration."""
    logger = logging.getLogger("scraper")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if log_file is specified
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def extract_json_from_response(response: str) -> str:
    """Extract JSON object from LLM response."""
    start = response.find("{")
    end = response.rfind("}")
    return response[start:end+1] if start != -1 and end != -1 and end > start else response

def clean_title(title: str) -> str:
    """Clean and normalize product titles."""
    if not title:
        return ""
    
    # Remove extra whitespace
    title = re.sub(r'\s+', ' ', title.strip())
    
    # Remove common promotional text
    promo_patterns = [
        r'\b(sale|offer|discount|special|limited|free shipping|new arrival)\b',
        r'\b\d+%\s*off\b',
        r'\b(rs\.?|lkr\.?)\s*\d+\b',
        r'\b(quick view|add to cart|buy now)\b'
    ]
    
    for pattern in promo_patterns:
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)
    
    # Clean up extra spaces again
    title = re.sub(r'\s+', ' ', title.strip())
    
    return title

def validate_price(price: Any) -> Optional[float]:
    """Validate and normalize price values."""
    if price is None:
        return None
    
    try:
        # Handle string prices
        if isinstance(price, str):
            # Remove currency symbols and commas
            price_clean = re.sub(r'[^\d.]', '', price)
            if not price_clean:
                return None
            price = float(price_clean)
        else:
            price = float(price)
        
        # Validate price is reasonable (between 1 and 1,000,000 LKR)
        if 1 <= price <= 1_000_000:
            return round(price, 2)
        else:
            return None
            
    except (ValueError, TypeError):
        return None

def save_json_data(data: Dict[Any, Any], filepath: str) -> bool:
    """Save data to JSON file safely."""
    try:
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        return True
    except Exception as e:
        logging.getLogger("scraper").error(f"Error saving JSON data: {e}")
        return False

def load_json_data(filepath: str) -> Optional[Dict[Any, Any]]:
    """Load data from JSON file safely."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.getLogger("scraper").error(f"Error loading JSON data: {e}")
        return None

def create_backup_filename(original_path: str) -> str:
    """Create a backup filename with timestamp."""
    path = Path(original_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return str(path.parent / f"{path.stem}_{timestamp}{path.suffix}")

def deduplicate_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate items, keeping the one with lowest price."""
    seen_titles = {}
    
    for item in items:
        title = item.get("title", "").strip().lower()
        price = validate_price(item.get("price_value") or item.get("price_LKR"))
        
        if not title or price is None:
            continue
            
        if title not in seen_titles or price < seen_titles[title]["price_LKR"]:
            seen_titles[title] = {
                "title": item.get("title", "").strip(),
                "price_LKR": price,
                "currency": item.get("currency", "LKR")
            }
    
    return list(seen_titles.values())

def format_currency(amount: float, currency: str = "LKR") -> str:
    """Format currency amount for display."""
    return f"{currency} {amount:,.2f}"

def calculate_stats(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate statistics for scraped items."""
    if not items:
        return {"count": 0}
    
    prices = [item.get("price_LKR", 0) for item in items if item.get("price_LKR")]
    
    if not prices:
        return {"count": len(items), "price_stats": None}
    
    return {
        "count": len(items),
        "price_stats": {
            "min": min(prices),
            "max": max(prices),
            "avg": sum(prices) / len(prices),
            "median": sorted(prices)[len(prices) // 2]
        }
    }
