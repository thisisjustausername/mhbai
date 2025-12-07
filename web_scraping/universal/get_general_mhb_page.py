# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: get the general mhb page for each university
# STATUS: IN DEVELOPMENT
# FileID: Sc-ge-0005

import math
import multiprocessing
from multiprocessing import pool
import time
import psycopg2
import requests
from bs4 import BeautifulSoup
from database import database as db


def get_general_mhb_page(university: str, city: str) -> str | None:
    """
    Get the general mhb page for each university.

    Parameters:
        university (str): Name of the university.
        city (str): City of the university.

    Returns:
        str | None: URL of the general mhb page or None if not found.
    """
    try:
        session = requests.Session()
        # base_url = "https://www.google.com/search"
        base_url = "https://leta.mullvad.net/search?q="
        query = f"modulhandbuch+{university}+{city}"
        url = f"{base_url}{query}&engine=google&language=de"

        response = session.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        link = soup.find("div", class_="results svelte-fmlk7p").find("div").find("article").find("a").get("href")
    except:
        raise Exception("No link found")
    if link is None:
        raise Exception("No link found")
    return link

@db.cursor_handling(manually_supply_cursor=False)
def bundled_mhb_page(data: list[dict]):
    session = requests.Session()
    
    # base_url = "https://www.google.com/search"
    base_url = "https://leta.mullvad.net/search?q="
    for uni in data:
        university, city = uni["university"], uni["city"]
        query = f"modulhandbuch+{university}+{city}"
        url = f"{base_url}{query}&engine=google&language=de"

        try:
            response = session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            link = soup.find("div", class_="results svelte-fmlk7p").find("div").find("article").find("a").get("href") # type: ignore
        except:
            continue
        if link is None:
            continue
        result = db.update(cursor=cursor, table="all_unis.universities", arguments={"mhb_url": link}, conditions={"name": university, "city": city}) # type: ignore
        if result.is_error:
            print(f"Error updating university {university}, {city}: {link}")
    return None

@db.cursor_handling(manually_supply_cursor=False)
def get_uni_mhb_url(abort: bool = False, cursor: psycopg2.extensions.cursor | None = None) -> None:
    """
    get all universities from db

    Parameters:
        abort (bool): whether to abort on first failure
        cursor (psycopg2.extensions.cursor | None): SUPPLIED BY DECORATOR; Database cursor for storing data.
    Returns:
        None
    """
        
    # set cursor again in order to only set linter warning ignore setting once
    cursor = cursor # type: ignore
    
    # get data
    result = db.select(cursor=cursor, table="all_unis.universities", keywords=["name", "city"], answer_type=db.ANSWER_TYPE.LIST_ANSWER, specific_where="mhb_url IS NULL") # type: ignore
    if result.is_error:
        raise result.error
    data = result.data
    data = [{key if key != "name" else "university": value for key, value in uni.items()} for uni in data]
    for uni in data:
        time.sleep(3)
        try:
            link = get_general_mhb_page(**uni)
        except Exception:
            if abort:
                raise Exception("BLOCKED")
            print(f"No link found for {uni['university']}, {uni['city']}")
            continue
        result = db.update(cursor=cursor, table="all_unis.universities", arguments={"mhb_url": link}, conditions={"name": uni["university"], "city": uni["city"]}) # type: ignore
        if result.is_error:
            print(result.error)
            print(f"Error updating university {uni['university']}, {uni['city']}: {link}")
        else:
            print(f"Updated university {uni['university']}, {uni['city']}: {link}")


# NOTE: do not use cursor decorator, since this function closes the cursor very early while running for a long duration
def get_data_asynchronous(urls_per_job: int = 2):
    # initialize multiprocessing
    multiprocessing.set_start_method("spawn")

    # connect to db
    cursor = db.connect()
    
    # get data
    result = db.select(cursor=cursor, table="all_unis.universities", keywords=["name", "city"], answer_type=db.ANSWER_TYPE.LIST_ANSWER)

    # close cursor
    db.close(cursor)

    # handle error
    if result.is_error:
        raise result.error
    
    data = result.data
    data = [{key if key != "name" else "university": value for key, value in uni.items()} for uni in data]
    # assign processes
    processes = math.ceil(len(data) / urls_per_job)

    # start pool
    with multiprocessing.Pool(processes=processes) as pool:
        # distribute jobs and collect results
        results = [pool.apply_async(bundled_mhb_page, args=(data[i:i + urls_per_job],)) for i in range(0, len(data), urls_per_job)]
        for result in results:
            print(result.get())


def automate():
    get_uni_mhb_url(abort=True)
if __name__ == "__main__":
    # Example usage
    # get_data_asynchronous()
    get_uni_mhb_url()