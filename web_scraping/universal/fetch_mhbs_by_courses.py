# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: get the url to the mhb pdf for each course of study
# Status: PROTOTYPING
# FileID: Sc-ge-0006

from datetime import datetime, timedelta
import time

import psycopg2
import requests
from bs4 import BeautifulSoup
from database import database as db

@db.cursor_handling(manually_supply_cursor=False)
def fetch_search_strings(search_strings: list[dict[str, str]], cursor: psycopg2.extensions.cursor | None = None) -> None | Exception:
    """
    fetches mhb urls for given search strings and updates the database
    
    Parameters:
        search_strings (list[dict[str, str]]): list of search strings to fetch mh
        cursor (psycopg2.extensions.cursor | None): SUPPLIED BY DECORATOR; Database cursor for storing data.
    Returns:
        None | Exception: None if successful, Exception if an error occurred
    """

    session = requests.Session()
    
    # url for the duckduckgo instant answer api
    # base_url: str = "https://api.duckduckgo.com/"
    base_url = "https://search.brave.com/search"
    for search_string in search_strings:
        try:
            response = session.get(base_url, params={"q": search_string, "lang": "de"}) # , "format": "json"
            response.raise_for_status()
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
        result = db.update(cursor=cursor, table="all_unis.prototyping_mhbs", arguments={"mhb_url": mhb_url}, conditions={"search_string": search_string}) # type: ignore
        if result.is_error:
            print(f"Error updating search_string {search_string}: {mhb_url}")
            continue
        print(f"Updated search_string {search_string}: {mhb_url}")
        time.sleep(5)
    return None


@db.cursor_handling(manually_supply_cursor=False)
def main(cursor: psycopg2.extensions.cursor | None = None) -> None:
    """
    main function to fetch mhb urls for all universities without mhb url in the database
    
    Parameters:
        cursor (psycopg2.extensions.cursor | None): SUPPLIED BY DECORATOR; Database cursor for storing data.
    Returns:
        None
    """

    # fetch all universities
    result = db.select(cursor=cursor, table="all_unis.prototyping_mhbs", keywords=["search_string"], specific_where="mhb_url IS NULL") # type: ignore
    # handle possible error
    if result.is_error:
        raise result.error

    # get data
    search_strings = result.data
    search_strings = [i["search_string"] for i in search_strings if i["search_string"] is not None]

    fetch_search_strings(search_strings)

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
