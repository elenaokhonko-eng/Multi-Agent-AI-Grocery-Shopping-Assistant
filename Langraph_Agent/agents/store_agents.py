"""
Store specific agents for multi-agent autonomous checkout flow.
"""
from typing import List, Dict, Any
import os
import json
import importlib.util
import sys

# Reuse the existing mock scraper logic for the MVP
# Later this will be replaced with actual MCP/Playwright logins
scraper_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Web_scraper", "utils", "mock_singapore_data.py")
spec = importlib.util.spec_from_file_location("mock_singapore_data", scraper_file)
mock_singapore_data = importlib.util.module_from_spec(spec)
sys.modules["mock_singapore_data"] = mock_singapore_data
spec.loader.exec_module(mock_singapore_data)
search_mock_products = mock_singapore_data.search_mock_products

class BaseStoreAgent:
    def __init__(self, store_name: str, domain: str, llm):
        self.store_name = store_name
        self.domain = domain
        self.llm = llm

    def login(self):
        """Mock login flow"""
        print(f"[{self.store_name} Agent] Logging into {self.domain}...")
        # Simulate authentication pause
        return True

    def get_cart(self, keywords: List[str]) -> Dict[str, Any]:
        """Search for items and return a cart representation"""
        self.login()
        cart_items = []
        total_price = 0.0
        missing_items = []

        for keyword in keywords:
            # Reusing the underlying mock logic to find items, but strictly filtering by store domain
            results = search_mock_products(keyword)
            # Filter results for this specific store
            store_results = [r for r in results if self.domain in r.get("website", "").lower()]
            
            if store_results:
                # Take the best match (first one)
                item = store_results[0]
                # Format to standard schema
                price = item.get("price_sgd", 0)
                if price == 0: price = item.get("price_lkr", 5.0)
                if price == 0: price = 5.0

                cart_item = {
                    "keyword": keyword,
                    "title": item.get("title", item.get("name", "Unknown Product")),
                    "price_sgd": price,
                    "price_lkr": price,
                    "quantity": 1,
                    "website": self.domain,
                    "source_url": item.get("source_url", ""),
                    "image_url": item.get("image_url", ""),
                    "collection": self.store_name.lower()
                }
                cart_items.append(cart_item)
                total_price += price
            else:
                missing_items.append(keyword)

        return {
            "store_name": self.store_name,
            "domain": self.domain,
            "items": cart_items,
            "missing_items": missing_items,
            "subtotal": total_price
        }

    def checkout(self, items: List[Dict[str, Any]]) -> bool:
        """Mock checkout flow to be used after final user approval"""
        print(f"[{self.store_name} Agent] Proceeding to checkout...")
        print(f"[{self.store_name} Agent] Adding {len(items)} items to cart")
        print(f"[{self.store_name} Agent] Processing payment...")
        print(f"[{self.store_name} Agent] Order successfully placed!")
        return True


class FairPriceAgent(BaseStoreAgent):
    def __init__(self, llm):
        super().__init__("FairPrice", "fairprice.com.sg", llm)

class RedMartAgent(BaseStoreAgent):
    def __init__(self, llm):
        super().__init__("RedMart", "lazada.sg", llm)

class ShengSiongAgent(BaseStoreAgent):
    def __init__(self, llm):
        super().__init__("ShengSiong", "shengsiong.com.sg", llm)

class ColdStorageAgent(BaseStoreAgent):
    def __init__(self, llm):
        super().__init__("ColdStorage", "coldstorage.com.sg", llm)

class LittleFarmsAgent(BaseStoreAgent):
    def __init__(self, llm):
        super().__init__("LittleFarms", "littlefarms.com", llm)
    
    def process_weekly_salmon_order(self):
        """Special workflow for the autonomous salmon order"""
        print("[LittleFarms Agent] Triggered autonomous weekly salmon workflow.")
        cart = self.get_cart(["Akaroa Salmon Fresh New Zealand King Salmon - Fillet"])
        
        # Check if subtotal is > 100 for free delivery
        if cart["subtotal"] >= 100:
            print("[LittleFarms Agent] Subtotal > 100 SGD. Delivery is free! Executing checkout...")
            return self.checkout(cart["items"])
        else:
            print(f"[LittleFarms Agent] Subtotal is only {cart['subtotal']} SGD. Needs to be > 100 SGD for autonomous checkout.")
            return False
