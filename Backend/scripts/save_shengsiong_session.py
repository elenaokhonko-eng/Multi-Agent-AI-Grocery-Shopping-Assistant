import os
import time
from playwright.sync_api import sync_playwright

AUTH_DIR = os.path.join(os.path.dirname(__file__), "..", "auth_sessions")

def create_auth_dir():
    if not os.path.exists(AUTH_DIR):
        os.makedirs(AUTH_DIR)

def save_shengsiong_session():
    print("=" * 50)
    print("Sheng Siong Incapsula Clearance & Session Saver")
    print("=" * 50)
    print("A browser will now open to Sheng Siong.")
    print("If you see an Incapsula 'Pardon Our Interruption' or Captcha,")
    print("please clear it manually until you see the Sheng Siong homepage.")
    print("Once you are on the actual homepage, return to this terminal and press Enter.")
    print("=" * 50)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        page.goto("https://shengsiong.com.sg")
        
        input("\nPress Enter here AFTER you have successfully passed Incapsula... ")
        
        create_auth_dir()
        auth_file = os.path.join(AUTH_DIR, "shengsiong_auth.json")
        context.storage_state(path=auth_file)
        print(f"✅ Session saved successfully to {auth_file}!")
        browser.close()

if __name__ == "__main__":
    save_shengsiong_session()
