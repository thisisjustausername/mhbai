# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: get the url to the mhb pdf for each course of study
# Status: IN DEVELOPMENT
# FileID: Sc-ge-0007

from datetime import datetime, timedelta
import math
import time
import selenium.webdriver as webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from multiprocessing import Pool

from web_scraping.universal.data import database as db

def wait_for_page_load(driver, timeout: int = 10) -> None:
    """
    Wait for the page to fully load.

    Parameters:
        driver (webdriver): The Selenium WebDriver instance.
        timeout (int): Maximum time to wait for the page to load.
    """
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )

def initialize_driver() -> webdriver.Chrome:
    """
    Initialize and return a Selenium WebDriver instance with specified options.

    Returns:
        webdriver.Chrome: Configured Selenium WebDriver instance.
    """
    options = Options()
    driver = webdriver.Chrome(options=options)
    return driver

def fetch_search_strings(search_strings: list[dict[str, str]]) -> None | Exception:


    # get cursor
    cursor = db.connect()

    driver = initialize_driver()
    
    # url for the duckduckgo instant answer api
    # base_url: str = "https://api.duckduckgo.com/"
    base_url = "https://www.google.com/search"
    for search_string in search_strings:
        try:
            response = driver.get(f"{base_url}?q={search_string.replace(" ", "+")}")
        except Exception as e:
            if response.status_code == 429:
                raise Exception("Rate limit exceeded. Stopping the scraper.")
            print(f"Error for query {search_string}: {response.status_code}")
            continue
        soup = BeautifulSoup(response.text, 'lxml')
        try:
            mhb_url = soup.find("div", {"id": "results"}).find("div").find("a").get("href")
        except Exception as e:
            print("Error for query: {search_string}: No url found")
            continue
        # mhb_url = response.json().get("OfficialDomain", None)
        if mhb_url is None:
            print(f"Error for query {search_string}: No OfficialDomain found")
            continue
        result = db.update(cursor=cursor, table="universal_mhbs", arguments={"mhb_url": mhb_url}, conditions={"search_string": search_string})
        if result.is_error:
            print(f"Error updating search_string {search_string}: {mhb_url}")
            continue
        print(f"Updated search_string {search_string}: {mhb_url}")
        time.sleep(5)
    db.close(cursor)
    return None


def main(multiprocessing: bool = True) -> None:

    # get cursor
    cursor = db.connect()

    # fetch all universities
    result = db.select(cursor=cursor, table="universal_mhbs", keywords=["search_string"], specific_where="mhb_url IS NULL")
    db.close(cursor)
    # handle possible error
    if result.is_error:
        raise result.error

    # get data
    search_strings = result.data
    search_strings = [i["search_string"] for i in search_strings if i["search_string"] is not None]
    
    # without multiprocessing
    if multiprocessing is False:
        fetch_search_strings(search_strings)    
        return
    
    # with multiprocessing
    cpu_count = multiprocessing.cpu_count()
    urls_per_job = math.ceil(len(search_strings) / cpu_count)
    
    with multiprocessing.Pool(processes=cpu_count) as pool:
        results = [pool.apply_async(fetch_search_strings, args=(search_strings[i:i + urls_per_job],)) for i in range(0, len(search_strings), urls_per_job)]
        for result in results:
            data = result.get()


if __name__ == "__main__":
    retry = True
    minutes = 10

    while retry:
        try:
            main()
            retry = False
        except Exception as e:
            if "Rate limit exceeded" in str(e):
                print(f"Rate limit exceeded. Retrying in {minutes} minutes at {(datetime.now() + timedelta(minutes=minutes)).strftime('%H:%M:%S')}")
                time.sleep(minutes * 60)
            else:
                print(f"An unexpected error occurred: {e}")
                retry = False
