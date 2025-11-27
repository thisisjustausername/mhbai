# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: scrape courses from Zeit studiengaenge.zeit.de
# Status: VERSION 1.0
# FileID: Un-sc-0003

from psycopg2.extensions import cursor
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

from web_scraping.universal.scrape import Scraper

class Zeit(Scraper):
    """
    Scrape information from studiengaenge.zeit.de
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_urls = self.generate_urls()

    def generate_urls(self) -> list[str]:
        """
        Generate list of URLs to scrape from studiengaenge.zeit.de

        Returns:
            list[str]: List of URLs to scrape
        """
        return [f"https://studiengaenge.zeit.de/studienangebote?abschluss%5B%5D=bachelor&abschluss%5B%5D=master&abschluss%5B%5D=staatsexamen&filterOrder=abschluss%5B%5D&page={i+1}" for i in range(100)]


    def scrape_url(self, driver: webdriver.Chrome, wait: WebDriverWait, cursor: cursor, url: str):
     # call page
        driver.get(element)
        # wait for page to load
        time.sleep(5)
        
        while True:
            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                wait.until(EC.visibility_of_element_located((By.XPATH, "/html/body/div[2]/div[1]/main/div/suma-course-search/div[3]/std-course-list")))
                break
            except:
                pass
        
        # extra time to load
        time.sleep(0.2)

        # scrape data
        courses = driver.find_elements(By.CSS_SELECTOR, "a[_ngcontent-ng-c2093291323]")
        # courses = driver.find_elements(By.CLASS_NAME, "std-profileListItem__content")
        
        # each elem in elems is a course of study
        elems = [{"href": i.get_attribute("href"), 
                    "title": i.get_attribute("data-course-name"), 
                    "university": i.get_attribute("data-college-name"), 
                    "city": (sub := i.find_element(By.CLASS_NAME, "std-profileListItem__content")).find_element(By.XPATH, "div[1]/div[1]/div[3]"), 
                    "degree": (sub_sub := sub.find_element(By.XPATH, "div[2]")).find_element(By.XPATH, "div[1]/div[1]").text, 
                    "semesters": sub_sub.find_element(By.XPATH, "div[2]/div[1]").text} for i in courses]
        # elems = [{"href": i.get_attribute("href"), "title": i.get_attribute("title")} for i in courses]

        # clean elems
        for i in elems:
            information = i["title"].split("\n")
            i["name"] = information[0].strip()
            i["city"] = information[1].strip()
            i["university"] = information[2].strip()
            i["degree"] = information[3].strip()
            try:
                db.insert(cursor=cursor, table="all_unis.prototyping_mhbs", arguments={
                    "source_title": i["title"], 
                    "name": i["name"],
                    "city": i["city"],
                    "university": i["university"],
                    "degree": i["degree"],
                    "source_url": i["href"], 
                    "source": "studiengaenge.zeit.de"
                })
            except Exception as e:
                db.insert(cursor=cursor, table="all_unis.prototyping_mhbs", arguments={
                    "source_title": i["title"],
                    "source_url": i["href"], 
                    "source": "studiengaenge.zeit.de"})
                print(f"Error inserting into db: {e}")
        # elems = [i.find_element(By.CLASS_NAME, "item-main-link").get_attribute("href") for i in child_elements if i.get_attribute("class") in ["page-course-listing-entry search-result simple profile", "page-course-listing-entry search-result simple profile similar-courses"]]

        return elems