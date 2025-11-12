# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: download mhbs from University of Augsburg
# Status: FUNCTIONAL-TEMPORARY
# FileID: Sc-au-0001

import requests
import json
from bs4 import BeautifulSoup
import time

def check_url(url: str) -> bool:
    """
    checks, whether the url is safe to use
    """

    if url.startswith("https://mhb.uni-augsburg.de/") and url.endswith(".pdf") and not "redirect" in url and len(url) <= 500:
        return True
    return False

def fetch_valid_urls(url_list=["https://mhb.uni-augsburg.de/"], final_links=[]):
    """
    searches for all mhb links and saves them as valid urls
    """

    # start_url = "https://mhb.uni-augsburg.de/"
    new_urls = []
    for link in url_list:
        result = requests.get(link)
        if result.status_code != 200:
            raise Exception("Error fetching mhb links")

        soup = BeautifulSoup(result.text, 'lxml')

        link_container = soup.find("div", class_="section-inner mt-0 mb-0")

        # next line is optional
        link_container = link_container.find("div", class_="textEditorContent")

        list_items = link_container.find_all('li')
        links = [i.find('a')['href'] for i in list_items]
        links = [link + i for i in links]

        # iterate from the end in order to not change the next indices when popping an element from the list
        for curr_link in links:
            if curr_link.endswith(".pdf"):
                final_links.append(curr_link)
            else:
                new_urls.append(curr_link)
    if len(new_urls) == 0:
        return final_links
    return fetch_valid_urls(new_urls, final_links)

def download_all_pdfs():
    """
    downloads all mhb pdfs
    """
    with open("uni_a_all_mhbs.json", "r") as file:
        data = json.load(file)
    for index, i in enumerate(data):
        pdf = requests.get(i)
        with open(f"pdfs/{pdf.headers.get('Content-Disposition').split("filename=",1)[1]}", "wb") as file:
            file.write(pdf.content)
        print(index)

def download_new_pdfs(new_links: list):
    """
    downloads only new mhb pdfs

    Parameters:
        new_links (list): list of new mhb links
    """
    for index, i in enumerate(new_links):
        pdf = requests.get(i)
        with open(f"pdfs/{pdf.headers.get('Content-Disposition').split('filename=',1)[1]}", "wb") as file:
            file.write(pdf.content)
        print(index)

if __name__ == "__main__":
    def do_everything():
        """
        combines everything by extracting all mhb links and then downloading all mhbs
        """
        data = fetch_valid_urls()
        # print(f"It took approximately {time.time() - start} seconds to fetch all mhbs of the Uni Augsburg.")
        with open("uni_a_all_mhbs.json", "w") as file:
            json.dump(data, file, indent=4)

        download_all_pdfs()
    
    def add_new_pdfs():
        """
        fetches all mhb links and downloads only the new ones
        """
        data = fetch_valid_urls()
        with open("uni_a_all_mhbs.json", "r") as file:
            old_data = json.load(file)

        with open("uni_a_all_mhbs.json", "w") as file:
            json.dump(data, file, indent=4)
        
        new_links = [i for i in data if i not in old_data]

        download_new_pdfs(new_links)

    
    # use this to download all mhb pdfs for university of augsburg timed with the pdf urls already fetched
    """start = time.time()
    download_all_pdfs()
    end = time.time()
    print(end - start)"""

    # use this to fetch and download all mhb pdfs for university of augsburg
    # do_everything()

    # use this to only download new mhb pdfs for university of augsburg
    add_new_pdfs()