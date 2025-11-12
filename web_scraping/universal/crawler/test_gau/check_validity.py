# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: verify, whether urls from crawling are still valid
# STATUS: PROTOTYPING
# FileID: Sc-cr-0004

import math
import requests
import multiprocessing

def check_urls(urls: list, offset: int=0):
    """
    Check, whether urls are still valid.

    Parameters:
        urls (list): List of URLs to be processed.
        offset (int): Where to start counting in order to show a readable output to the user
    """
    valid_urls = []
    for url in urls:
        try:
            response = requests.head(url, allow_redirects=True)
            if response.status_code != 404:
                valid_urls.append(url)
                print(url)
        except requests.RequestException as e:
            print(f"Error checking {url}: {e}")
    return valid_urls

def get_base_links(urls_per_job: int = 30):
    """
    get the links from test.txt
    
    Parameters:
        urls_per_job (int): Number of URLs to be processed per job in the multiprocessing pool.
    """

    # initialize multiprocessing
    multiprocessing.set_start_method("spawn")

    with open("web_scraping/universal/test_gau/test.txt", "r") as file:
        data = file.read()

    data = data.split("\n")
    list_urls = [i for i in data if 'mhb' in i.lower() or 'modulhandb' in i.lower()]
    list_urls = [i for i in list_urls if 'pdf' in i]
    print(len(list_urls))
    print(list_urls)
    
    # assign processes
    processes = math.ceil(len(list_urls) / urls_per_job)

    # start pool
    with multiprocessing.Pool(processes=processes) as pool:

        # initialize variables
        all_elements = []

        # distribute jobs and collect results
        results = [pool.apply_async(check_urls, args=(list_urls[i:i + urls_per_job],i)) for i in range(0, len(list_urls), urls_per_job)]
        # gather results
        for result in results:
            elements = result.get()
            all_elements += elements
        print(all_elements)

if __name__ == "__main__":
    get_base_links(urls_per_job=5)
