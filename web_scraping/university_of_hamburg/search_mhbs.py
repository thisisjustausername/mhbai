# IMPORTANT note: this code isn't made for vm, since it can't run on headless computer (due to google's bot blocking), there are ways to avoid this, but since this is just simple experimental code, it'd be overkill
# since i can use a vpn from the university i use it do avoid duckduckgo's bot tracker
# if being bot blocked, add 5 seconds delay after loading page, reconnect to vpn, solve captcha and restart program

import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import json
import time

options = Options()
options.add_argument("--window-size=1920,1080")
# Create a temporary user data dir

driver = webdriver.Chrome(options=options)

with open("courses_of_study.json", "r") as file:
    data = json.load(file)

with open("university_of_hamburg.json", "r") as file:
    url_list = json.load(file)

with open("university_of_hamburg_errors.json", "r") as file:
    data = json.load(file)


def wait_for_page_load(driver, timeout=10):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )

error_list = []
for i in data:
    try:
        search_string = f"Universität Hamburg {i['name']} Modulhandbuch filetype:pdf"
        url = f"https://www.duckduckgo.com/html?q={urllib.parse.quote(search_string)}"
        driver.get(url)
        time.sleep(10)
        wait_for_page_load(driver)
        element = driver.find_element(By.CSS_SELECTOR, '[class="result results_links results_links_deep web-result "]') # this way ads are filtered out
        result = element.find_element(By.CLASS_NAME, "result__title").find_element(By.TAG_NAME, "a")
        mhb_url = result.get_attribute("href")
        print(mhb_url)
        url_list.append((i, mhb_url.split("https://duckduckgo.com/l/?uddg=", 1)[1]))
    except:
        error_list.append(i)

# unnecessary since already ignoring ads
new_data = [i for i in url_list if "ad_domain" not in i[1]]
error_data = [i[0] for i in url_list if "ad_domain" in i[1]]
error_list += error_data

with open("university_of_hamburg.json", "w") as file:
    json.dump(url_list, file)

with open("university_of_hamburg_errors.json", "w") as file:
    json.dump(error_list, file)