from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import urllib.parse
import json

api_requests = []

def handle_request(request):
    if "api" in request.url or "graphql" in request.url or "search" in request.url:
        api_requests.append({
            "url": request.url,
            "method": request.method,
            "headers": request.headers
        })

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    Stealth().apply_stealth_sync(page)
    
    page.on("request", handle_request)
    
    keyword = "eggs"
    url = f"https://shengsiong.com.sg/search/{urllib.parse.quote(keyword)}"
    print(f"Navigating to {url}")
    try:
        page.goto(url, timeout=30000, wait_until="networkidle")
    except Exception as e:
        print("Timeout or error:", e)
    
    # Save the requests to a file so we can inspect them
    with open("ss_requests.json", "w") as f:
        json.dump(api_requests, f, indent=2)
        
    browser.close()
    
print(f"Captured {len(api_requests)} potential API requests.")
