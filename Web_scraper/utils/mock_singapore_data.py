"""
Mock data and search engine for Singapore grocery stores.
Contains realistic products, prices in SGD, and metadata for the 12 fixed grocery items.
"""
from typing import List, Dict, Any
import random
from datetime import datetime

MOCK_PRODUCTS = {
    "mineral water": {
        "littlefarms.com": [
            {"title": "Evian Natural Mineral Water 12x1.5L (France)", "price_value": 24.50, "image_url": "https://images.unsplash.com/photo-1608885898957-a599fb18de36?w=200"},
            {"title": "Fiji Natural Artesian Water 12x1L", "price_value": 29.90, "image_url": "https://images.unsplash.com/photo-1608885898957-a599fb18de36?w=200"}
        ],
        "fairprice.com.sg": [
            {"title": "Evian Natural Mineral Water Case 12x1.5L", "price_value": 18.90, "image_url": "https://images.unsplash.com/photo-1608885898957-a599fb18de36?w=200"},
            {"title": "Volvic Natural Mineral Water 12x1.5L", "price_value": 17.50, "image_url": "https://images.unsplash.com/photo-1608885898957-a599fb18de36?w=200"}
        ],
        "shengsiong.com.sg": [
            {"title": "Evian Natural Mineral Water 12x1.5L", "price_value": 16.80, "image_url": "https://images.unsplash.com/photo-1608885898957-a599fb18de36?w=200"},
            {"title": "Sheng Siong Spring Water 12x1.5L", "price_value": 8.50, "image_url": "https://images.unsplash.com/photo-1608885898957-a599fb18de36?w=200"}
        ],
        "coldstorage.com.sg": [
            {"title": "Evian Natural Mineral Water 12x1.5L", "price_value": 19.90, "image_url": "https://images.unsplash.com/photo-1608885898957-a599fb18de36?w=200"},
            {"title": "Fiji Natural Artesian Water Case 12x1L", "price_value": 26.50, "image_url": "https://images.unsplash.com/photo-1608885898957-a599fb18de36?w=200"}
        ],
        "lazada.sg": [
            {"title": "Evian Natural Mineral Water 12x1.5L (RedMart)", "price_value": 17.90, "image_url": "https://images.unsplash.com/photo-1608885898957-a599fb18de36?w=200"},
            {"title": "Volvic Natural Mineral Water 12x1.5L (RedMart)", "price_value": 16.90, "image_url": "https://images.unsplash.com/photo-1608885898957-a599fb18de36?w=200"}
        ]
    },
    "sparkling water": {
        "littlefarms.com": [
            {"title": "San Pellegrino Sparkling Mineral Water 24x250ml", "price_value": 39.90, "image_url": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=200"},
            {"title": "Perrier Sparkling Natural Mineral Water 24x330ml", "price_value": 44.50, "image_url": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=200"}
        ],
        "fairprice.com.sg": [
            {"title": "San Pellegrino Sparkling Natural Mineral Water 24x250ml", "price_value": 32.50, "image_url": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=200"},
            {"title": "Perrier Sparkling Water Glass 24x330ml", "price_value": 34.90, "image_url": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=200"}
        ],
        "shengsiong.com.sg": [
            {"title": "Perrier Sparkling Mineral Water Can 24x330ml", "price_value": 29.90, "image_url": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=200"},
            {"title": "San Pellegrino Sparkling Water 24x250ml", "price_value": 28.50, "image_url": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=200"}
        ],
        "coldstorage.com.sg": [
            {"title": "San Pellegrino Sparkling Mineral Water 24x250ml", "price_value": 35.90, "image_url": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=200"},
            {"title": "Perrier Sparkling Natural Mineral Water 24x330ml", "price_value": 37.50, "image_url": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=200"}
        ],
        "lazada.sg": [
            {"title": "San Pellegrino Sparkling Mineral Water 24x250ml (RedMart)", "price_value": 31.90, "image_url": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=200"},
            {"title": "Perrier Sparkling Natural Mineral Water 24x330ml (RedMart)", "price_value": 33.50, "image_url": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=200"}
        ]
    },
    "lemons": {
        "littlefarms.com": [
            {"title": "Organic Fresh Lemons (Pack of 3-4, approx 500g)", "price_value": 4.95, "image_url": "https://images.unsplash.com/photo-1590502593747-42a996133562?w=200"}
        ],
        "fairprice.com.sg": [
            {"title": "Fresh Lemons (Pack of 3-4, approx 500g)", "price_value": 2.50, "image_url": "https://images.unsplash.com/photo-1590502593747-42a996133562?w=200"}
        ],
        "shengsiong.com.sg": [
            {"title": "Fresh Lemons (Pack of 4)", "price_value": 1.95, "image_url": "https://images.unsplash.com/photo-1590502593747-42a996133562?w=200"}
        ],
        "coldstorage.com.sg": [
            {"title": "Fresh Lemons imported (Pack of 4)", "price_value": 2.95, "image_url": "https://images.unsplash.com/photo-1590502593747-42a996133562?w=200"}
        ],
        "lazada.sg": [
            {"title": "Fresh Lemons Pack (approx 500g)", "price_value": 2.30, "image_url": "https://images.unsplash.com/photo-1590502593747-42a996133562?w=200"}
        ]
    },
    "sockeye salmon": {
        "littlefarms.com": [
            {"title": "Little Farms New Zealand Wild Caught Sockeye Salmon (approx 1kg)", "price_value": 72.50, "image_url": "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=200"}
        ]
        # Rest of the stores do NOT sell New Zealand Wild Sockeye Salmon from Little Farms
    },
    "salmon skin": {
        "littlefarms.com": [
            {"title": "Irvins Salted Egg Salmon Skin Snack Packet 105g", "price_value": 9.50, "image_url": "https://images.unsplash.com/photo-1599490659213-e2b9527bb087?w=200"}
        ],
        "fairprice.com.sg": [
            {"title": "Irvins Salted Egg Salmon Skin Packet 105g", "price_value": 8.00, "image_url": "https://images.unsplash.com/photo-1599490659213-e2b9527bb087?w=200"}
        ],
        "shengsiong.com.sg": [
            {"title": "Irvins Salted Egg Salmon Skin 105g", "price_value": 7.80, "image_url": "https://images.unsplash.com/photo-1599490659213-e2b9527bb087?w=200"}
        ],
        "coldstorage.com.sg": [
            {"title": "Irvins Salted Egg Salmon Skin Original 105g", "price_value": 8.20, "image_url": "https://images.unsplash.com/photo-1599490659213-e2b9527bb087?w=200"}
        ],
        "lazada.sg": [
            {"title": "Irvins Salted Egg Salmon Skin Snack (105g)", "price_value": 7.95, "image_url": "https://images.unsplash.com/photo-1599490659213-e2b9527bb087?w=200"}
        ]
    },
    "macadamia nuts": {
        "littlefarms.com": [
            {"title": "Premium Raw Macadamia Nuts Packet 250g", "price_value": 9.90, "image_url": "https://images.unsplash.com/photo-1585250953683-9bc7d853e3fa?w=200"}
        ],
        "fairprice.com.sg": [
            {"title": "FairPrice Roasted Macadamia Nuts 250g", "price_value": 6.80, "image_url": "https://images.unsplash.com/photo-1585250953683-9bc7d853e3fa?w=200"}
        ],
        "shengsiong.com.sg": [
            {"title": "Sheng Siong Raw Macadamia Nuts 250g", "price_value": 5.95, "image_url": "https://images.unsplash.com/photo-1585250953683-9bc7d853e3fa?w=200"}
        ],
        "coldstorage.com.sg": [
            {"title": "Meadows Premium Baked Macadamia Nuts 250g", "price_value": 7.50, "image_url": "https://images.unsplash.com/photo-1585250953683-9bc7d853e3fa?w=200"}
        ],
        "lazada.sg": [
            {"title": "RedMart Baked Macadamia Nuts 250g", "price_value": 6.50, "image_url": "https://images.unsplash.com/photo-1585250953683-9bc7d853e3fa?w=200"}
        ]
    },
    "berries": {
        "littlefarms.com": [
            {"title": "Fresh Sweet Blueberries Packet 125g", "price_value": 5.90, "image_url": "https://images.unsplash.com/photo-1601004890684-d8cbf643f5f2?w=200"},
            {"title": "Fresh Raspberries punnet 125g", "price_value": 6.20, "image_url": "https://images.unsplash.com/photo-1577069861033-55d04cec4ef5?w=200"}
        ],
        "fairprice.com.sg": [
            {"title": "Fresh Blueberries punnet 125g", "price_value": 3.95, "image_url": "https://images.unsplash.com/photo-1601004890684-d8cbf643f5f2?w=200"},
            {"title": "Fresh Raspberries punnet 125g", "price_value": 4.50, "image_url": "https://images.unsplash.com/photo-1577069861033-55d04cec4ef5?w=200"}
        ],
        "shengsiong.com.sg": [
            {"title": "Fresh Blueberries 125g", "price_value": 2.95, "image_url": "https://images.unsplash.com/photo-1601004890684-d8cbf643f5f2?w=200"},
            {"title": "Fresh Blackberries 125g", "price_value": 3.20, "image_url": "https://images.unsplash.com/photo-1577069861033-55d04cec4ef5?w=200"}
        ],
        "coldstorage.com.sg": [
            {"title": "Fresh Blueberries imported 125g", "price_value": 4.20, "image_url": "https://images.unsplash.com/photo-1601004890684-d8cbf643f5f2?w=200"},
            {"title": "Fresh Raspberries punnet 125g", "price_value": 4.90, "image_url": "https://images.unsplash.com/photo-1577069861033-55d04cec4ef5?w=200"}
        ],
        "lazada.sg": [
            {"title": "Fresh Blueberries 125g (RedMart)", "price_value": 3.80, "image_url": "https://images.unsplash.com/photo-1601004890684-d8cbf643f5f2?w=200"},
            {"title": "Fresh Raspberries 125g (RedMart)", "price_value": 4.20, "image_url": "https://images.unsplash.com/photo-1577069861033-55d04cec4ef5?w=200"}
        ]
    },
    "trash bags": {
        "littlefarms.com": [
            {"title": "Ecover Biodegradable Heavy Duty Trash Bags (Roll of 20)", "price_value": 8.90, "image_url": "https://images.unsplash.com/photo-1618090584126-129cd1f3fbaa?w=200"}
        ],
        "fairprice.com.sg": [
            {"title": "Glad Heavy Duty Garbage Trash Bags - Medium (Roll of 30)", "price_value": 5.60, "image_url": "https://images.unsplash.com/photo-1618090584126-129cd1f3fbaa?w=200"}
        ],
        "shengsiong.com.sg": [
            {"title": "Sheng Siong Durable Garbage Trash Bags (Roll of 40)", "price_value": 3.80, "image_url": "https://images.unsplash.com/photo-1618090584126-129cd1f3fbaa?w=200"}
        ],
        "coldstorage.com.sg": [
            {"title": "Glad Drawstring Trash Garbage Bags (Roll of 30)", "price_value": 6.20, "image_url": "https://images.unsplash.com/photo-1618090584126-129cd1f3fbaa?w=200"}
        ],
        "lazada.sg": [
            {"title": "Glad Medium Drawstring Garbage Trash Bags 30s", "price_value": 5.40, "image_url": "https://images.unsplash.com/photo-1618090584126-129cd1f3fbaa?w=200"}
        ]
    },
    "washing powder": {
        "littlefarms.com": [
            {"title": "Ecover Zero Eco Laundry Washing Powder Concentrate 1.8kg", "price_value": 26.90, "image_url": "https://images.unsplash.com/photo-1610557892470-76d747eed2f3?w=200"}
        ],
        "fairprice.com.sg": [
            {"title": "Dynamo Power Gel Laundry Detergent Liquid 2.7kg", "price_value": 12.50, "image_url": "https://images.unsplash.com/photo-1610557892470-76d747eed2f3?w=200"},
            {"title": "Attack Ultra Power Washing Powder Detergent 3kg", "price_value": 10.90, "image_url": "https://images.unsplash.com/photo-1610557892470-76d747eed2f3?w=200"}
        ],
        "shengsiong.com.sg": [
            {"title": "Dynamo Power Gel Laundry Detergent 2.7kg", "price_value": 11.20, "image_url": "https://images.unsplash.com/photo-1610557892470-76d747eed2f3?w=200"},
            {"title": "Attack Color Detergent Washing Powder 3kg", "price_value": 9.50, "image_url": "https://images.unsplash.com/photo-1610557892470-76d747eed2f3?w=200"}
        ],
        "coldstorage.com.sg": [
            {"title": "Dynamo Power Gel Laundry Detergent Liquid 2.7kg", "price_value": 13.90, "image_url": "https://images.unsplash.com/photo-1610557892470-76d747eed2f3?w=200"},
            {"title": "Breeze Power Clean Washing Powder 3kg", "price_value": 11.50, "image_url": "https://images.unsplash.com/photo-1610557892470-76d747eed2f3?w=200"}
        ],
        "lazada.sg": [
            {"title": "Dynamo Power Gel Laundry Liquid Detergent 2.7kg (RedMart)", "price_value": 11.90, "image_url": "https://images.unsplash.com/photo-1610557892470-76d747eed2f3?w=200"},
            {"title": "Breeze Power Clean Detergent Washing Powder 3kg (RedMart)", "price_value": 10.50, "image_url": "https://images.unsplash.com/photo-1610557892470-76d747eed2f3?w=200"}
        ]
    },
    "bell peppers": {
        "littlefarms.com": [
            {"title": "Premium Organic Yellow Bell Peppers (Pack of 3)", "price_value": 6.90, "image_url": "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=200"}
        ],
        "fairprice.com.sg": [
            {"title": "Fresh Yellow Capsicum Bell Peppers (3 pieces)", "price_value": 3.80, "image_url": "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=200"}
        ],
        "shengsiong.com.sg": [
            {"title": "Fresh Yellow Bell Peppers Capsicum (3 pieces)", "price_value": 2.95, "image_url": "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=200"}
        ],
        "coldstorage.com.sg": [
            {"title": "Fresh Yellow Bell Peppers (Pack of 3)", "price_value": 4.50, "image_url": "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=200"}
        ],
        "lazada.sg": [
            {"title": "Fresh Yellow Bell Peppers Capsicum (3 pieces, RedMart)", "price_value": 3.50, "image_url": "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=200"}
        ]
    },
    "eggs": {
        "littlefarms.com": [
            {"title": "Nuegg Intense Egg Yolk Premium Eggs (Pack of 10)", "price_value": 8.50, "image_url": "https://images.unsplash.com/photo-1506976785307-8732e854ad03?w=200"}
        ],
        "fairprice.com.sg": [
            {"title": "Nuegg Intense Egg Yolk Premium Eggs (Pack of 10)", "price_value": 6.20, "image_url": "https://images.unsplash.com/photo-1506976785307-8732e854ad03?w=200"}
        ],
        "shengsiong.com.sg": [
            {"title": "Nuegg Intense Egg Yolk Premium Eggs (Pack of 10)", "price_value": 5.80, "image_url": "https://images.unsplash.com/photo-1506976785307-8732e854ad03?w=200"}
        ],
        "coldstorage.com.sg": [
            {"title": "Nuegg Intense Egg Yolk Premium Eggs (Pack of 10)", "price_value": 6.90, "image_url": "https://images.unsplash.com/photo-1506976785307-8732e854ad03?w=200"}
        ],
        "lazada.sg": [
            {"title": "Nuegg Intense Egg Yolk Premium Eggs (Pack of 10, RedMart)", "price_value": 5.95, "image_url": "https://images.unsplash.com/photo-1506976785307-8732e854ad03?w=200"}
        ]
    },
    "kopi o": {
        "littlefarms.com": [
            {"title": "Gold Roast Traditional Kopi O Kosong Bags (Pack of 20)", "price_value": 7.50, "image_url": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=200"}
        ],
        "fairprice.com.sg": [
            {"title": "Gold Roast Traditional Kopi O Kosong Bags 20s", "price_value": 5.20, "image_url": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=200"}
        ],
        "shengsiong.com.sg": [
            {"title": "Gold Roast Traditional Kopi O Kosong Bags 20s", "price_value": 4.50, "image_url": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=200"}
        ],
        "coldstorage.com.sg": [
            {"title": "Gold Roast Traditional Kopi O Kosong Bags 20s", "price_value": 5.50, "image_url": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=200"}
        ],
        "lazada.sg": [
            {"title": "Gold Roast Traditional Kopi O Kosong Bags 20s (RedMart)", "price_value": 4.95, "image_url": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=200"}
        ]
    },
    "spinach": {
        "littlefarms.com": [
            {"title": "Organic Fresh Baby Spinach (punnet 250g)", "price_value": 5.90, "image_url": "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=200"}
        ],
        "fairprice.com.sg": [
            {"title": "Fresh Baby Spinach (packet 250g)", "price_value": 3.50, "image_url": "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=200"}
        ],
        "shengsiong.com.sg": [
            {"title": "Fresh Local Chinese Spinach (packet 250g)", "price_value": 1.95, "image_url": "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=200"}
        ],
        "coldstorage.com.sg": [
            {"title": "Fresh Baby Spinach imported (packet 250g)", "price_value": 3.90, "image_url": "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=200"}
        ],
        "lazada.sg": [
            {"title": "Fresh Baby Spinach packet 250g (RedMart)", "price_value": 3.20, "image_url": "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=200"}
        ]
    }
}

def search_mock_products(query: str, store_domain: str) -> List[Dict[str, Any]]:
    """Search mock products matching the query for a specific store."""
    query_lower = query.lower()
    
    # Map general search query to our mock keys
    matched_key = None
    for key in MOCK_PRODUCTS.keys():
        if key in query_lower or query_lower in key:
            matched_key = key
            break
            
    # Extra mappings
    if not matched_key:
        if "water" in query_lower:
            if "sparkling" in query_lower:
                matched_key = "sparkling water"
            else:
                matched_key = "mineral water"
        elif "lemon" in query_lower:
            matched_key = "lemons"
        elif "salmon" in query_lower:
            if "skin" in query_lower:
                matched_key = "salmon skin"
            else:
                matched_key = "sockeye salmon"
        elif "nut" in query_lower or "macadamia" in query_lower:
            matched_key = "macadamia nuts"
        elif "berry" in query_lower or "berries" in query_lower or "blueberry" in query_lower or "raspberry" in query_lower:
            matched_key = "berries"
        elif "bag" in query_lower or "trash" in query_lower:
            matched_key = "trash bags"
        elif "wash" in query_lower or "detergent" in query_lower or "powder" in query_lower:
            matched_key = "washing powder"
        elif "pepper" in query_lower or "capsicum" in query_lower:
            matched_key = "bell peppers"
        elif "egg" in query_lower:
            matched_key = "eggs"
        elif "kopi" in query_lower or "coffee" in query_lower:
            matched_key = "kopi o"
        elif "spinach" in query_lower:
            matched_key = "spinach"

    if not matched_key:
        return []
        
    store_products = MOCK_PRODUCTS.get(matched_key, {}).get(store_domain, [])
    
    # Standardize result format
    results = []
    for p in store_products:
        results.append({
            "title": p["title"],
            "price_value": p["price_value"],
            "currency": "SGD",
            "image_url": p["image_url"],
            "website": store_domain,
            "scraped_at": datetime.utcnow()
        })
    return results
