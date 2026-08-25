from playwright.sync_api import sync_playwright
import urllib.parse
from bs4 import BeautifulSoup

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    keyword = "eggs"
    
    print("Testing ShengSiong...")
    url = f"https://shengsiong.com.sg/search/{urllib.parse.quote(keyword)}"
    page.goto(url, timeout=30000)
    page.wait_for_timeout(3000)
    
    # print all divs with 'price' in their class
    soup = BeautifulSoup(page.content(), 'html.parser')
    for div in soup.find_all(class_=lambda x: x and 'price' in x.lower()):
        print(div.get_text(strip=True))
        
    print("\nTesting RedMart...")
    url = f"https://redmart.lazada.sg/catalog/?q={urllib.parse.quote(keyword)}"
    page.goto(url, timeout=30000)
    page.wait_for_timeout(3000)
    
    soup = BeautifulSoup(page.content(), 'html.parser')
    # For redmart, let's look at the first few product cards
    for idx, product in enumerate(soup.find_all('div', attrs={'data-qa-locator': 'product-item'})[:3]):
        print(f"Product {idx}:")
        print(product.get_text(separator=' | ', strip=True))
        
    browser.close()
