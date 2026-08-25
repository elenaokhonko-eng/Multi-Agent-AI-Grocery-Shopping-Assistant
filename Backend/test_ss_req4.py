import requests
from bs4 import BeautifulSoup
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
}

r = requests.get("https://shengsiong.com.sg/", headers=headers)
soup = BeautifulSoup(r.text, 'html.parser')

scripts = soup.find_all('script')
for s in scripts:
    src = s.get('src')
    if src and 'meteor' not in src.lower():
        print("External JS:", src)
    elif src:
        js_url = src if src.startswith('http') else 'https://shengsiong.com.sg' + src
        print("Fetching JS:", js_url)
        js_r = requests.get(js_url, headers=headers)
        js_text = js_r.text
        
        # Look for API endpoints
        endpoints = re.findall(r'https?://[a-zA-Z0-9.\-]+/api/[a-zA-Z0-9./\-]*', js_text)
        if endpoints:
            print("Found endpoints:", set(endpoints))
            
        if "algolia" in js_text.lower():
            print("Algolia found in", js_url)
