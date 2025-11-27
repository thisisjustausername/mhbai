import json
import math
import multiprocessing
import psycopg2
from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from abc import ABC, abstractmethod
from typeguard import typechecked

from database import database as db
from datatypes.result import Result
from datatypes.response import Response

class Scraper(ABC):
    """
    Universal scraper class

    Attributes:
        urls (list): List of URLs to scrape
    """

    def __init__(self, new_only: bool = False):
        """
        Initialize Scraper object.

        Parameters:
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


    @typechecked
    def process_urls(self, urls: list, offset: int = 0, printing: bool = True, raspi: bool = False) -> Response:
        """
        Process a list of URLs to scrape course information.
        Each url is a page of a website containing multiple courses of study.

        Parameters:
            urls (list): List of URLs to be processed.
            offset (int): Where to start counting in order to show a readable output to the user
            printing (bool): Whether to print progress information
            raspi (bool): Whether the program is running on a Raspberry Pi
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
        
        # connection to db
        cursor = db.connect()

        # process each url page
        for index, element in enumerate(urls):
            try:
                # scrape data for current url
                result = self.scrape_url(driver=driver, wait=wait, cursor=cursor, url=element)

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
        # close driver
        driver.quit()
        db.close(cursor)
        return Response(success_list=elements, error_list=error_list)
    

    @abstractmethod
    @typechecked
    def generate_urls(self, new_only: bool = False) -> list[str]:
        """
        Generate list of URLs to scrape

        Parameters:
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

        Parameters:
            driver (webdriver.Chrome): Selenium WebDriver instance.
            wait (WebDriverWait): Selenium WebDriverWait instance.
            cursor (psycopg2.extensions.cursor): Database cursor for storing data.
            url (str): URL of the list page to scrape.
        Returns:
            list[dict[str, Any]] | dict[str, Any]: list of course information found on the page or a single course information dictionary
        """
        pass

    @typechecked
    def fetch_async(self, urls_per_job: int = 30, printing: bool = True, raspi: bool = False) -> Response:
        """
        Fetch data from a list of URLs asynchronously.

        Parameters:
            urls (list): List of URLs to fetch data from.
            offset (int): Where to start counting in order to show a readable output to the user
            printing (bool): Whether to print progress information
            raspi (bool): Whether the program is running on a Raspberry Pi
        Returns:
            Response: Response object containing successful results and error lists
        """

        # initialize multiprocessing
        multiprocessing.set_start_method("spawn")

        # assign processes
        processes = math.ceil(len(self.urls) / urls_per_job)

        # start pool
        with multiprocessing.Pool(processes=processes) as pool:

            # initialize variables
            all_elements = []
            all_errors = []

            # distribute jobs and collect results
            results = [pool.apply_async(self.process_urls, args=(self.urls[i:i + urls_per_job], i, printing)) for i in range(0, len(self.urls), urls_per_job)]
            # gather results
            for result in results:
                response = result.get()
                elements = response.success_list
                error_list = response.error_list
                all_elements += elements
                all_errors += error_list
        
        with open(self.error_file, "w") as f:
                json.dump(all_errors, f, indent=4)
        
        return Response(success_list=all_elements, error_list=all_errors)