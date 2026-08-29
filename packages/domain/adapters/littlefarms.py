import os
from typing import Any

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

from .base import RetailerAdapter, logger


class LittleFarmsAdapter(RetailerAdapter):
    def __init__(self):
        super().__init__("LittleFarms", "littlefarms.com")

    def _login(self, page):
        logger.info(f"[{self.store_name} Adapter] Attempting real login with .env credentials...")
        user = os.environ.get("LITTLEFARMS_EMAIL", "")
        pwd = os.environ.get("LITTLEFARMS_PASSWORD", "")
        page.goto(f"https://{self.domain}/customer/account/login/", timeout=60000)
        page.wait_for_timeout(2000)
        if user and pwd:
            logger.info(f"[{self.store_name} Adapter] Typing credentials for {user}...")
            page.fill('input[name="login[username]"]', user)
            page.fill('input[name="login[password]"]', pwd)
            page.click('button#send2')
            page.wait_for_timeout(4000)
        else:
            logger.info(f"[{self.store_name} Adapter] No LITTLEFARMS_EMAIL found in .env, skipping real login.")
        return True

    def get_checkout_details(self) -> dict[str, str]:
        logger.info(f"[{self.store_name} Adapter] Navigating to account settings to scrape details...")

        user = os.environ.get("LITTLEFARMS_EMAIL", "")
        if not user:
            return {
                "address": "Not logged in (Missing LITTLEFARMS_EMAIL in .env)",
                "payment_method": "Not logged in"
            }

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
                    text = payment_table.get_text(separator=" ", strip=True)
                    import re
                    match = re.search(r'(\d{4})', text)
                    if match:
                        payment_text = f"Card ending in {match.group(1)} (Saved)"
                    else:
                        payment_text = text[:30] + "..."

                browser.close()
                return {
                    "address": final_address,
                    "payment_method": payment_text
                }
        except Exception as e:
            logger.error(f"[{self.store_name} Adapter] Error scraping account details: {e}")
            return {
                "address": f"Error scraping address for {user}",
                "payment_method": "Error scraping payment method"
            }

    def checkout(self, items: list[dict[str, Any]]) -> bool:
        """Full Playwright checkout flow for Little Farms"""
        logger.info(f"[{self.store_name} Adapter] Proceeding to full autonomous checkout...")

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                page = context.new_page()
                Stealth().apply_stealth_sync(page)

                # 1. Login
                self._login(page)

                # 2. Add Items to Cart
                for item in items:
                    url = item.get("source_url") or item.get("url")
                    if url:
                        logger.info(f"[{self.store_name} Adapter] Adding {item.get('title', 'item')} to cart from {url}")
                        page.goto(url)
                        page.wait_for_timeout(3000)
                        # Execute JS to add to cart to avoid visibility issues
                        page.evaluate("if(document.querySelector('form[data-role=\"tocart-form\"]')) { document.querySelector('form[data-role=\"tocart-form\"]').submit(); }")
                        page.wait_for_timeout(4000)

                # 3. Navigate to Checkout
                logger.info(f"[{self.store_name} Adapter] Navigating to checkout...")
                page.goto(f"https://{self.domain}/checkout/")
                page.wait_for_timeout(8000) # Wait for checkout SPA to hydrate

                # 4. Shipping Step
                logger.info(f"[{self.store_name} Adapter] Processing shipping step...")
                # In Magento, the Next button usually has class .continue
                page.evaluate("if(document.querySelector('button.continue')) { document.querySelector('button.continue').click(); }")
                page.wait_for_timeout(6000)

                # 5. Payment & Comment Step
                logger.info(f"[{self.store_name} Adapter] Injecting order comments and selecting payment...")
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
                logger.info(f"[{self.store_name} Adapter] Finalizing order placement...")

                # DANGER: UNCOMMENT THE FOLLOWING LINES TO ENABLE REAL PURCHASES
                # page.evaluate("if(document.querySelector('button.action.primary.checkout')) { document.querySelector('button.action.primary.checkout').click(); }")
                # page.wait_for_timeout(10000)
                # print(f"[{self.store_name} Adapter] Order placed successfully! (url: {page.url})")
                logger.info(f"[{self.store_name} Adapter] [SAFETY STOP]: Order would have been placed here. Uncomment code to go live.")

                browser.close()
                return True
        except Exception as e:
            logger.error(f"[{self.store_name} Adapter] Checkout failed: {e}")
            return False
