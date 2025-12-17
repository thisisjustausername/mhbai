# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: get url of uni page for each university
# Status: VERSION 1.0
# FileID: Sc-ge-0002

import time

from bs4 import BeautifulSoup
import psycopg2
import requests
from database import database as db

@db.cursor_handling(manually_supply_cursor=False)
def bundled_universities(universities: list[dict[str, str]], cursor: psycopg2.extensions.cursor | None = None) -> None | Exception:
    """
    fetches uni urls for given universities and updates the database
    
    Args:
        universities (list[dict[str, str]]): list of universities to fetch uni urls for
        cursor (psycopg2.extensions.cursor | None): SUPPLIED BY DECORATOR; Database cursor for storing data.
    Returns:
        None | Exception: None if successful, Exception if an error occurred
    """

    session = requests.Session()
    
    # url for the duckduckgo instant answer api
    # base_url: str = "https://api.duckduckgo.com/"
    base_url = "https://leta.mullvad.net/search?"
    for university in universities:
        query = university["university"]
        if university["city"] not in query:
            query += f" {university['city']}"
        try:
            response = session.get(base_url, params={"q": query, "engine": "google", "language": "de"}) # , "format": "json"
            response.raise_for_status()
        except Exception as e:
            if response.status_code == 429:
                raise Exception("Rate limit exceeded. Stopping the scraper.")
            print(f"Error for query {query}: {response.status_code}")
            continue
        soup = BeautifulSoup(response.text, 'lxml')
        uni_url = soup.find("div", class_="results svelte-fmlk7p").find("div").find("article").find("a").get("href")
        # uni_url = response.json().get("OfficialDomain", None)
        if uni_url is None:
            print(f"Error for query {query}: No OfficialDomain found")
            continue
        if uni_url.startswith("https://www."):
            uni_url = uni_url.split("https://www.", 1)[1]
        if uni_url.startswith("http://"):
            uni_url = uni_url.split("http://", 1)[1]
        """
        if uni_url.endswith("/"):
            uni_url = uni_url[:-1]
        """
        if "/" in uni_url:
            uni_url = uni_url.split("/", 1)[0]
        result = db.update(cursor=cursor, table="all_unis.prototyping_mhbs", arguments={"uni_url": uni_url}, conditions={"university": university["university"], "city": university["city"]}) # type: ignore
        if result.is_error:
            print(f"Error updating university {university['university']}, {university['city']}: {uni_url}")
            continue
        print(f"Updated university {university['university']}, {university['city']}: {uni_url}")
        time.sleep(5)
    return None


# NOTE: do not use cursor decorator, since this function closes the cursor very early while running for a long duration
def main():
    
    # set urls per job
    urls_per_job: int = 10

    # connect to db
    cursor = db.connect()
    
    # fetch all universities
    result = db.select(cursor=cursor, table="all_unis.prototyping_mhbs", keywords=["university", "city"], specific_where="uni_url IS NULL")
    db.close(cursor)

    # handle possible error
    if result.is_error:
        raise result.error

    # get data
    universities = result.data
    data = []
    for i in universities:
        if i not in data:
            data.append({"university": i["university"], "city": i["city"]})
    universities = data

    """
    # initialize multiprocessing
    multiprocessing.set_start_method("spawn")
    # assign processes
    processes = math.ceil(len(universities) / urls_per_job)
    with multiprocessing.Pool(processes=processes) as pool:
        # distribute jobs and collect results
        results = [pool.apply_async(bundled_universities, args=(universities[i:i + urls_per_job],)) for i in range(0, len(universities), urls_per_job)]
        for result in results:
            result.get()
    """
    bundled_universities(universities)

if __name__ == "__main__":
    main()