# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: get the base urls for all courses of study
# Status: VERSION 1.0
# FileID: Sc-ge-0001

import json
import math
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import multiprocessing

from database import database as db

def process_urls(urls: list, offset: int=0, raspi=False):
    """
    Process a list of URLs to scrape course information.
    Each url is a page of studieren.de containing multiple courses of study.

    Parameters:
        urls (list): List of URLs to be processed.
        offset (int): Where to start counting in order to show a readable output to the user
        raspi (bool): Whether the program is running on a Raspberry Pi
    """

    # try setting up webdriver
    try:
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        if raspi:
            service = Service("/usr/bin/chromedriver")
            driver = webdriver.Chrome(service=service, options=options)
        else:
            driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 1)
    except:
        print("Error occurred for whole url list")
        return [], urls
    
    # initialize variables
    elements = []
    error_list = []
    
    # connection to db
    cursor = db.connect()

    # process each url page
    for index, element in enumerate(urls):
        try:
            # call page
            driver.get(element)
            # wait for page to load
            while True:
                try:
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    wait.until(EC.visibility_of_element_located((By.ID, "search-results")))
                    wait.until(EC.visibility_of_element_located((By.XPATH, "/html/body/div[1]/div[1]/div[1]/a")))
                    break
                except:
                    pass
            
            # extra time to load
            time.sleep(0.2)

            # scrape data
            page = driver.find_element(By.ID, "search-results")
            child_elements = page.find_elements(By.CSS_SELECTOR, "*")

            # bare_elems = [i.find_element(By.CLASS_NAME, "item-main-link") for i in child_elements if i.get_attribute("class") in ["page-course-listing-entry search-result simple profile", "page-course-listing-entry search-result simple profile similar-courses"]]
            
            bare_elems = driver.find_elements(By.CSS_SELECTOR,
            ".page-course-listing-entry.search-result.simple.profile .item-main-link, "
            ".page-course-listing-entry.search-result.simple.profile.similar-courses .item-main-link")

            # each elem in elems is a course of study
            elems = [{"href": i.get_attribute("href"), "title": i.get_attribute("title")} for i in bare_elems]

            # clean elems
            for i in elems:
                information = i["title"].split("\n")
                i["name"] = information[0].strip()
                i["city"] = information[1].strip()
                i["university"] = information[2].strip()
                i["degree"] = information[3].strip()
                try:
                    db.insert(cursor=cursor, table="universal_mhbs", arguments={
                        "stud_title": i["title"], 
                        "name": i["name"],
                        "city": i["city"],
                        "university": i["university"],
                        "degree": i["degree"],
                        "stud_url": i["href"]
                    })
                except Exception as e:
                    db.insert(cursor=cursor, table="universal_mhbs", arguments={
                        "stud_title": i["title"],
                        "stud_url": i["href"]})
                    print(f"Error inserting into db: {e}")
            # elems = [i.find_element(By.CLASS_NAME, "item-main-link").get_attribute("href") for i in child_elements if i.get_attribute("class") in ["page-course-listing-entry search-result simple profile", "page-course-listing-entry search-result simple profile similar-courses"]]

            # add elems to list
            elements += elems
            print(index+offset)
        
        # catch errors
        except Exception as exception:
            print(f"Error occurred: {exception}")
            error_list.append(element)
    
    # close driver
    driver.quit()
    db.close(cursor)
    return elements, error_list


def get_base_links(urls_per_job: int = 30, raspi: bool=False):
    """
    Get the base links for all courses of study from studieren.de
    
    Parameters:
        urls_per_job (int): Number of URLs to be processed per job in the multiprocessing pool.
        raspi (bool): Whether the program is running on a Raspberry Pi
    """

    # initialize multiprocessing
    multiprocessing.set_start_method("spawn")

    # create base list of page urls to process
    list_urls = [f"https://studieren.de/suche.0.html?lt=course&rs=list&sort=alphabetical&start={i*23}" for i in range(410)]

    # assign processes
    processes = math.ceil(len(list_urls) / urls_per_job)

    # start pool
    with multiprocessing.Pool(processes=processes) as pool:

        # initialize variables
        all_elements = []
        all_errors = []

        # distribute jobs and collect results
        results = [pool.apply_async(process_urls, args=(list_urls[i:i + urls_per_job],i,raspi)) for i in range(0, len(list_urls), urls_per_job)]
        # gather results
        for result in results:
            elements, error_list = result.get()
            all_elements += elements
            all_errors += error_list
        sys.exit(0)

    # save results to files
    # TODO: remove files and result gathering since usage of db
    with open("web_scraping/universal/files/data.json", "w") as file:
        json.dump(all_elements, file, indent=4)
    with open("web_scraping/universal/files/error_list.json", "w") as file:
        json.dump(all_errors, file, indent=4)

def get_base_links_synchronous(raspi: bool=False):
    """
    Get the base links for all courses of study from studieren.de synchronously.
    
    Parameters:
        raspi (bool): Whether the program is running on a Raspberry Pi
    """
    # for debugging purposes
    list_urls = [f"https://studieren.de/suche.0.html?lt=course&rs=list&sort=alphabetical&start={i*23}" for i in range(410)]
    all_elements, all_errors = process_urls(list_urls, raspi=raspi)
    

def get_error_base_links(urls_per_job: int = 1):
    """
    Get the base links for all courses of study from studieren.de where errors occurred.
    
    Parameters:
        urls_per_job (int): Number of URLs to be processed per job in the multiprocessing pool.
    """
    multiprocessing.set_start_method("spawn")
    with open("web_scraping/universal/files/data.json", "r") as file:
        all_elements = json.load(file)
    with open("web_scraping/universal/files/error_list.json", "r") as file:
        list_urls = json.load(file)
    processes = math.ceil(len(list_urls) / urls_per_job)
    with multiprocessing.Pool(processes=processes) as pool:
        all_errors = [] # initializing all_errors new, but not all_elements
        results = [pool.apply_async(process_urls, args=(list_urls[i:i + urls_per_job],i,)) for i in range(0, len(list_urls), urls_per_job)]
        for result in results:
            elements, error_list = result.get()
            all_elements += elements
            all_errors += error_list
    """
    with open("web_scraping/universal/files/data.json", "w") as file:
        json.dump(all_elements, file, indent=4)
    with open("web_scraping/universal/files/error_list.json", "w") as file:
        json.dump(all_errors, file, indent=4)
    """

if __name__ == "__main__":
    raspi = True
    # get_base_links(urls_per_job=2, raspi=raspi)
    get_base_links_synchronous(raspi=False)
    """
    print("-----------------------------------------------\nstep 2\n-----------------------------------------------")
    with open("web_scraping/universal/files/data.json", "r") as file:
        data = json.load(file)
    print(len(data))
    """