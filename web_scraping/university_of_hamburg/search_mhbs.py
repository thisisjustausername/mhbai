import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
import tempfile
import json
import requests
import sys
from bs4 import BeautifulSoup

options = Options()
options.add_argument("--headless=new")  # newer headless mode, works better
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--disable-extensions")
options.add_argument("--window-size=1920,1080")
# Create a temporary user data dir
user_data_dir = tempfile.mkdtemp()
options.add_argument(f"--user-data-dir={user_data_dir}")

driver = webdriver.Chrome(options=options)

with open("web_scraping/university_of_hamburg/courses_of_study.json", "r") as file:
    data  =json.load(file)

def wait_for_page_load(driver, timeout=10):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://duckduckgo.com",
    "Connection": "keep-alive"
}

for i in data:
    
    search_string = f"Universität Hamburg {i['name']} Modulhandbuch filetype:pdf"
    url = f"https://www.duckduckgo.com/html?q={urllib.parse.quote(search_string)}"
    # === OPEN FIRST URL ===
    #driver.get(url)
    #wait_for_page_load(driver)
    #print(driver.page_source)
    data = requests.get(url, headers=headers).text
    soup = BeautifulSoup(data, "lxml")
    result = soup.find("div", class_="links_main links_deep result__body")
    print(soup)
    sys.exit()
    breakpoint()