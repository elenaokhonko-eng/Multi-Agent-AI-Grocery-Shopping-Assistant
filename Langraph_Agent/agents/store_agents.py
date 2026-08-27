"""
Store specific agents for multi-agent autonomous checkout flow.
"""
from typing import List, Dict, Any
import os
import json
import importlib.util
import sys
import re

import urllib.parse
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup

def extract_price_value(price_str: str) -> float:
    # Extracts the first float it finds in a string
    match = re.search(r'[\d]+\.[\d]{2}', price_str)
    if match:
        return float(match.group())
    return 0.0

class BaseStoreAgent:
    def __init__(self, store_name: str, domain: str, llm):
        self.store_name = store_name
        self.domain = domain
        self.llm = llm

    def login(self, page):
        """Playwright login flow"""
        print(f"[{self.store_name} Agent] Navigating to https://{self.domain} for login...")
        page.goto(f"https://{self.domain}", timeout=60000)
        # We would handle authentication here if needed for the specific store
        return True

    def parse_product_page(self, page, keyword: str) -> Dict[str, Any]:
        """
        Abstract method to be overridden by subclasses.
        Parses the search results page and returns the first best product match.
        Should return a dictionary with price_sgd, title, and image_url.
        """
        raise NotImplementedError("Subclasses must implement parse_product_page")

    def get_cart(self, keywords: List[str]) -> Dict[str, Any]:
        """Search for items using Playwright with Stealth and return a cart representation"""
        cart_items = []
        total_price = 0.0
        missing_items = []

        print(f"[{self.store_name} Agent] Spawning Playwright browser with stealth...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=False,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-setuid-sandbox"
                    ]
                )
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 800}
                )
                page = context.new_page()
                Stealth().apply_stealth_sync(page)
                
                self.login(page)
                
                for keyword in keywords:
                    try:
                        print(f"[{self.store_name} Agent] Searching for '{keyword}'...")
                        
                        product_data = self.parse_product_page(page, keyword)
                        
                        if product_data:
                            price = product_data.get("price_sgd", 0.0)
                            cart_item = {
                                "keyword": keyword,
                                "title": product_data.get("title", f"{keyword} (Live Web Scraped)"),
                                "price_sgd": price,
                                "price_lkr": price,
                                "quantity": 1,
                                "website": self.domain,
                                "source_url": page.url,
                                "image_url": product_data.get("image_url", ""),
                                "collection": self.store_name.lower()
                            }
                            cart_items.append(cart_item)
                            total_price += price
                        else:
                            missing_items.append(keyword)
                            print(f"[{self.store_name} Agent] No product found for {keyword}")
                            
                    except Exception as e:
                        print(f"[{self.store_name} Agent] Error searching for {keyword}: {e}")
                        missing_items.append(keyword)
                        
                browser.close()
        except Exception as e:
            print(f"[{self.store_name} Agent] Playwright failed: {e}")
            missing_items.extend(keywords)

        return {
            "store_name": self.store_name,
            "domain": self.domain,
            "items": cart_items,
            "missing_items": missing_items,
            "subtotal": total_price
        }

    def checkout(self, items: List[Dict[str, Any]]) -> bool:
        """Playwright checkout flow with safety guardrails"""
        print(f"[{self.store_name} Agent] Proceeding to checkout safely...")
        print(f"[{self.store_name} Agent] Adding {len(items)} items to cart via Playwright")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                page = context.new_page()
                Stealth().apply_stealth_sync(page)
                self.login(page)
                print(f"[{self.store_name} Agent] Navigated to cart page...")
                print(f"[{self.store_name} Agent] [SAFETY STOP]: Stopping before final payment processing to prevent accidental charges.")
                browser.close()
                return True
        except Exception as e:
            print(f"[{self.store_name} Agent] Checkout failed: {e}")
            return False

    def scrape_account_details(self, page) -> Dict[str, str]:
        """
        Abstract method. Scrapes and returns delivery address and payment method.
        """
        return {
            "address": "123 Orchard Road, #05-12, Singapore 238881 (Mocked)",
            "payment_method": "Visa ending in 4242 (Mocked)"
        }

    def get_checkout_details(self) -> Dict[str, Any]:
        """Playwright flow to login and fetch real address & payment details"""
        print(f"[{self.store_name} Agent] Fetching real checkout details safely...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                
                # Check for saved auth session
                auth_file = os.path.join(os.path.dirname(__file__), "..", "..", "Backend", "auth_sessions", f"{self.store_name.lower()}_auth.json")
                if os.path.exists(auth_file):
                    print(f"[{self.store_name} Agent] Found saved auth session: {auth_file}")
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        storage_state=auth_file
                    )
                else:
                    context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                    
                page = context.new_page()
                Stealth().apply_stealth_sync(page)
                
                # 1. Login with credentials or just rely on session
                self.login(page)
                
                # 2. Navigate to checkout or account page and scrape details
                details = self.scrape_account_details(page)
                
                browser.close()
                return details
        except Exception as e:
            print(f"[{self.store_name} Agent] Failed to fetch checkout details: {e}")
            return {
                "address": "Failed to scrape address",
                "payment_method": "Failed to scrape payment"
            }


class FairPriceAgent(BaseStoreAgent):
    def __init__(self, llm):
        super().__init__("FairPrice", "fairprice.com.sg", llm)
        
    def login(self, page):
        print(f"[{self.store_name} Agent] Checking login requirements...")
        pwd = os.environ.get("FAIRPRICE_PASSWORD", "")
        if pwd == "google-sso":
            print(f"[{self.store_name} Agent] google-sso detected. Relying on saved session from fairprice_auth.json.")
            return True
            
        print(f"[{self.store_name} Agent] Attempting real login with .env credentials...")
        user = os.environ.get("FAIRPRICE_EMAIL", "")
        page.goto(f"https://{self.domain}/login", timeout=60000)
        page.wait_for_timeout(2000)
        if user and pwd:
            print(f"[{self.store_name} Agent] Typing credentials for {user}...")
            # TODO: Add real CSS selectors for email login
        else:
            print(f"[{self.store_name} Agent] No FAIRPRICE_EMAIL found in .env, skipping real login.")
        return True

    def scrape_account_details(self, page) -> Dict[str, str]:
        print(f"[{self.store_name} Agent] Navigating to account settings to scrape details...")
        # We try to go to the address book
        page.goto(f"https://{self.domain}/account/address-book", timeout=60000)
        page.wait_for_timeout(3000)
        
        # If the page redirected to login, it means the session is missing or invalid
        if "login" in page.url:
            print(f"[{self.store_name} Agent] Redirected to login. Session missing or invalid.")
            return {
                "address": "Not logged in (Run save_fairprice_session.py)",
                "payment_method": "Not logged in"
            }
            
        # Try to extract the first address
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page.content(), 'html.parser')
            # Look for address cards
            address_divs = soup.find_all('div', attrs={"data-testid": lambda value: value and "address" in value.lower()})
            if not address_divs:
                # fallback text extraction
                text = soup.body.get_text(separator=" ", strip=True)
                if "Elena" in text or "Singapore" in text:
                    address_text = text[:150] + "..."
                else:
                    address_text = "Address book found but couldn't parse correctly."
            else:
                address_text = address_divs[0].get_text(separator=" ", strip=True)
                
            return {
                "address": address_text[:100] + ("..." if len(address_text) > 100 else ""),
                "payment_method": "Visa (Saved on Account)"
            }
        except Exception as e:
            print(f"[{self.store_name} Agent] Error scraping FairPrice address: {e}")
            
        return super().scrape_account_details(page)
        
    def parse_product_page(self, page, keyword: str) -> Dict[str, Any]:
        search_url = f"https://{self.domain}/search?query={urllib.parse.quote(keyword)}"
        page.goto(search_url, timeout=30000)
        page.wait_for_timeout(3000) # Wait for CF and hydration
        
        content = page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        price_spans = soup.find_all('span', string=re.compile(r'^\$\d+\.\d{2}$'))
        if not price_spans:
            return None
            
        first_price_span = price_spans[0]
        price_str = first_price_span.get_text()
        price = extract_price_value(price_str)
        
        title = keyword
        product_container = first_price_span.find_parent('div')
        if product_container:
            for s in product_container.find_all('span'):
                text = s.get_text().strip()
                if len(text) > 10 and '$' not in text:
                    title = text
                    break
                    
        return {
            "price_sgd": price,
            "title": title,
            "image_url": ""
        }

class RedMartAgent(BaseStoreAgent):
    def __init__(self, llm):
        super().__init__("RedMart", "redmart.lazada.sg", llm)
        
    def login(self, page):
        print(f"[{self.store_name} Agent] Checking login requirements...")
        pwd = os.environ.get("REDMART_PASSWORD", "")
        if pwd == "google-sso":
            print(f"[{self.store_name} Agent] google-sso detected. Relying on saved session from redmart_auth.json.")
            return True
        return True 

    def parse_product_page(self, page, keyword: str) -> Dict[str, Any]:
        search_url = f"https://redmart.lazada.sg/catalog/?q={urllib.parse.quote(keyword)}"
        page.goto(search_url, timeout=30000)
        page.wait_for_timeout(3000) 
        
        content = page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Look for the first product card
        product_card = soup.find('div', attrs={'data-qa-locator': 'product-item'})
        if not product_card:
            return None
            
        # Find price within that card
        price_element = product_card.find(string=re.compile(r'^\$\d+\.\d{2}$'))
        if not price_element:
            return None
            
        price = extract_price_value(price_element)
        
        # Attempt to get title
        title = keyword
        title_elem = product_card.find('a', title=True)
        if title_elem and title_elem.get('title'):
            title = title_elem.get('title')
        else:
            title = f"{keyword} (RedMart Item)"
            
        # Strict validation for RedMart/Lazada to avoid irrelevant non-grocery results (e.g., Electronics)
        keyword_words = [w.lower() for w in keyword.split() if len(w) > 2]
        if keyword_words:
            # Must have at least 50% of significant keyword words in the title
            matches = [w for w in keyword_words if w in title.lower()]
            if len(matches) / len(keyword_words) < 0.5:
                print(f"[RedMart Agent] Rejected '{title}' for keyword '{keyword}' (Insufficient keyword match: {matches})")
                return None
            
        return {
            "price_sgd": price,
            "title": title,
            "image_url": ""
        }

class ShengSiongAgent(BaseStoreAgent):
    def __init__(self, llm):
        super().__init__("ShengSiong", "shengsiong.com.sg", llm)
        self.auth_file = os.path.join(os.path.dirname(__file__), "..", "..", "Backend", "auth_sessions", "shengsiong_auth.json")

    def parse_product_page(self, page, keyword: str) -> Dict[str, Any]:
        pass

    def get_cart(self, shopping_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Override get_cart to use Playwright with saved session for Incapsula WAF bypass."""
        print(f"[{self.store_name} Agent] Searching for {len(shopping_list)} items...")
        
        cart = {
            "items": [],
            "missing_items": [],
            "subtotal": 0.0,
            "delivery_fee": 6.00,
            "total": 0.0,
            "free_delivery_threshold": 100.00
        }
        
        try:
            with sync_playwright() as p:
                if os.path.exists(self.auth_file):
                    print(f"[{self.store_name} Agent] Found saved auth session: {self.auth_file}")
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        storage_state=self.auth_file
                    )
                else:
                    print(f"[{self.store_name} Agent] WARNING: No auth session found. Run save_shengsiong_session.py to bypass WAF.")
                    browser = p.chromium.launch(headless=False)
                    context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                
                page = context.new_page()
                Stealth().apply_stealth_sync(page)

                for item in shopping_list:
                    keyword = item["item"]
                    qty = item["quantity"]
                    print(f"[{self.store_name} Agent] Searching for: {keyword}")
                    
                    search_url = f"https://shengsiong.com.sg/search?q={urllib.parse.quote(keyword)}"
                    page.goto(search_url, timeout=40000)
                    page.wait_for_timeout(3000)
                    
                    # Check for Incapsula block
                    html = page.content()
                    if "Incapsula" in html or "Pardon Our Interruption" in html:
                        print(f"[{self.store_name} Agent] Blocked by WAF for {keyword}.")
                        cart["missing_items"].append(keyword)
                        continue
                    
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    product_nodes = soup.find_all('div', class_='product-container')
                    if not product_nodes:
                        cart["missing_items"].append(keyword)
                        continue
                        
                    found = False
                    for node in product_nodes[:1]: # pick first
                        title_el = node.find('div', class_='product-title')
                        price_el = node.find('div', class_='price')
                        
                        if title_el and price_el:
                            title = title_el.get_text(strip=True)
                            price_text = price_el.get_text(strip=True).replace('$', '').replace('S', '').strip()
                            try:
                                price_sgd = float(price_text)
                                print(f"  -> Found: {title} @ ${price_sgd}")
                                cart["items"].append({
                                    "item": keyword,
                                    "title": title,
                                    "price_sgd": price_sgd,
                                    "quantity": qty,
                                    "url": search_url
                                })
                                cart["subtotal"] += price_sgd * qty
                                found = True
                            except ValueError:
                                pass
                    
                    if not found:
                        cart["missing_items"].append(keyword)

                browser.close()
                
        except Exception as e:
            print(f"[{self.store_name} Agent] Error during scraping: {e}")
            for item in shopping_list:
                if item["item"] not in [i["item"] for i in cart["items"]] and item["item"] not in cart["missing_items"]:
                    cart["missing_items"].append(item["item"])

        if cart["subtotal"] >= cart["free_delivery_threshold"]:
            cart["delivery_fee"] = 0.0
            
        cart["total"] = cart["subtotal"] + cart["delivery_fee"]
        return cart

class ColdStorageAgent(BaseStoreAgent):
    def __init__(self, llm):
        super().__init__("ColdStorage", "coldstorage.com.sg", llm)
        
    def parse_product_page(self, page, keyword: str) -> Dict[str, Any]:
        return {"price_sgd": 5.0, "title": keyword, "image_url": ""}

class LittleFarmsAgent(BaseStoreAgent):
    def __init__(self, llm):
        super().__init__("LittleFarms", "littlefarms.com", llm)
        
    def login(self, page):
        print(f"[{self.store_name} Agent] Attempting real login with .env credentials...")
        user = os.environ.get("LITTLEFARMS_EMAIL", "")
        pwd = os.environ.get("LITTLEFARMS_PASSWORD", "")
        page.goto(f"https://{self.domain}/customer/account/login/", timeout=60000)
        page.wait_for_timeout(2000)
        if user and pwd:
            print(f"[{self.store_name} Agent] Typing credentials for {user}...")
            page.fill('input[name="login[username]"]', user)
            page.fill('input[name="login[password]"]', pwd)
            page.click('button#send2')
            page.wait_for_timeout(4000)
        else:
            print(f"[{self.store_name} Agent] No LITTLEFARMS_EMAIL found in .env, skipping real login.")
        return True

    def scrape_account_details(self, page) -> Dict[str, str]:
        print(f"[{self.store_name} Agent] Navigating to account settings to scrape details...")
        
        user = os.environ.get("LITTLEFARMS_EMAIL", "")
        if not user:
            return super().scrape_account_details(page)

        try:
            # 1. Scrape Address
            page.goto(f"https://{self.domain}/customer/address/")
            page.wait_for_timeout(2000)
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(page.content(), 'html.parser')
            address_box = soup.select_one('.box-address-billing')
            address_text = address_box.get_text(separator=" ", strip=True) if address_box else "Address not found"
            address_text = address_text.replace("Default Billing Address", "").strip()
            address_text = address_text.replace("Change Billing Address", "").strip()
            final_address = address_text[:100] + ("..." if len(address_text) > 100 else "")
            
            # 2. Scrape Payment Method
            page.goto(f"https://{self.domain}/stripe/customer/paymentmethods/")
            page.wait_for_timeout(2000)
            payment_soup = BeautifulSoup(page.content(), 'html.parser')
            
            payment_table = payment_soup.select_one('.table-wrapper')
            payment_text = "No saved cards found"
            if payment_table:
                # E.g. " 6024"
                text = payment_table.get_text(separator=" ", strip=True)
                import re
                match = re.search(r'(\d{4})', text)
                if match:
                    payment_text = f"Card ending in {match.group(1)} (Saved)"
                else:
                    payment_text = text[:30] + "..."
            
            return {
                "address": final_address,
                "payment_method": payment_text
            }
        except Exception as e:
            print(f"[{self.store_name} Agent] Error scraping account details: {e}")
            return {
                "address": f"Error scraping address for {user}",
                "payment_method": "Error scraping payment method"
            }
        
    def parse_product_page(self, page, keyword: str) -> Dict[str, Any]:
        search_url = f"https://{self.domain}/catalogsearch/result/?q={urllib.parse.quote(keyword)}"
        page.goto(search_url, timeout=30000)
        page.wait_for_timeout(3000)
        
        content = page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        price = 0.0
        for span in soup.find_all(string=re.compile(r'\$\d+\.\d{2}')):
            val = extract_price_value(span)
            if val > 0:
                price = val
                break
                
        if price == 0.0:
            return None
        
        return {
            "price_sgd": price,
            "title": f"{keyword} (Little Farms)",
            "image_url": ""
        }
    
    def checkout(self, items: List[Dict[str, Any]]) -> bool:
        """Full Playwright checkout flow for Little Farms"""
        print(f"[{self.store_name} Agent] Proceeding to full autonomous checkout...")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                page = context.new_page()
                Stealth().apply_stealth_sync(page)
                
                # 1. Login
                self.login(page)
                
                # 2. Add Items to Cart
                for item in items:
                    url = item.get("source_url")
                    if url:
                        print(f"[{self.store_name} Agent] Adding {item['keyword']} to cart from {url}")
                        page.goto(url)
                        page.wait_for_timeout(3000)
                        # Execute JS to add to cart to avoid visibility issues
                        page.evaluate("if(document.querySelector('form[data-role=\"tocart-form\"]')) { document.querySelector('form[data-role=\"tocart-form\"]').submit(); }")
                        page.wait_for_timeout(4000)
                
                # 3. Navigate to Checkout
                print(f"[{self.store_name} Agent] Navigating to checkout...")
                page.goto(f"https://{self.domain}/checkout/")
                page.wait_for_timeout(8000) # Wait for checkout SPA to hydrate
                
                # 4. Shipping Step
                print(f"[{self.store_name} Agent] Processing shipping step...")
                # In Magento, the Next button usually has class .continue
                page.evaluate("if(document.querySelector('button.continue')) { document.querySelector('button.continue').click(); }")
                page.wait_for_timeout(6000)
                
                # 5. Payment & Comment Step
                print(f"[{self.store_name} Agent] Injecting order comments and selecting payment...")
                # Inject comment via JS
                comment = "intercom might not work - call me when arrive to the condo - lobby 3B"
                page.evaluate(f"if(document.querySelector('textarea#order_comment')) {{ document.querySelector('textarea#order_comment').value = '{comment}'; document.querySelector('textarea#order_comment').dispatchEvent(new Event('change')); }}")
                
                # Select vaulted card
                page.evaluate("""
                    var radios = document.querySelectorAll('input[name="payment[method]"]');
                    for (var i = 0; i < radios.length; i++) {
                        if (radios[i].value.includes('stripe') || radios[i].value.includes('vault')) {
                            radios[i].click();
                            break;
                        }
                    }
                """)
                page.wait_for_timeout(3000)
                
                # 6. Place Order
                print(f"[{self.store_name} Agent] Finalizing order placement...")
                
                # DANGER: UNCOMMENT THE FOLLOWING LINES TO ENABLE REAL PURCHASES
                # page.evaluate("if(document.querySelector('button.action.primary.checkout')) { document.querySelector('button.action.primary.checkout').click(); }")
                # page.wait_for_timeout(10000)
                # print(f"[{self.store_name} Agent] Order placed successfully! (url: {page.url})")
                print(f"[{self.store_name} Agent] [SAFETY STOP]: Order would have been placed here. Uncomment code in store_agents.py to go live.")
                
                browser.close()
                return True
        except Exception as e:
            print(f"[{self.store_name} Agent] Checkout failed: {e}")
            return False
    
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
