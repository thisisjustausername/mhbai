# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: scrape courses from Daad daad.de using their api (data from Hochschulkompass)
# Status: VERSION 1.0
# FileID: Un-sc-0001

from datetime import datetime, timedelta
import json
import math
import multiprocessing
from typing import Annotated, Literal, overload
import psycopg2
import time

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from abc import ABC, abstractmethod
from typeguard import typechecked

from database import database as db
from datatypes.result import Result
from datatypes.response import Response, Message

class Scraper(ABC):
    """
    Universal scraper class

    Attributes:
        urls (list): List of URLs to scrape
    """

    def __init__(self, new_only: bool = False):
        """
        Initialize Scraper object.

        Args:
            new_only (bool): Whether to scrape only new URLs
        Returns:
            None
        """
        self.error_file = self.set_error_file()
        self.urls = self.generate_urls(new_only=new_only)


    @abstractmethod
    def set_error_file(self) -> str:
        """
        Set the error file path for storing fetched URLs.

        Returns:
            str: Path to the error file
        """
        pass


    @db.cursor_handling(manually_supply_cursor=False)
    def process_urls(self, urls: list, offset: int = 0, delay: float = 0, printing: bool = True, raspi: bool = False, cursor: psycopg2.extensions.cursor | None = None) -> Response:
        """
        Process a list of URLs to scrape course information.
        Each url is a page of a website containing multiple courses of study.

        Args:
            urls (list): List of URLs to be processed.
            offset (int): Where to start counting in order to show a readable output to the user
            delay (float): Delay in seconds between fetching URLs in order to avoid rate limits
            printing (bool): Whether to print progress information
            raspi (bool): Whether the program is running on a Raspberry Pi
            cursor (psycopg2.extensions.cursor | None): SUPPLIED BY DECORATOR; Database cursor for storing data.
        Returns:
            Response: Response object containing scraped data and list of error URLs
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
            if printing:
                print("Error occurred for whole url list")
            return Response(success_list=[], error_list=urls)
        
        # initialize variables
        elements = []
        error_list = []
    
        # process each url page
        for index, element in enumerate(urls):
            try:
                # scrape data for current url
                result = self.scrape_url(driver=driver, wait=wait, cursor=cursor, url=element) # type: ignore

                # if result data contains data from multiple courses, add list, if data only contains data of a single course, append data
                if result.is_error is True:
                    print("Error occured: " + str(result.error))
                    continue
                if isinstance(result.data, list):
                    elements += result.data
                else:
                    elements.append(result.data)
            
            # catch errors
            except Exception as exception:
                # handle error for current url
                if printing:
                    print(f"Error occurred: {exception}")
                error_list.append(element)
            
            # sleep for the given delay
            time.sleep(delay)
        # close driver
        driver.quit()
        return Response(success_list=elements, error_list=error_list)
    

    @abstractmethod
    @typechecked
    def generate_urls(self, new_only: bool = False) -> list[str]:
        """
        Generate list of URLs to scrape

        Args:
            new_only (bool): Whether to generate only unfetched URLs
        Returns:
            list[str]: List of URLs to scrape
        """
        pass
    

    @abstractmethod
    @typechecked
    def scrape_url(self, driver: webdriver.Chrome, wait: WebDriverWait, cursor: psycopg2.extensions.cursor, url: str) -> Result:
        """
        extract course link and information from list page

        Args:
            driver (webdriver.Chrome): Selenium WebDriver instance.
            wait (WebDriverWait): Selenium WebDriverWait instance.
            cursor (psycopg2.extensions.cursor): Database cursor for storing data.
            url (str): URL of the list page to scrape.
        Returns:
            list[dict[str, Any]] | dict[str, Any]: list of course information found on the page or a single course information dictionary
        """
        pass

    
    @abstractmethod
    @typechecked
    def add_data_universities(self) -> Response:
        """
        Scrape information of universities and store them in the database.
        
        Returns:
            Result: Result object indicating success or failure of the operation.
        """
        pass


    @typechecked
    def fetch_async(self, urls_per_job: int = 30, printing: bool = True, raspi: bool = False) -> Response:
        """
        This method is deprecated since the synchronous fetching method is faster due to avoiding rate limits.
        Fetch data from a list of URLs asynchronously.

        Args:
            urls_per_job (int): Number of URLs per job for asynchronous fetching.
            printing (bool): Whether to print progress information
            raspi (bool): Whether the program is running on a Raspberry Pi
        Returns:
            Response: Response object containing successful results and error lists
        """

        # initialize multiprocessing
        # multiprocessing.set_start_method("spawn")
        ctx = multiprocessing.get_context("spawn")

        # assign processes
        processes = math.ceil(len(self.urls) / urls_per_job)

        # start pool
        # with multiprocessing.Pool(processes=processes) as pool:
        with ctx.Pool(processes=processes) as pool:

            # initialize variables
            all_elements = []
            all_errors = []
            messages = []
            message = None

            # distribute jobs and collect results
            results = [pool.apply_async(self.process_urls, args=(self.urls[i:i + urls_per_job], i, printing)) for i in range(0, len(self.urls), urls_per_job)]
            # gather results
            for result in results:
                response = result.get()
                elements = response.success_list
                error_list = response.error_list
                all_elements += elements
                all_errors += error_list
                messages.append(response.message)
        
        # save errors
        with open(self.error_file, "w") as f:
                json.dump(all_errors, f, indent=4)
        
        # check for rate limit messages
        if any(msg is not None and msg.category == "rate limit" for msg in messages):
            message = Message(
                name="RateLimitHit",
                type="Error",
                category="rate limit",
                info="One or more processes hit a rate limit during fetching.",
                details=None,
                code=None
            )
        
        return Response(success_list=all_elements, error_list=all_errors, message=message)

    @typechecked
    def fetch_sync(self, delay: float = 0, printing: bool = True) -> Response:
        """
        Fetch data from a list of URLs synchronously.

        Args:
            delay (float): Delay in seconds between fetching URLs in order to avoid rate limits
            printing (bool): Whether to print progress information
        Returns:
            Response: Response object containing scraped data and list of error URLs
        """

        # process all urls
        response = self.process_urls(urls=self.urls, offset=0, delay=delay, printing=printing)

        # save errors
        with open(self.error_file, "w") as f:
                json.dump(response.error_list, f, indent=4)
        
        # return data
        return response


    @typechecked

    @overload
    def main(self, async_fetch: Literal[True], rate_limit_delay: int = 3, printing: bool = True, raspi: bool = False) -> Response: ...

    @overload
    def main(self, async_fetch: Literal[False], rate_limit_delay: int = 3, printing: bool = True, raspi: bool = False, delay: float = 0) -> Response: ...

    def main(self, async_fetch: bool = True, rate_limit_delay: int = 3, printing: bool = True, raspi: bool = False, delay: Annotated[float, "Explicit with async_fetch = True"] = 0) -> Response:
        """
        Main method to start the scraping process.

        Args:
            async_fetch (bool): Whether to fetch data asynchronously
            rate_limit_delay (int): Delay in minutes to wait after hitting a rate limit
            printing (bool): Whether to print progress information
            raspi (bool): Whether the program is running on a Raspberry Pi
            delay (float): Delay in seconds between fetching URLs in order to avoid rate limits; will be ignored if async_fetch is True
        Returns:
            Response: Response object containing scraped data and list of error URLs
        """

        # set fetch method
        if async_fetch:
            fetch = lambda: self.fetch_async(printing=printing, raspi=raspi)
        else:
            fetch = lambda: self.fetch_sync(delay=delay, printing=printing)
        
        # fetch data
        while True:
            # fetch data
            response = fetch()
            self.urls = self.generate_urls(new_only=True)

            # check for rate limit errors
            if len(response.error_list) > 0 and (msg := response.message) is not None and msg.category == "rate limit":
                if printing:
                    print(f"Rate limit hit, waiting for {rate_limit_delay} minute{'s' if rate_limit_delay != 1 else ''} at {(datetime.now() + timedelta(minutes=rate_limit_delay)).strftime('%H:%M:%S')}...")
                time.sleep(rate_limit_delay * 60)
                continue
            else:
                break
        return response