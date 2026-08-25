import sys
import os
import urllib.parse
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup

def debug_scrape(store_name, domain, url):
    print(f"[{store_name}] Debugging {url}...")
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
        
        page.goto(f"https://{domain}", timeout=30000)
        page.wait_for_timeout(2000)
        
        page.goto(url, timeout=30000)
        page.wait_for_timeout(5000)
        
        content = page.content()
        with open(f"{store_name}_debug.html", "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"[{store_name}] Saved HTML to {store_name}_debug.html")
        browser.close()

if __name__ == "__main__":
    debug_scrape("FairPrice", "fairprice.com.sg", "https://www.fairprice.com.sg/search?query=eggs")
    debug_scrape("LittleFarms", "littlefarms.com", "https://littlefarms.com/search?q=eggs")
