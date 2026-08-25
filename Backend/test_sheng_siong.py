from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import urllib.parse
from bs4 import BeautifulSoup
import re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    stealth_sync(page)
    
    keyword = "eggs"
    print("Testing ShengSiong with stealth...")
    url = f"https://shengsiong.com.sg/search/{urllib.parse.quote(keyword)}"
    page.goto(url, timeout=30000)
    page.wait_for_timeout(5000)
    
    soup = BeautifulSoup(page.content(), 'html.parser')
    text = soup.get_text(separator=' | ', strip=True)
    print("ShengSiong Text Snippet:", text[:1000].encode('utf-8', 'ignore').decode('utf-8'))
    browser.close()
