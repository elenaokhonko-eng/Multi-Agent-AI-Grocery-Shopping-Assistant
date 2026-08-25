import os
import time
from playwright.sync_api import sync_playwright

AUTH_DIR = os.path.join(os.path.dirname(__file__), "..", "auth_sessions")

def create_auth_dir():
    if not os.path.exists(AUTH_DIR):
        os.makedirs(AUTH_DIR)

def save_fairprice_session():
    print("=" * 50)
    print("FairPrice Google SSO Session Saver")
    print("=" * 50)
    print("A browser will now open to the FairPrice login page.")
    print("Please manually log in using your Google account.")
    print("Once you are fully logged in and see the FairPrice homepage,")
    print("return to this terminal and press Enter.")
    print("=" * 50)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        page.goto("https://fairprice.com.sg/login")
        
        input("\nPress Enter here AFTER you have successfully logged in... ")
        
        create_auth_dir()
        auth_file = os.path.join(AUTH_DIR, "fairprice_auth.json")
        context.storage_state(path=auth_file)
        print(f"✅ Session saved successfully to {auth_file}!")
        browser.close()

if __name__ == "__main__":
    save_fairprice_session()
