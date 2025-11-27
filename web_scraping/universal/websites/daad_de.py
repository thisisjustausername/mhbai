# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: scrape courses from Daad daad.de using their api (data from Hochschulkompass)
# Status: VERSION 1.0
# FileID: Un-sc-0003


from flask import json
import psycopg2
import requests

from typing_extensions import override
from typeguard import typechecked

from database import database as db
from web_scraping.universal.scrape import Scraper
from datatypes.result import Result
from datatypes.response import Response

class Daad(Scraper):
    """
    Scrape detailed information from hochschulkompass.de
    """
    def __init__(self, *args, **kwargs):
        # initialize parent class
        super().__init__(*args, **kwargs)

    def set_error_file(self) -> str:
        """
        Set the error file path for storing fetched URLs.

        Returns:
            str: Path to the error file
        """
        return "web_scraping/universal/websites/daad_de_fetched_urls.json"

    @typechecked
    def generate_urls(self, new_only: bool = False) -> list[str]:
        """
        Generate list of URLs to scrape from studiengaenge.zeit.de

        Parameters:
            new_only (bool): Whether to generate only unfetched URLs
        Returns:
            list[str]: List of URLs to scrape
        """

        urls = [f"https://api.daad.de/api/ajax/hsk/list/de?hec-degree-type=25,37,5&hec-p={i+1}" for i in range(1118)]

        if new_only:
            try:
                with open(self.error_file, "r") as f:
                    urls = json.load(f)
                return urls
            except FileNotFoundError:
                pass
        
        return urls
    
    
    @override
    @typechecked
    def process_urls(self, urls: list, offset: int = 0, printing: bool = True) -> Response:
        """
        Overrides method process_urls from parent class Scraper since this version doesn't use selenium but requests.

        Process a list of URLs to scrape course information.
        Each url is a page of daad.de containing multiple courses of study using the API.

        Parameters:
            urls (list): List of URLs to be processed.
            offset (int): Where to start counting in order to show a readable output to the user
            printing (bool): Whether to print progress information
        Returns:
            Response: Response object containing scraped data and list of error URLs
        """

        # initialize variables
        elements = []
        error_list = []
        
        # connection to db
        cursor = db.connect()

        # process each url page
        for index, element in enumerate(urls):
            try:
                # scrape data for current url
                result = self.scrape_url(cursor=cursor, url=element)
                
                # test result for error
                if result.is_error is True and printing is True:
                    print("Error occured: " + str(result.error))
                    continue

                # append data to result list
                elements.append(result.data)

                # print progress
                if printing:
                    print(index + offset)
            
            # catch errors
            except requests.ConnectionError as e:
                print("Connection error occurred: ", e)
                error_list += urls[index:]
                break
            except Exception as exception:
                # handle error for current url
                if printing:
                    print(f"Error occurred: {exception}")
                error_list.append(element)
        
        # close database connection
        db.close(cursor)

        # return result
        return Response(success_list=elements, error_list=error_list)

    @typechecked
    def scrape_url(self, cursor: psycopg2.extensions.cursor, url: str) -> Result:
        """
        Implements abstract method from parent class Scraper.

        extract information from api

        Parameters:
            cursor (psycopg2.extensions.cursor): Database cursor for storing data.
            url (str): URL of the list page to scrape.
        Returns:
            Result: course information found on the page
        """

        # result of the API request
        result = requests.get(url=url, timeout=5)

        # check result for errors
        if result.status_code != 200:
            raise Exception(f"Failed to fetch data from {url} with status code {result.status_code}")
        
        # parse JSON data from the response
        data = result.json()

        # extract course information from JSON data
        courses = [{
            "web_id": i["id"], 
            "type_of_institution": i["institutionTypeId"],
            "web_url": i["link"]["url"], 
            "logo_url": i["logo"]["src"]["large"],
            "degree": (sub := i["items"])[0]["text"], 
            "duration": duration.split(" Semester")[0] if "Semester" in (duration := sub[1]["text"]) else str(int(int(duration.split(" Monate")[0]) / 6)) if "Monate" in duration else None, 
            "city": sub[2]["text"], 
            "study_type": sub[3]["text"], 
            "title": i["headline"], 
            "university": i["subline"], 
            "source": "daad.de"
        } for i in data["results"]["items"]]

        # create query for inserting course information into database
        query = f"""
            INSERT INTO all_unis.mhbs_unis (
                university_name, 
                type_of_institution, 
                city, 
                web_id, 
                source_url, 
                source, 
                name, 
                degree, 
                duration, 
                study_type)
            VALUES {', '.join(['(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)' for _ in range(len(courses))])}"""

        # setting variables for sql-injection save insert
        variables = [
            [
                i["university"], 
                i["type_of_institution"], 
                i["city"], 
                i["web_id"], 
                i["source"] + i["web_url"], 
                i["source"], 
                i["title"], 
                i["degree"], 
                i["duration"], 
                i["study_type"].split(", ")
            ] for i in courses]
        variables = [e for i in variables for e in i]

        # execute database insertion
        response = db.custom_call(cursor=cursor, query=query, type_of_answer=db.ANSWER_TYPE.NO_ANSWER, variables=variables)
        
        # check if there was an error during database insertion
        if response.is_error is True:
            return response
        
        # return the result containing course information
        result = Result(data=courses)
        return result


if __name__ == "__main__":
    scraper = Daad(new_only=True)
    response = scraper.fetch_async()
    print(response)