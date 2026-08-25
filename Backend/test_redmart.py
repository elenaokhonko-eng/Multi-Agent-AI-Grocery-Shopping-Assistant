from playwright.sync_api import sync_playwright
import urllib.parse
from bs4 import BeautifulSoup
import re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    for keyword in ["CGPL South Africa Lemon", "Raspberries"]:
        print(f"\nTesting RedMart for: {keyword}")
        url = f"https://redmart.lazada.sg/catalog/?q={urllib.parse.quote(keyword)}"
        page.goto(url, timeout=30000)
        page.wait_for_timeout(3000)
        
        soup = BeautifulSoup(page.content(), 'html.parser')
        # Look for the first product card
        product_card = soup.find('div', attrs={'data-qa-locator': 'product-item'})
        if product_card:
            print("Product found:", product_card.get_text(separator=' | ', strip=True))
        else:
            print("No product card found.")
            
    browser.close()
