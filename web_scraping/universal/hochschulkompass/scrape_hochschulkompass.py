# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: scrape courses from Hochschulkompass hochschulkompass.de
# Status: PROTOTYPING
# FileID: Un-sc-0001

import json
import math
import multiprocessing
import sys
import time
import psycopg2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from typing import Any

from database import database as db

@db.cursor_handling(manually_supply_cursor=False)
def process_urls(urls: list, offset: int=0, raspi=False, cursor: psycopg2.extensions.cursor | None = None) -> tuple[list, list]:
    """
    Process a list of URLs to scrape course information.
    Each url is a page of studiengaenge.zeit.de containing multiple courses of study.

    Args:
        urls (list): List of URLs to be processed.
        offset (int): Where to start counting in order to show a readable output to the user
        raspi (bool): Whether the program is running on a Raspberry Pi
        cursor (psycopg2.extensions.cursor | None): SUPPLIED BY DECORATOR; Database cursor for storing data.
    Returns:
        tuple[list, list]: A tuple containing a list of scraped elements and a list of URLs that resulted in errors.
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
    
    # process each url page
    for index, element in enumerate(urls):
        try:
           
        elements += 
        # catch errors
        except Exception as exception:
            print(f"Error occurred: {exception}")
            error_list.append(element)
    
    # close driver
    driver.quit()
    return elements, error_list


def find_courses_off_list_page(driver: webdriver.Chrome, wait: WebDriverWait, cursor: psycopg2.extensions.cursor, url: str) -> list[dict[str, Any]]:
    """
    extract course link and information from list page

    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance.
        wait (WebDriverWait): Selenium WebDriverWait instance.
        cursor (psycopg2.extensions.cursor): Database cursor for storing data.
        url (str): URL of the list page to scrape.
    Returns:
        list[dict[str, Any]]: list of course information found on the page
    """
    pass


def find_courses_on_detail_page(driver: webdriver.Chrome, wait: WebDriverWait, cursor: psycopg2.extensions.cursor, url: str) -> dict[str, Any]:
    """
    extract information from detail-page

    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance.
        wait (WebDriverWait): Selenium WebDriverWait instance.
        cursor (psycopg2.extensions.cursor): Database cursor for storing data.
        url (str): URL of the list page to scrape.
    Returns:
        dict: course information found on the page
    """
    pass


def get_base_links(urls_per_job: int = 30, raspi: bool=False):
    """
    Get the base links for all courses of study from studiengaenge.zeit.de
    
    Args:
        urls_per_job (int): Number of URLs to be processed per job in the multiprocessing pool.
        raspi (bool): Whether the program is running on a Raspberry Pi
    """

    # initialize multiprocessing
    multiprocessing.set_start_method("spawn")

    # create base list of page urls to process
    
    # list for blocks of courses
    # list_urls = [f"https://www.hochschulkompass.de/studium/studiengangsuche/erweiterte-studiengangsuche/search/1/studtyp/3/pn/{i}/view/wide.html?tx_szhrksearch_pi1%5Babschluss%5D%5B0%5D=24&tx_szhrksearch_pi1%5Babschluss%5D%5B1%5D=37&tx_szhrksearch_pi1%5Babschluss%5D%5B2%5D=5&tx_szhrksearch_pi1%5Bresults_at_a_time%5D=100" for i in range(220)]
    list_urls = [f"https://www.hochschulkompass.de/studium/studiengangsuche/erweiterte-studiengangsuche/detail/all/search/{i}/studtyp/3/view/wide.html?tx_szhrksearch_pi1%5Babschluss%5D%5B0%5D=24&tx_szhrksearch_pi1%5Babschluss%5D%5B1%5D=37&tx_szhrksearch_pi1%5Babschluss%5D%5B2%5D=5&tx_szhrksearch_pi1%5Bresults_at_a_time%5D=100" for i in range(21941)]

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


@NotImplementedError
def get_base_links_synchronous(raspi: bool=False):
    """
    Get the base links for all courses of study from studiengaenge.zeit.de synchronously.
    
    Args:
        raspi (bool): Whether the program is running on a Raspberry Pi
    """
    # for debugging purposes
    list_urls = [f"https://www.hochschulkompass.de/studium/studiengangsuche/erweiterte-studiengangsuche/detail/all/search/1/studtyp/3/pn/{i}/view/wide.html?tx_szhrksearch_pi1%5Babschluss%5D%5B0%5D=24&tx_szhrksearch_pi1%5Babschluss%5D%5B1%5D=37&tx_szhrksearch_pi1%5Babschluss%5D%5B2%5D=5&tx_szhrksearch_pi1%5Bresults_at_a_time%5D=100" for i in range(21941)]
    all_elements, all_errors = process_urls(list_urls, raspi=raspi)
    

@NotImplementedError
def get_error_base_links(urls_per_job: int = 1):
    """
    Get the base links for all courses of study from studiengaenge.zeit.de where errors occurred.
    
    Args:
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
    get_base_links()