import requests
import urllib.parse
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
}

r = requests.get("https://shengsiong.com.sg/search/eggs", headers=headers)
html = r.text

prices = re.findall(r'\$\d+\.\d{2}', html)
print(f"Found {len(prices)} prices in raw HTML.")
if prices:
    print(prices[:5])
