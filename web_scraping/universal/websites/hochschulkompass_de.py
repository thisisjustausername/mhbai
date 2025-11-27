# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: scrape courses from Hochschulkompass hochschulkompass.de
# Status: VERSION 1.0
# FileID: Un-sc-0002


import time
import psycopg2
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from database import database as db
from selenium.webdriver.common.by import By

from web_scraping.universal.scrape import Scraper

class HochschulkompassDetailed(Scraper):
    """
    Scrape detailed information from hochschulkompass.de
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_urls = [f"https://www.hochschulkompass.de/studium/studiengangsuche/erweiterte-studiengangsuche/detail/all/search/{i}/studtyp/3/view/wide.html?tx_szhrksearch_pi1%5Babschluss%5D%5B0%5D=24&tx_szhrksearch_pi1%5Babschluss%5D%5B1%5D=37&tx_szhrksearch_pi1%5Babschluss%5D%5B2%5D=5&tx_szhrksearch_pi1%5Bresults_at_a_time%5D=100" for i in range(21941)]
        self.elements = []

    def generate_urls(self) -> list[str]:
        """
        Generate list of URLs to scrape from studiengaenge.zeit.de

        Returns:
            list[str]: List of URLs to scrape
        """
        return [f"https://www.hochschulkompass.de/studium/studiengangsuche/erweiterte-studiengangsuche/detail/all/search/{i}/studtyp/3/view/wide.html?tx_szhrksearch_pi1%5Babschluss%5D%5B0%5D=24&tx_szhrksearch_pi1%5Babschluss%5D%5B1%5D=37&tx_szhrksearch_pi1%5Babschluss%5D%5B2%5D=5&tx_szhrksearch_pi1%5Bresults_at_a_time%5D=100" for i in range(21941)]
    

    def scrape_url(self, driver: webdriver.Chrome, wait: WebDriverWait, cursor: psycopg2.extensions.cursor, url: str):
        """
        extract information from detail-page

        Parameters:
            driver (webdriver.Chrome): Selenium WebDriver instance.
            wait (WebDriverWait): Selenium WebDriverWait instance.
            cursor (psycopg2.extensions.cursor): Database cursor for storing data.
            url (str): URL of the list page to scrape.
        Returns:
            dict: course information found on the page
        """

        driver.get(url)

        # wait for page to load
        while True:
            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                break
            except:
                pass
        
        # extra time to load
        time.sleep(0.2)
        with open("test_2.html", "w") as file:
            file.write(driver.page_source)

        # scrape data
        block = driver.find_element(By.CLASS_NAME, "course-block")
        title = block.find_element(By.XPATH, "/header/h1").text
        
        


class HochschulkompassUndetailed(Scraper):
    """
    Scrape undetailed information from hochschulkompass.de
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_urls = [f"https://www.hochschulkompass.de/studium/studiengangsuche/erweiterte-studiengangsuche/search/1/studtyp/3/pn/{i}/view/wide.html?tx_szhrksearch_pi1%5Babschluss%5D%5B0%5D=24&tx_szhrksearch_pi1%5Babschluss%5D%5B1%5D=37&tx_szhrksearch_pi1%5Babschluss%5D%5B2%5D=5&tx_szhrksearch_pi1%5Bresults_at_a_time%5D=100" for i in range(220)]
        self.elements = []


    def generate_urls(self) -> list[str]:
        """
        Generate list of URLs to scrape from studiengaenge.zeit.de

        Returns:
            list[str]: List of URLs to scrape
        """
        return [f"https://www.hochschulkompass.de/studium/studiengangsuche/erweiterte-studiengangsuche/search/1/studtyp/3/pn/{i}/view/wide.html?tx_szhrksearch_pi1%5Babschluss%5D%5B0%5D=24&tx_szhrksearch_pi1%5Babschluss%5D%5B1%5D=37&tx_szhrksearch_pi1%5Babschluss%5D%5B2%5D=5&tx_szhrksearch_pi1%5Bresults_at_a_time%5D=100" for i in range(220)]


    def scrape_url(self, driver: webdriver.Chrome, wait: WebDriverWait, cursor: psycopg2.extensions.cursor, url: str):
        """
        extract course link and information from list page

        Parameters:
            driver (webdriver.Chrome): Selenium WebDriver instance.
            wait (WebDriverWait): Selenium WebDriverWait instance.
            cursor (psycopg2.extensions.cursor): Database cursor for storing data.
            url (str): URL of the list page to scrape.
        Returns:
            list[dict[str, Any]]: list of course information found on the page
        """


if __name__ == "__main__":
    hk_detailed = HochschulkompassDetailed()
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 1)
    hk_detailed.scrape_url(cursor=db.connect(), wait=wait, driver=driver, url=hk_detailed.list_urls[0])