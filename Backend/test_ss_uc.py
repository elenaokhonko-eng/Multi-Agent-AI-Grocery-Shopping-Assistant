import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import time
import re
import urllib.parse

print("Starting UC...")
options = uc.ChromeOptions()
options.add_argument('--headless=new')
driver = uc.Chrome(options=options)

keyword = "eggs"
print(f"Searching {keyword} on Sheng Siong...")
search_url = f"https://shengsiong.com.sg/search/{urllib.parse.quote(keyword)}"
driver.get(search_url)

# Wait a bit longer for Meteor to hydrate
print("Waiting 10 seconds for hydration...")
time.sleep(10)

content = driver.page_source
with open("ss_test_page.html", "w", encoding="utf-8") as f:
    f.write(content)

soup = BeautifulSoup(content, 'html.parser')
price = 0.0
for span in soup.find_all(string=re.compile(r'\$\d+\.\d{2}')):
    print("Found potential price:", span)
    
driver.quit()
print("Done.")
