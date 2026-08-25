import requests
import re
import json
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
}

r = requests.get("https://shengsiong.com.sg/search/eggs", headers=headers)
html = r.text
soup = BeautifulSoup(html, 'html.parser')

scripts = soup.find_all('script')
print(f"Found {len(scripts)} script tags.")

for s in scripts:
    if s.string and ('__INITIAL_STATE__' in s.string or 'eggs' in s.string):
        print("Found interesting script!")
        print(s.string[:200])

if "api" in html or "graphql" in html:
    print("Found API reference in HTML")
