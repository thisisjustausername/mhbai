from datetime import datetime, timedelta
import time

import requests
from bs4 import BeautifulSoup
from web_scraping.universal.data import database as db


def fetch_search_strings(search_strings: list[dict[str, str]]) -> None | Exception:

    session = requests.Session()

    # get cursor
    cursor = db.connect()
    
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
        mhb_url = soup.find("div", {"id": "results"}).find("div").find("a").get("href")
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


def main():

    # get cursor
    cursor = db.connect()

    # fetch all universities
    result = db.select(cursor=cursor, table="universal_mhbs", keywords=["search_string"])
    db.close(cursor)
    # handle possible error
    if result.is_error:
        raise result.error

    # get data
    search_strings = result.data
    search_strings = [i["search_string"] for i in search_strings if i["search_string"] is not None]

    fetch_search_strings(search_strings)

if __name__ == "__main__":
    retry = True
    minutes = 5

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