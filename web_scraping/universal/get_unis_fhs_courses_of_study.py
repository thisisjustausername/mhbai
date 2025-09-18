# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: get the base urls for all courses of study

import json
import math
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import multiprocessing

def process_urls(urls: list, offset: int=0):
    """
    Process a list of URLs to scrape course information.

    Parameters:
        urls (list): List of URLs to be processed.
        offset (int): Where to start counting in order to show a readable output to the user
    """
    options = Options()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    elements = []
    wait = WebDriverWait(driver, 1)
    error_list = []
    for index, i in enumerate(urls):
        print(index+offset)
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

            time.sleep(0.2)
            page = driver.find_element(By.ID, "search-results")
            child_elements = page.find_elements(By.CSS_SELECTOR, "*")
            bare_elems = [i.find_element(By.CLASS_NAME, "item-main-link") for i in child_elements if i.get_attribute("class") in ["page-course-listing-entry search-result simple profile", "page-course-listing-entry search-result simple profile similar-courses"]]
            elems = [{"href": i.get_attribute("href"), "title": i.get_attribute("title")} for i in bare_elems]
            for i in elems:
                information = i["title"].split("\n")
                i["name"] = information[0].strip()
                i["city"] = information[1].strip()
                i["university"] = information[2].strip()
                i["degree"] = information[3].strip()

            # elems = [i.find_element(By.CLASS_NAME, "item-main-link").get_attribute("href") for i in child_elements if i.get_attribute("class") in ["page-course-listing-entry search-result simple profile", "page-course-listing-entry search-result simple profile similar-courses"]]

            elements += elems
        except:
            print(f"Error occurred: {i}")
            error_list.append(i)
    driver.quit()
    return elements, error_list


def get_base_links(urls_per_job: int = 5):
    """
    Get the base links for all courses of study from studieren.de
    
    Parameters:
        urls_per_job (int): Number of URLs to be processed per job in the multiprocessing pool.
    """
    multiprocessing.set_start_method("spawn")
    list_urls = [f"https://studieren.de/suche.0.html?lt=course&rs=list&sort=alphabetical&start={i*23}" for i in range(410)]
    processes = math.ceil(len(list_urls) / urls_per_job)
    with multiprocessing.Pool(processes=processes) as pool:
        all_elements = []
        all_errors = []
        results = [pool.apply_async(process_urls, args=(list_urls[i:i + urls_per_job],i,)) for i in range(0, len(list_urls), urls_per_job)]
        for result in results:
            elements, error_list = result.get()
            all_elements += elements
            all_errors += error_list

    with open("web_scraping/universal/files/data.json", "w") as file:
        json.dump(all_elements, file, indent=4)
    with open("web_scraping/universal/files/error_list.json", "w") as file:
        json.dump(all_errors, file, indent=4)

if __name__ == "__main__":
    get_base_links()
    with open("web_scraping/universal/files/data.json", "r") as file:
        data = json.load(file)
    print(len(data))