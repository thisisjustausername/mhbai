import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def get_base_links():
    options = Options()
    #options.add_argument("--headless=new")
    list_urls = [f"https://studieren.de/suche.0.html?lt=course&rs=list&sort=alphabetical&start={i*23}" for i in range(410)]
    driver = webdriver.Chrome(options=options)
    #list_urls = list_urls[:1]
    elements = []
    wait = WebDriverWait(driver, 1)
    for index, i in enumerate(list_urls):
        print(index)
    while True:
        try:
            driver.get(i)
            while True:
                try:
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    wait.until(EC.visibility_of_element_located((By.ID, "search-results")))
                    wait.until(EC.visibility_of_element_located((By.XPATH, "/html/body/div[1]/div[1]/div[1]/a")))
                    break
                except:
                    pass

            time.sleep(0.5)
            page = driver.find_element(By.ID, "search-results")
            child_elements = page.find_elements(By.CSS_SELECTOR, "*")
            elems = [i.find_element(By.CLASS_NAME, "item-main-link").get_attribute("href") for i in child_elements if i.get_attribute("class") in ["page-course-listing-entry search-result simple profile", "page-course-listing-entry search-result simple profile similar-courses"]]
            elements += elems
            for e in elems:
                print(e)
            break
        except:
            pass

    with open("data.json", "w") as file:
        json.dump(elements, file)

# get_base_links()
with open("data.json", "r") as file:
    data = json.load(file)
print(len(data))