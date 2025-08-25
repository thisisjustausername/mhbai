# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: find the urls to the mhbs for university of aachen

import time
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tempfile
import json
import requests
import sys
from bs4 import BeautifulSoup

options = Options()
"""options.add_argument("--headless=new")  # newer headless mode, works better
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--disable-extensions")
options.add_argument("--window-size=1920,1080")
# Create a temporary user data dir
user_data_dir = tempfile.mkdtemp()
options.add_argument(f"--user-data-dir={user_data_dir}")"""

driver = webdriver.Chrome(options=options)

def wait_for_page_load(driver, timeout=10):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )


"""# just for retrying error urls
with open("rwth_aachen_errors.json", "r") as file:
    errors = json.load(file)

with open("rwth_aachen.json", "r") as file:
    old_data = json.load(file)

urls = []
for i in errors:
    driver.get(i)
    wait = WebDriverWait(driver, 15)
    element = wait.until(EC.visibility_of_element_located((By.TAG_NAME, 'iframe')))
    iframe = driver.find_element(By.TAG_NAME, 'iframe')
    driver.switch_to.frame(iframe)
    elements = driver.find_elements(By.CSS_SELECTOR, '[class=" MaskRenderer"]')
    data = [i.find_element(By.TAG_NAME, "a") for i in elements if len(i.find_elements(By.TAG_NAME, 'a')) > 0]
    data = [{"name": i.get_attribute("text"), "url": i.get_attribute("href")} for i in data]
    urls += data
    print(driver.current_url)

old_data += urls

with open("rwth_aachen.json", "w") as file:
    json.dump(old_data, file)
sys.exit()"""

# between 1770 and 2074
number = 1770

urls = []
error_list = []
while number <= 2074:
    base_url = f"https://online.rwth-aachen.de/RWTHonline/ee/ui/ca2/app/desktop/#/pl/ui/$ctx/wbModhbReport.downloadPublicMHBVersion?$ctx=design=ca2;header=max;lang=de&pOrgNr=1&pStpStpNr={number}"
    try:
        driver.get(base_url)
        wait = WebDriverWait(driver, 15)
        element = wait.until(EC.visibility_of_element_located((By.TAG_NAME, 'iframe')))
        iframe = driver.find_element(By.TAG_NAME, 'iframe')
        driver.switch_to.frame(iframe)
        elements = driver.find_elements(By.CSS_SELECTOR, '[class=" MaskRenderer"]')
        data = [i.find_element(By.TAG_NAME, "a") for i in elements if len(i.find_elements(By.TAG_NAME, 'a')) > 0]
        data = [{"name": i.get_attribute("text"), "url": i.get_attribute("href")} for i in data]
        urls += data
        print(driver.current_url)
    except:
        error_list.append(base_url)
    number += 1


with open("rwth_aachen.json", "w") as file:
    json.dump(urls, file)

with open("rwth_aachen_errors.json", "w") as file:
    json.dump(error_list, file)