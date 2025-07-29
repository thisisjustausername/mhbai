import time
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

def wait_for_page_load(driver, timeout=10):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )

# between 1770 and 2074
number = 1770
base_url = f"https://online.rwth-aachen.de/RWTHonline/ee/ui/ca2/app/desktop/#/pl/ui/$ctx/wbModhbReport.downloadPublicMHBVersion?$ctx=design=ca2;header=max;lang=de&pOrgNr=1&pStpStpNr={number}"

while number <= 2074:
    driver.get(base_url)
    time.sleep(1)
    print(driver.page_source)
    """data = requests.get(base_url).text
    soup = BeautifulSoup(data, "lxml")
    results = soup.find_all("td", class_=" MaskRenderer")
    print(data)
    clean_results = []
    for i in results:
        clean = i.find("a")
        if clean is not None:
            clean_results.append(i)
    print(clean_results)"""
    number += 1
    sys.exit()