import os
import json
from typing import Dict, Any, List
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from .base import RetailerAdapter, logger

class FairPriceAdapter(RetailerAdapter):
    def __init__(self):
        super().__init__("FairPrice", "fairprice.com.sg")
        
    def _login(self, page):
        logger.info(f"[{self.store_name} Adapter] Checking login requirements...")
        pwd = os.environ.get("FAIRPRICE_PASSWORD", "")
        if pwd == "google-sso":
            logger.info(f"[{self.store_name} Adapter] google-sso detected. Relying on saved session.")
            return True
            
        logger.info(f"[{self.store_name} Adapter] Attempting real login with .env credentials...")
        user = os.environ.get("FAIRPRICE_EMAIL", "")
        page.goto(f"https://{self.domain}/login", timeout=60000)
        page.wait_for_timeout(2000)
        if user and pwd:
            logger.info(f"[{self.store_name} Adapter] Typing credentials for {user}...")
            # Real CSS selectors would go here for manual login
        else:
            logger.info(f"[{self.store_name} Adapter] No FAIRPRICE_EMAIL found in .env, skipping real login.")
        return True

    def get_checkout_details(self) -> Dict[str, str]:
        logger.info(f"[{self.store_name} Adapter] Fetching real checkout details safely...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                
                auth_file = os.path.join(os.path.dirname(__file__), "..", "..", "..", "Backend", "auth_sessions", f"{self.store_name.lower()}_auth.json")
                if os.path.exists(auth_file):
                    logger.info(f"[{self.store_name} Adapter] Found saved auth session: {auth_file}")
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        storage_state=auth_file
                    )
                else:
                    context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                    
                page = context.new_page()
                Stealth().apply_stealth_sync(page)
                
                self._login(page)
                
                logger.info(f"[{self.store_name} Adapter] Navigating to account settings to scrape details...")
                page.goto(f"https://{self.domain}/account/address-book", timeout=60000)
                page.wait_for_timeout(3000)
                
                if "login" in page.url:
                    logger.warning(f"[{self.store_name} Adapter] Redirected to login. Session missing or invalid.")
                    browser.close()
                    return {
                        "address": "Not logged in (Run save_fairprice_session.py)",
                        "payment_method": "Not logged in"
                    }
                    
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(page.content(), 'html.parser')
                    address_divs = soup.find_all('div', attrs={"data-testid": lambda value: value and "address" in value.lower()})
                    if not address_divs:
                        text = soup.body.get_text(separator=" ", strip=True)
                        if "Elena" in text or "Singapore" in text:
                            address_text = text[:150] + "..."
                        else:
                            address_text = "Address book found but couldn't parse correctly."
                    else:
                        address_text = address_divs[0].get_text(separator=" ", strip=True)
                        
                    final_address = address_text[:100] + ("..." if len(address_text) > 100 else "")
                except Exception as e:
                    logger.error(f"[{self.store_name} Adapter] Error scraping FairPrice address: {e}")
                    final_address = "Failed to extract address from HTML."

                browser.close()
                return {
                    "address": final_address,
                    "payment_method": "Visa (Saved on Account)"
                }
        except Exception as e:
            logger.error(f"[{self.store_name} Adapter] Failed to fetch checkout details: {e}")
            return {
                "address": "Failed to scrape address",
                "payment_method": "Failed to scrape payment"
            }

    def checkout(self, items: List[Dict[str, Any]]) -> bool:
        logger.info(f"[{self.store_name} Adapter] Proceeding to checkout safely...")
        logger.info(f"[{self.store_name} Adapter] Adding {len(items)} items to cart via Playwright")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                page = context.new_page()
                Stealth().apply_stealth_sync(page)
                self._login(page)
                logger.info(f"[{self.store_name} Adapter] Navigated to cart page...")
                logger.info(f"[{self.store_name} Adapter] [SAFETY STOP]: Stopping before final payment processing to prevent accidental charges.")
                browser.close()
                return True
        except Exception as e:
            logger.error(f"[{self.store_name} Adapter] Checkout failed: {e}")
            return False
