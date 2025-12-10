# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: scrape courses from Daad daad.de using their api (data from Hochschulkompass)
# Status: VERSION 1.0
# FileID: Un-ws-0001


from flask import json
import psycopg2
import requests
import time

from typing_extensions import override
from typeguard import typechecked

from database import database as db
from web_scraping.universal.scrape import Scraper
from datatypes.result import Result
from datatypes.response import Response, Message

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
                    self.urls = json.load(f)
                return self.urls
            except FileNotFoundError:
                pass
        
        self.urls = urls
        return self.urls
    
    
    @override
    @db.cursor_handling(manually_supply_cursor=False)
    @typechecked
    def process_urls(self, urls: list, offset: int = 0, delay: float = 0, printing: bool = True, cursor: psycopg2.extensions.cursor | None = None) -> Response:
        """
        Overrides method process_urls from parent class Scraper since this version doesn't use selenium but requests.

        Process a list of URLs to scrape course information.
        Each url is a page of daad.de containing multiple courses of study using the API.

        Parameters:
            urls (list): List of URLs to be processed.
            offset (int): Where to start counting in order to show a readable output to the user
            delay (float): Delay in seconds between fetching URLs in order to avoid rate limits
            printing (bool): Whether to print progress information
            cursor (psycopg2.extensions.cursor | None): SUPPLIED BY DECORATOR; Database cursor for storing data.
        Returns:
            Response: Response object containing scraped data and list of error URLs
        """

        # initialize variables
        elements = []
        error_list = []
        message = None
    
        # process each url page
        for index, element in enumerate(urls):
            try:
                # scrape data for current url
                result = self.scrape_url(cursor=cursor, url=element) # type: ignore
                
                # test result for error
                if result.is_error:
                    # for debugging purposes
                    if "duplicate key" in str(result.error):
                        if printing is True:
                            print("Duplicate entry found, skipping")
                        continue

                    error_list.append(element)
                    if printing is True:
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
                message = Message(
                    name="ConnectionError",
                    type="Error",
                    category="rate limit",
                    info="A connection error occurred while fetching data.",
                    details={"exception": str(e)},
                    code=None
                )
                break
            except Exception as exception:
                # handle error for current url
                if printing:
                    print(f"Error occurred: {exception}")
                error_list.append(element)
            
            # sleep for the given delay
            time.sleep(delay)
        
        # TODO: save data in database
        raise NotImplementedError("Saving data to database not implemented yet.")

        # return result
        return Response(success_list=elements, error_list=error_list, message=message)

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
        result = requests.get(url=url, timeout=10)

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
            "logo_url": i["logo"]["src"]["large"] if i["logo"] is not None else None,
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
                logo_url, 
                web_id, 
                source_url, 
                source, 
                name, 
                degree, 
                duration, 
                study_type)
            VALUES {', '.join(['(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)' for _ in range(len(courses))])}"""
            # ON CONFLICT (source_url) DO NOTHING"""

        # setting variables for sql-injection save insert
        variables = [
            [
                i["university"], 
                i["type_of_institution"], 
                i["city"], 
                i["logo_url"], 
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
    
    
    def _fetch_universities(self) -> list[dict[str, str]]:
        """
        Private method
        Fetches the list of universities from the Hochschulkompass TXT download endpoint.

        Returns:
            list[dict[str, str]]: A list of dictionaries containing data for each university in Germany.
        """

        # initialize URL for the Hochschulkompass TXT download
        url = "https://hs-kompass.de/kompass/xml/download/hs_liste.txt"

        # make the GET request to fetch the data
        response = requests.get(url)
        response.raise_for_status()

        # extract the data
        data = response.text
        
        # clean the data
        data = data.split("\n")
        header = data[0].split("\t")
        universities = [line.split("\t") for line in data[1:] if line]

        rename_dict = {"Hs-Nr.": "hs_nr",                                # used
                    "Hochschulkurzname": "short_name",                   # unused
                    "Hochschulname": "name",                             # used
                    "Adressname der Hochschule": "address_name",         # unused
                    "Hochschultyp": "type",                              # unknown
                    "Trägerschaft": "holder_type",                       # unknown
                    "Bundesland": "state",                               # unused
                    "Anzahl Studierende": "students",                    # unused
                    "Gründungsjahr": "founded",                          # unused
                    "Promotionsrecht": "doctoral_rights",                # unused
                    "Habilationsrecht": "habilitation_rights",           # unused
                    "Straße": "street",                                  # unused
                    "Postleitzahl (Hausanschrift)": "postal_code",       # unused
                    "Ort (Hausanschrift)": "city",                       # used
                    "Telefonvorwahl": "phone_area_code",                 # unused
                    "Telefon": "phone_number",                           # unused
                    "Fax": "fax_number",                                 # unused
                    "Home Page": "website",                              # used
                    "Mitglied HRK": "hrk_member"                         # unused
                    }

        clean_data = [{rename_dict.get(h, h): u for h, u in zip(header, uni)} for uni in universities]

        return clean_data
    

    @typechecked
    def _compare_university_names(self, fetched_name: str, db_name: str) -> bool:
        """
        Compares two university names for similarity.

        Parameters:
            name1 (str): First university name.
            name2 (str): Second university name.
        Returns:
            bool: True if names are similar, False otherwise.
        """
        # ignore upper and lowercase writing
        fetched_name = fetched_name.lower()
        db_name = db_name.lower()

        # check for exact match or substring match
        if fetched_name == db_name or fetched_name in db_name or db_name in fetched_name:
            return True
        
        # turn en-dashes and em-dashes into hyphens
        fetched_name = fetched_name.replace("—", "-").replace("–", "-")
        db_name = db_name.replace("—", "-").replace("–", "-")

        # check for exact match or substring match again
        if fetched_name == db_name or fetched_name in db_name or db_name in fetched_name:
            return True
        
        # if no match found, return false
        return False
    

    @typechecked
    def add_data_complicated_universities(self, db_unis: list[dict[str, str]], fetched_unis: dict[str, dict[str, str]]) -> Response:
        """
        Submethod of add_data_universities to handle complicated cases.
        This method is called after the main method add_data_universities.
        Since this method takes longer than the simple compare compare algorithm, only call this for the complicated cases.

        Returns:
            Response: Response object indicating success or failure of the operation.
        """

        # do not stop comparing after match was found since better match could be found

        # create a possible combinations without duplicates
        combinations = {(db_uni, fetched_uni) for db_uni in db_unis for fetched_uni in fetched_unis.keys()}

        # initialize matches
        matches = [] # create list since no duplicates can exist

        for i in combinations:
            if self._compare_university_names(fetched_name=i[1], db_name=i[0]["name"]):
                matches.append(i)
        
        # matches should only contain 1:1 relations but due to counting unclean matches as matches, this relation condition might me broken
        # therefore allow 1:n relations so each db_uni can only appear once but fetched_uni can appear multiple times (since e.g. a university has multiple locations can exist, that has only one entry in fetched_unis, since multiple citys are being combined)
        
        # new dict that contains db_unis grouped by name
        grouped_db_unis = {}
        
        for uni in matches:
            if uni[0]["name"] not in grouped_db_unis:
                grouped_db_unis[uni[0]["name"]] = [uni]
                continue
            grouped_db_unis[uni[0]["name"]].append(uni)
        
        # iterate over all db_unis that have multiple fetched uni matches
        for uni in [{key: value for key, value in grouped_db_unis.items() if len(value) > 1}]:
            success_fetched = [{key: value} for key, value in uni.items() for val in value if val[1]["city"] in val[0]["city"].split(", ")] # check whether the city of the fetched uni matches one of the cities for the db_uni
            # if none matches, take none
            
    
    @db.cursor_handling(manually_supply_cursor=False)
    @typechecked
    def add_data_universities(self, cursor: psycopg2.extensions.cursor | None = None) -> Response:
        """
        Implements abstract method from parent class Scraper.

        Scrape information of universities and store them in the database.

        Parameters:
            cursor (psycopg2.extensions.cursor | None): SUPPLIED BY DECORATOR; Database cursor for storing data.

        Returns:
            Response: Response object indicating success or failure of the operation.
        """

        # get universities from db
        result = db.select(cursor=cursor, # type: ignore
                           table="all_unis.universities", 
                           answer_type=db.ANSWER_TYPE.LIST_ANSWER, 
                           keywords=["id", "name", "city"], 
                           specific_where="source = 'daad.de' AND website IS NULL")
        
        # handle database error
        if result.is_error:
            return Response(message=Message(
                name="DatabaseError",
                type="Error",
                category="database",
                info="Failed to fetch universities from database.",
                details={"exception": result.error, "stack_trace": result.stack_trace},
                code=None
            ))
        
        universities = result.data
        
        # fetch universities from the Hochschulkompass
        fetched_unis = self._fetch_universities()
        
        # restructure and extract important data
        fetched_unis = {uni["name"] : {
            "website": uni["website"],
            "hs_nr": uni["hs_nr"], 
            "city": uni["city"]
        } for uni in fetched_unis}
        
        # extract universities
        universities = result.data

        # initialize dict for updated universities
        updated_unis = {}

        # combine db data and fetched data
        for uni in universities:
            # if no city matched, just match university name (for uni that has locations in multiple cities)
            if uni["name"] in fetched_unis and fetched_unis[uni["name"]]["city"] in uni["city"].split(", "): # very unclean but it works
                updated_unis[uni["id"]] = {
                    "website": fetched_unis[uni["name"]]["website"],
                    "hs_nr": fetched_unis[uni["name"]]["hs_nr"], 
                    "city_check_successful": True
                }
            elif uni["name"] in fetched_unis:
                updated_unis[uni["id"]] = {
                    "website": fetched_unis[uni["name"]]["website"],
                    "hs_nr": fetched_unis[uni["name"]]["hs_nr"], 
                    "city_check_successful": False
                }
        
        # remove duplicates where city check was unsuccessful
        clean_updated_unis = {}
        for key, value in updated_unis.items():
            if key not in clean_updated_unis:
                clean_updated_unis[key] = value
            else:
                if value["city_check_successful"] is True:
                    clean_updated_unis[key] = value
        updated_unis = clean_updated_unis

        # update universities in the database
        # initialize query
        query = f"""
            UPDATE all_unis.universities
            SET website = data.website,
                hs_nr = data.hs_nr
            FROM (VALUES
                {', '.join(['(%s, %s, %s)' for _ in range(len(updated_unis))])}
            ) AS data(id, website, hs_nr)
            WHERE all_unis.universities.id = data.id;
        """

        # set variables
        variables = [
            [
                uni_id,
                updated_unis[uni_id]["website"],
                int(updated_unis[uni_id]["hs_nr"])
            ] for uni_id in updated_unis
        ]
        variables = [e for i in variables for e in i]

        # if no universities to update, return success response
        if len(variables) == 0:
            return Response(success_list=[])
        
        # execute update query
        result = db.custom_call(
            cursor=cursor, # type: ignore
            query=query, 
            variables=variables,
            type_of_answer=db.ANSWER_TYPE.NO_ANSWER
        )

        # handle database error
        if result.is_error:
            return Response(message=Message(
                name="DatabaseError",
                type="Error",
                category="database",
                info="Failed to update universities in database.",
                details={"exception": result.error, "stack_trace": result.stack_trace},
                code=None
            ))

        # get universities from db again, but with updated values
        result = db.select(cursor=cursor, # type: ignore
                           table="all_unis.universities", 
                           answer_type=db.ANSWER_TYPE.LIST_ANSWER, 
                           keywords=["id", "name", "city"], 
                           specific_where="source = 'daad.de' AND website IS NULL")
        
        # handle database error
        if result.is_error:
            return Response(message=Message(
                name="DatabaseError",
                type="Error",
                category="database",
                info="Failed to fetch universities from database.",
                details={"exception": result.error, "stack_trace": result.stack_trace},
                code=None
            ))
        
        universities = result.data
        
        # handle complicated cases, that do not match 1:1
        self.add_data_complicated_universities(db_unis=universities, fetched_unis=fetched_unis)
        
        # return success response
        return Response(success_list=list(updated_unis.keys()))
            
            
    def _fetch_university_info(self) -> list[dict[str, str]]:
        """
        Fetches the list of universities from the Hochschulkompass TXT download endpoint.

        Returns:
            list[dict[str, str]]: A list of dictionaries containing data for each university in Germany.
        """

        # initialize URL for the Hochschulkompass TXT download
        url = "https://hs-kompass.de/kompass/xml/download/hs_liste.txt"

        # make the GET request to fetch the data
        response = requests.get(url)
        response.raise_for_status()

        # extract the data
        data = response.text
        
        # clean the data
        data = data.split("\n")
        header = data[0].split("\t")
        universities = [line.split("\t") for line in data[1:] if line]

        clean_data = [{h: u for h, u in zip(header, uni)} for uni in universities]

        return clean_data
        


if __name__ == "__main__":
    new_only = False
    scraper = Daad(new_only=new_only)
    # response = scraper.main(async_fetch=False, delay=0, rate_limit_delay=3, printing=True, raspi=False) # type: ignore
    response = scraper.add_data_universities()
    print(json.dumps(response.to_json(), indent=4))